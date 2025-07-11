import os
import sys
from utils import capture_screenshot

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

# 🔧 List of URLs or routes to capture
ROUTES = {
    "homepage": "http://localhost:5173/"
}

def save_ui_snapshots(commit_hash):
    baseline_dir = os.path.join(CURRENT_DIR, 'baseline', commit_hash)
    print(f"Creating baseline directory: {baseline_dir}")
    os.makedirs(baseline_dir, exist_ok=True)

    for name, url in ROUTES.items():
        print(f"Capturing {name} at {url}")
        try:
            capture_screenshot(
                url=url,
                file_name=name,
                file_path=baseline_dir
            )
            print(f"✓ Captured {name}")
        except Exception as e:
            print(f"✗ Failed to capture {name}: {e}")

if __name__ == '__main__':
    commit = sys.argv[1] if len(sys.argv) > 1 else 'default'
    print(f"Starting visual test script for commit: {commit}")
    save_ui_snapshots(commit)
    print("Script completed.")
