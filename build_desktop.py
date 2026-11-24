"""Build the standalone Windows app from the project's virtual environment."""

import os
from pathlib import Path
import sys


def main():
    if os.name != "nt":
        raise SystemExit("请在 Windows 上构建桌面应用。")
    project = Path(__file__).resolve().parent
    work = project / ".build"
    # 构建工具单独安装，日常运行不需要 PyInstaller。
    sys.path.insert(0, str(work / "packaging"))
    try:
        from PyInstaller.__main__ import run
    except ImportError as error:
        raise SystemExit("请先安装 requirements-build.txt 中的构建依赖。") from error
    run([
        "--noconfirm", "--onedir", "--windowed", "--noupx",
        "--name", "AI-Learning-Assistant",
        "--distpath", str(project / "dist"),
        "--workpath", str(work / "pyinstaller"),
        "--specpath", str(work),
        str(project / "desktop.py"),
    ])


if __name__ == "__main__":
    main()
