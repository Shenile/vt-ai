import os
import json
import subprocess
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
BASELINE_DIR = BASE_DIR / "baseline"
CACHE_FILE = BASELINE_DIR / "commit_cache.json"

UI_EXTENSIONS = {".html", ".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".sass", ".less"}
UI_FOLDERS = {"templates", "static", "public", "components", "assets"}


def get_changed_files(commit_id):
    """Returns list of changed file paths in a given commit."""
    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=", commit_id],
        capture_output=True, text=True, check=True
    )
    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

def is_ui_file(filepath):
    """Checks if the file is a UI-related file."""
    path = Path(filepath)
    return (
        path.suffix in UI_EXTENSIONS or
        any(part in UI_FOLDERS for part in path.parts)
    )

def is_ui_only_commit(commit_id):
    """Returns True if all files changed in the commit are UI files."""
    files = get_changed_files(commit_id)
    return any(is_ui_file(f) for f in files) and len(files) > 0

def get_ui_only_commits(n=20):
    """Returns a list of last N commit IDs that are UI-only."""
    result = subprocess.run(
        ["git", "rev-list", "--max-count", str(n), "HEAD"],
        capture_output=True, text=True, check=True
    )
    commit_ids = result.stdout.strip().split("\n")
    return [cid for cid in commit_ids if is_ui_only_commit(cid)]


# ------------------------------
def load_commit_history() -> dict:
    if not CACHE_FILE.exists():
        print("[•] No cache file found. Initializing new history.")
        return {"history": []}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[✗] Cache file is corrupted. Reinitializing.")
        return {"history": []}
    
def save_commit_to_cache(commit_id: str):
    cache = load_commit_history()
    if commit_id not in cache["history"]:
        cache["history"].append(commit_id)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"[✓] Tracked commit: {commit_id}")
    else:
        print(f"[•] Commit {commit_id} already tracked.")
#--------------------------------

from PIL import Image

def get_next_commit_pair(page_name="test_home_page"):
    """
    Returns the next valid commit pair with loaded images and DOMs.
    """
    cache = load_commit_history()
    history = cache.get("history", [])

    if len(history) < 2:
        print("[✗] Not enough commits in baseline to compare.")
        return None

    for i in range(len(history) - 1):
        last_processed = history[i]
        next_commit = history[i + 1]

        prev_img_path = BASELINE_DIR / last_processed / f"{page_name}.png"
        prev_dom_path = BASELINE_DIR / last_processed / f"{page_name}_dom.json"

        curr_img_path = BASELINE_DIR / next_commit / f"{page_name}.png"
        curr_dom_path = BASELINE_DIR / next_commit / f"{page_name}_dom.json"

        if all(p.exists() for p in [prev_img_path, prev_dom_path, curr_img_path, curr_dom_path]):
            try:
                return {
                    "prev_commit": last_processed,
                    "curr_commit": next_commit,
                    "prev": {
                        "image": Image.open(prev_img_path).convert("RGB"),
                        "dom": json.load(open(prev_dom_path, encoding="utf-8"))
                    },
                    "curr": {
                        "image": Image.open(curr_img_path).convert("RGB"),
                        "dom": json.load(open(curr_dom_path, encoding="utf-8"))
                    }
                }
            except Exception as e:
                print(f"[✗] Failed to load baseline files for commit pair {last_processed} → {next_commit}: {e}")
                continue

    print("[✗] No valid commit pair found with both image + dom.")
    return None
