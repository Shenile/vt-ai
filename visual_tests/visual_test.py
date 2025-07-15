import os
import sys
from utils import capture_screenshot_and_dom  # updated import



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
            capture_screenshot_and_dom(  # updated function
                url=url,
                file_name=name,
                file_path=baseline_dir
            )
            print(f"✓ Captured {name}")
        except Exception as e:
            print(f"✗ Failed to capture {name}: {e}")
