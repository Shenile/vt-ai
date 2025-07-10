import subprocess
commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
print(f"🧾 Latest commit hash: {commit_hash}")
