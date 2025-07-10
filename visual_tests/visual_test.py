import os
import sys
from utils import capture_screenshot

CURRENT_DIR = os.path.dirname(__file__)  # e.g., /visual-tests

def save_ui_snapshot(commit_hash):
    # Create a directory using the commit hash
    baseline_dir = os.path.join(CURRENT_DIR, 'baseline', commit_hash)
    os.makedirs(baseline_dir, exist_ok=True)

    capture_screenshot(
        url="https://www.google.com/",
        file_name="ui_snapshot",
        file_path=baseline_dir
    )

if __name__ == '__main__':
    commit = sys.argv[1] if len(sys.argv) > 1 else 'default'
    save_ui_snapshot(commit)