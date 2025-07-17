import json
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageChops
import shutil, io
import base64

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent

def clean_pycache():
    pycache_dir = PROJECT_ROOT_PATH / "visual_tests" / "__pycache__"
    if pycache_dir.exists():
        print(f"Cleaning up: {pycache_dir}")
        shutil.rmtree(pycache_dir, ignore_errors=True)

def run_git_command(args, cwd):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {' '.join(args)}\n{e.stderr.strip()}")

def sync_branch(branch, repo_path=PROJECT_ROOT_PATH, project_root_path=None):
    """
    Syncs a Git branch by checking it out and pulling the latest changes.

    Args:
        branch (str): Name of the branch to sync (e.g., "visual-baselines")
        repo_path (str or Path): Path to the local Git repo
        project_root_path (str or Path, optional): Used for logging/debugging
    """
    location = project_root_path or repo_path
    print(f"Syncing '{branch}' branch at {location}")
    clean_pycache()
    run_git_command(["checkout", branch], cwd=repo_path)
    run_git_command(["pull", "origin", branch], cwd=repo_path)
    run_git_command(["checkout", "main"], cwd=repo_path)

    print(f"[✓] Synced at {time.strftime('%Y-%m-%d %H:%M:%S')}")

SCRIPT_PATH = Path(__file__).resolve().parent
BASELINE_PATH = SCRIPT_PATH / "baseline"
PROJECT_ROOT = SCRIPT_PATH.parent
CACHE_FILE = BASELINE_PATH / "last_commit_cache.json"

def load_last_processed():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f).get("last_processed")
    else:
        # Ensure baselines dir exists
        BASELINE_PATH.mkdir(parents=True, exist_ok=True)

        # Create empty cache file
        with open(CACHE_FILE, "w") as f:
            json.dump({"last_processed": None}, f, indent=2)

        return None

def update_last_processed(commit_hash):
    with open(CACHE_FILE, "w") as f:
        json.dump({"last_processed": commit_hash}, f, indent=2)

def get_valid_commit_with_baseline(page_name, skip_commits):
    for commit in get_git_commits():
        if commit in skip_commits:
            continue
        commit_dir = BASELINE_PATH / commit
        if (commit_dir / f"{page_name}.png").exists() and (commit_dir / f"{page_name}_dom.json").exists():
            return commit
    return None

def get_git_commits(max_count=10):
    try:
        result = subprocess.run(
            ["git", "rev-list", "main", f"--max-count={max_count}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"[✗] Failed to get commit list: {e.stderr.strip()}")
        return []

def get_current_pair_in_memory(page_name="test_home_page"):
    print(f"[•] Scanning baselines in: {BASELINE_PATH}")

    baseline_commits = [d.name for d in BASELINE_PATH.iterdir() if d.is_dir()]
    if not baseline_commits:
        print("[!] No baselines available. Exiting comparison safely.")
        return None

    # Get commits in correct git order (most recent last)
    git_commits = get_git_commits(max_count=50)  # adjust as needed
    ordered_baselines = [c for c in git_commits if c in baseline_commits]

    def is_valid(commit):
        return (BASELINE_PATH / commit / f"{page_name}.png").exists() and \
               (BASELINE_PATH / commit / f"{page_name}_dom.json").exists()

    last_processed = load_last_processed()
    if last_processed and last_processed not in ordered_baselines:
        print(f"[!] Cached last commit {last_processed} not found in valid baselines.")
        update_last_processed(None)
        last_processed = None

    # If first time running
    if not last_processed:
        for commit in ordered_baselines:
            if is_valid(commit):
                update_last_processed(commit)
                return {
                    "first_time": True,
                    "curr_commit": commit,
                    "curr": {
                        "image": Image.open(BASELINE_PATH / commit / f"{page_name}.png").convert("RGB"),
                        "dom": json.load(open(BASELINE_PATH / commit / f"{page_name}_dom.json", encoding="utf-8"))
                    }
                }
        return None

    # Else, find next commit after last_processed
    try:
        prev_index = ordered_baselines.index(last_processed)
    except ValueError:
        print(f"[!] Could not find cached commit {last_processed} in ordered baselines.")
        return None

    for next_commit in ordered_baselines[prev_index + 1:]:
        if is_valid(next_commit):
            return {
                "first_time": False,
                "prev_commit": last_processed,
                "curr_commit": next_commit,
                "prev": {
                    "image": Image.open(BASELINE_PATH / last_processed / f"{page_name}.png").convert("RGB"),
                    "dom": json.load(open(BASELINE_PATH / last_processed / f"{page_name}_dom.json", encoding="utf-8"))
                },
                "curr": {
                    "image": Image.open(BASELINE_PATH / next_commit / f"{page_name}.png").convert("RGB"),
                    "dom": json.load(open(BASELINE_PATH / next_commit / f"{page_name}_dom.json", encoding="utf-8"))
                }
            }

    print("[✓] No newer valid commit found for comparison.")
    return None

def mark_issues(curr_pair, prev_pair, lpips_model, clip_model,
                lpips_thresh=0.03, clip_thresh=0.98, min_size=20):
    from PIL import ImageDraw
    import pandas as pd

    def is_bbox_contained(bigger, smaller):
        x1_b, y1_b, x2_b, y2_b = bigger
        x1_s, y1_s, x2_s, y2_s = smaller
        return x1_b <= x1_s and y1_b <= y1_s and x2_b >= x2_s and y2_b >= y2_s

    prev_img = prev_pair["image"].copy()
    curr_img = curr_pair["image"].copy()
    prev_draw = ImageDraw.Draw(prev_img)
    curr_draw = ImageDraw.Draw(curr_img)

    prev_dom = prev_pair["dom"]
    curr_dom = curr_pair["dom"]

    results = []
    segments = []

    for el_prev, el_curr in zip(prev_dom, curr_dom):
        if el_prev.get("tag") != el_curr.get("tag"):
            continue

        try:
            x = int(el_prev["x"])
            y = int(el_prev["y"])
            w = int(el_prev["width"])
            h = int(el_prev["height"])
            if w < min_size or h < min_size:
                continue

            crop_prev = prev_img.crop((x, y, x + w, y + h))
            crop_curr = curr_img.crop((x, y, x + w, y + h))

            lp_score = lpips_model.compute_distance(crop_prev, crop_curr)
            clip_score = clip_model.compute_similarity(crop_prev, crop_curr)

            is_changed = (lp_score > lpips_thresh) or (clip_score < clip_thresh)

            results.append({
                "tag": el_prev["tag"],
                "text": el_prev.get("text", ""),
                "bbox": (x, y, x + w, y + h),
                "LPIPS": round(lp_score, 4),
                "CLIP": round(clip_score, 4),
                "LPIPS_Detects_Change": int(lp_score > lpips_thresh),
                "CLIP_Detects_Change": int(clip_score < clip_thresh),
                "Change_Flag": int(is_changed)
            })

            segments.append({
                "tag": el_prev["tag"],
                "bbox": (x, y, x + w, y + h),
                "prev_crop": crop_prev,
                "curr_crop": crop_curr
            })

        except Exception as e:
            print(f"[!] Skipped region due to error: {e}")
            continue

    df_scores = pd.DataFrame(results)

    # --- containment filter (keep leaves) ---
        # --- Deduplicate parent containers if child is already flagged ---
    changed = [r for r in results if r["Change_Flag"] == 1]

    # Sort by area (smallest first)
    changed_sorted = sorted(changed, key=lambda r: (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1]))

    suppressed = set()
    for i, inner in enumerate(changed_sorted):
        xi1, yi1, xi2, yi2 = inner["bbox"]
        for j, outer in enumerate(changed_sorted[i+1:], start=i+1):
            xo1, yo1, xo2, yo2 = outer["bbox"]

            # Check if inner is fully inside outer
            if xo1 <= xi1 and yo1 <= yi1 and xo2 >= xi2 and yo2 >= yi2:
                suppressed.add(j)

    for idx in suppressed:
        results_idx = results.index(changed_sorted[idx])
        results[results_idx]["Change_Flag"] = 0
        results[results_idx]["LPIPS_Detects_Change"] = 0
        results[results_idx]["CLIP_Detects_Change"] = 0


    # Draw only filtered changes
    for i, row in df_scores[df_scores["Change_Flag"] == 1].iterrows():
        x1, y1, x2, y2 = row["bbox"]
        prev_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        curr_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

    summary = {
        "total_regions": len(df_scores),
        "changed_regions": int(df_scores["Change_Flag"].sum()) if not df_scores.empty else 0,
        "change_percent": round(df_scores["Change_Flag"].mean() * 100, 2) if not df_scores.empty else 0.0
    }

    print(f"[✓] Compared {len(df_scores)} DOM regions. Changes: {summary['changed_regions']}")

    return {
        "highlighted_prev": prev_img,
        "highlighted_curr": curr_img,
        "scores": df_scores,
        "segments": segments,
        "summary": summary
    }

def pixel_diff():
    pairs = get_current_pair_in_memory()
    if not pairs:
        print("[✗] Could not fetch image pair.")
        return

    image_a = pairs["prev"]["image"]
    image_b = pairs["curr"]["image"]

    # Ensure both images are the same size
    if image_a.size != image_b.size:
        print("[!] Image sizes do not match.")
        return

    diff = ImageChops.difference(image_a, image_b)
    diff.show()  
    # diff.save("pixel_diff_result.png")
    # print("[✓] Pixel diff generated and saved.")

def encode_image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"