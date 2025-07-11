import os
import time
import subprocess

# Path to your local cloned repository
REPO_PATH = os.path.dirname(__file__)
BRANCH = "visual-baselines"
INTERVAL = 300  # in seconds (5 minutes)

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

def sync_repo():
    print(f"Syncing {BRANCH} branch at {REPO_PATH}")
    run_git_command(["checkout", BRANCH], cwd=REPO_PATH)
    run_git_command(["pull", "origin", BRANCH], cwd=REPO_PATH)
    print(f"[✓] Synced at {time.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    while True:
        sync_repo()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
