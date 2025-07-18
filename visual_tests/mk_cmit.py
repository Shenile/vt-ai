from utils import run_git_command
from pathlib import Path

run_git_command(["add", "vt-ai-fe/src/App.jsx"], cwd=Path.cwd().parent)
run_git_command(["commit", "-m", "ui-change-commit"], cwd=Path.cwd().parent)
run_git_command(["push", "origin", "main"], cwd=Path.cwd().parent)