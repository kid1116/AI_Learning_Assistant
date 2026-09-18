import json
from pathlib import Path

# 当前项目目录
BASE_DIR = Path(__file__).parent

# 记忆文件
MEMORY_FILE = BASE_DIR / "data" / "memory.json"


def load_memory():
    """
    从文件中读取历史聊天记录
    """
    if not MEMORY_FILE.exists():
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return []


def save_memory(messages):
    """
    将聊天记录保存到文件
    """
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            messages,
            f,
            ensure_ascii=False,
            indent=4
        )


def clear_memory():
    """
    清空历史聊天记录
    """
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()