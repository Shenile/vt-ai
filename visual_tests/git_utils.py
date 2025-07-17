

import subprocess
from pathlib import Path

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
