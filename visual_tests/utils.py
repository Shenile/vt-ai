import os
import json
import time
import subprocess
from playwright.sync_api import sync_playwright, TimeoutError
from pathlib import Path
from PIL import Image
import io
import shutil

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent
import shutil

def clean_pycache():
    pycache_dir = PROJECT_ROOT_PATH / "visual_tests" / "__pycache__"
    if pycache_dir.exists():
        print(f"Cleaning up: {pycache_dir}")
        shutil.rmtree(pycache_dir, ignore_errors=True)

def capture_screenshot_and_dom(url, file_name, file_path):
    print(f"Ensuring directory exists: {file_path}")
    os.makedirs(file_path, exist_ok=True)

    try:
        with sync_playwright() as p:
            print("Launching Chromium browser in headless mode...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1,
                is_mobile=False
            )
            page = context.new_page()
            print(f"Navigating to URL: {url}")
            page.goto(url, wait_until="networkidle", timeout=15000)

            page.add_style_tag(content="""
                * {
                    animation: none !important;
                    transition: none !important;
                }
            """)

            print("Waiting for fonts to be ready...")
            page.evaluate("() => new Promise(resolve => document.fonts.ready.then(resolve))")

            # Screenshot
            output_path = os.path.join(file_path, f"{file_name}.png")
            print(f"Saving screenshot to: {output_path}")
            page.screenshot(path=output_path, full_page=True)

            # DOM snapshot with structured tree
            print("Extracting enhanced DOM snapshot with IDs and children...")
            dom_snapshot = page.evaluate("""() => {
                function getNodeData(node) {
                    const rect = node.getBoundingClientRect();
                    if (!node.dataset.vtId) {
                        node.dataset.vtId = 'node-' + Math.random().toString(36).substr(2, 9);
                    }
                    return {
                        id: node.dataset.vtId,
                        tag: node.tagName.toLowerCase(),
                        bbox: [rect.left, rect.top, rect.right, rect.bottom],
                        children: Array.from(node.children)
                            .filter(child => {
                                const r = child.getBoundingClientRect();
                                return r.width > 0 && r.height > 0;
                            })
                            .map(child => {
                                if (!child.dataset.vtId) {
                                    child.dataset.vtId = 'node-' + Math.random().toString(36).substr(2, 9);
                                }
                                return child.dataset.vtId;
                            })
                    };
                }

                function traverse(node, collected = []) {
                    if (!(node instanceof Element)) return collected;
                    const style = window.getComputedStyle(node);
                    if (style.display === 'none' || node.offsetWidth === 0 || node.offsetHeight === 0) return collected;

                    const data = getNodeData(node);
                    collected.push(data);
                    Array.from(node.children).forEach(child => traverse(child, collected));
                    return collected;
                }

                return traverse(document.body);
            }""")


            dom_path = os.path.join(file_path, f"{file_name}_dom.json")
            with open(dom_path, 'w') as f:
                json.dump(dom_snapshot, f, indent=2)

            print(f"DOM snapshot saved to: {dom_path}")
            print("✓ Screenshot + DOM capture completed.")

    except TimeoutError:
        print("TimeoutError: Page load timed out.")
    except Exception as e:
        print(f"Exception during capture: {e}")

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

def get_current_pair_in_memory(branch="visual-baselines", page_name="homepage"):
    """
    Reads PNG and DOM JSON from the last 2 commits in visual-baselines *without checking out the branch*.
    Uses `git show` to read content directly from the branch tree.

    Returns:
        {
            "prev": {"image": PIL.Image, "dom": list},
            "curr": {"image": PIL.Image, "dom": list}
        }
    """
    print(f"[•] Reading last 2 commits from '{branch}'...")

    try:
        # Get last 2 commit hashes from visual-baselines
        result = subprocess.run(
            ["git", "rev-list", branch, "--max-count=10", "main"],
            cwd=PROJECT_ROOT_PATH,
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print("[✗] Failed to get commit list:", e.stderr.strip())
        return None
    
    print(commits)

    # Check which of these commits actually contain the baseline files
    def commit_has_required_files(commit_hash):
        for ext in [".png", "_dom.json"]:
            path_in_git = f"visual-baselines:baselines/{commit_hash}/{page_name}{ext}"
            print(path_in_git)
            try:
                res = subprocess.run(
                    ["git", "show", path_in_git],
                    cwd=PROJECT_ROOT_PATH,
                    capture_output=True,
                    check=True
                )
                print(res)
            except subprocess.CalledProcessError:
                return False
        return True

    valid_commits = [c for c in commits if commit_has_required_files(c)]
    print(valid_commits)
    if len(valid_commits) < 2:
        print("[!] Not enough valid commits with baseline files in visual-baselines.")
        return None

    curr, prev = valid_commits[0], valid_commits[1]
    print(f"[✓] Using commits:\n    Previous: {prev}\n    Current : {curr}")

    def load_image_from_git(commit, filename):
        path = f"visual-baselines:baselines/{commit}/{filename}"
        try:
            result = subprocess.run(
                ["git", "show", path],
                cwd=PROJECT_ROOT_PATH,
                capture_output=True,
                check=True
            )
            return Image.open(io.BytesIO(result.stdout)).convert("RGB")
        except subprocess.CalledProcessError as e:
            print(f"[✗] Could not read image from {path}:", e.stderr.strip())
            return None

    def load_json_from_git(commit, filename):
        path = f"visual-baselines:baselines/{commit}/{filename}"
        try:
            result = subprocess.run(
                ["git", "show", path],
                cwd=PROJECT_ROOT_PATH,
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"[✗] Could not read JSON from {path}:", e.stderr.strip())
            return None

    return {
        "prev": {
            "image": load_image_from_git(prev, f"{page_name}.png"),
            "dom": load_json_from_git(prev, f"{page_name}_dom.json")
        },
        "curr": {
            "image": load_image_from_git(curr, f"{page_name}.png"),
            "dom": load_json_from_git(curr, f"{page_name}_dom.json")
        }
    }

def mark_issues(curr_pair, prev_pair, lpips_model, clip_model,
                lpips_thresh=0.03, clip_thresh=0.98, min_size=20):
    """
    Detects and highlights changed UI regions and returns full prediction metadata.

    Args:
        curr_pair, prev_pair: dicts with keys {"image": PIL.Image, "dom": list}
        lpips_model, clip_model: objects with `compute_distance()` and `compute_similarity()` methods
        lpips_thresh, clip_thresh: thresholds for flagging a change
        min_size: minimum region size to evaluate

    Returns:
        {
            "highlighted_prev": <PIL.Image>,
            "highlighted_curr": <PIL.Image>,
            "scores": pd.DataFrame of LPIPS/CLIP per region,
            "segments": list of dicts per region
        }
    """
    from PIL import ImageDraw
    import pandas as pd

    prev_img = prev_pair["image"].copy()
    curr_img = curr_pair["image"].copy()
    prev_draw = ImageDraw.Draw(prev_img)
    curr_draw = ImageDraw.Draw(curr_img)

    prev_dom = prev_pair["dom"]
    curr_dom = curr_pair["dom"]

    results = []
    segments = []

    for el_prev, el_curr in zip(prev_dom, curr_dom):
        tag = el_prev.get("tag")
        if tag != el_curr.get("tag"):
            continue
        try:
            x1, y1, x2, y2 = map(int, el_prev["bbox"])
            w, h = x2 - x1, y2 - y1
            if w < min_size or h < min_size:
                continue

            crop_prev = prev_pair["image"].crop((x1, y1, x2, y2))
            crop_curr = curr_pair["image"].crop((x1, y1, x2, y2))

            lp_score = lpips_model.compute_distance(crop_prev, crop_curr)
            clip_score = clip_model.compute_similarity(crop_prev, crop_curr)

            is_changed = (lp_score > lpips_thresh) or (clip_score < clip_thresh)
            if is_changed:
                prev_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                curr_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

            results.append({
                "tag": tag,
                "bbox": (x1, y1, x2, y2),
                "LPIPS": round(lp_score, 4),
                "CLIP": round(clip_score, 4),
                "LPIPS_Detects_Change": int(lp_score > lpips_thresh),
                "CLIP_Detects_Change": int(clip_score < clip_thresh),
                "Change_Flag": int(is_changed)
            })

            segments.append({
                "tag": tag,
                "bbox": (x1, y1, x2, y2),
                "prev_crop": crop_prev,
                "curr_crop": crop_curr
            })

        except Exception as e:
            print(f"[!] Skipped region due to error: {e}")
            continue

    df_scores = pd.DataFrame(results)
    # ➕ ADD SUMMARY SECTION
    total = len(df_scores)
    changed = df_scores["Change_Flag"].sum() if total > 0 else 0
    summary = {
        "total_regions": total,
        "changed_regions": int(changed),
        "change_percent": round((changed / total) * 100, 2) if total else 0.0
    }

    return {
        "highlighted_prev": prev_img,
        "highlighted_curr": curr_img,
        "scores": df_scores,
        "segments": segments,
         "summary": summary
    }
