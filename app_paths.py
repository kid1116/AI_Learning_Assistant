"""Keep mutable files outside the app bundle."""

import os
import sys
from pathlib import Path


def app_home():
    override = os.getenv("AI_LEARNING_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent

    executable_dir = Path(sys.executable).resolve().parent
    dist_dir = executable_dir.parent
    project = dist_dir.parent
    if (dist_dir.name.lower() == "dist"
            and (project / "desktop.py").is_file()
            and (project / ".env.example").is_file()):
        return project
    return executable_dir


APP_HOME = app_home()
DATA_DIR = APP_HOME / "data"
ENV_FILE = APP_HOME / ".env"
