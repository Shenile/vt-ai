import os
import sys
from utils import capture_screenshot

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

def save_ui_snapshot(commit_hash):
    baseline_dir = os.path.join(CURRENT_DIR, 'baseline', commit_hash)
    print(f"Creating baseline directory: {baseline_dir}")
    os.makedirs(baseline_dir, exist_ok=True)

    print(f"Capturing UI snapshot for commit: {commit_hash}")
    capture_screenshot(
        url="https://www.google.com/",
        file_name="ui_snapshot",
        file_path=baseline_dir
    )
    print("UI snapshot saved successfully.")

if __name__ == '__main__':
    commit = sys.argv[1] if len(sys.argv) > 1 else 'default'
    print(f"Starting visual test script for commit: {commit}")
    save_ui_snapshot(commit)
    print("Script completed.")
