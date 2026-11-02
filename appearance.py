"""桌面外观配置，与对话记忆分开保存。"""
import json
import os
from pathlib import Path
import re
import tempfile

SETTINGS_FILE = Path(__file__).resolve().parent / "data" / "appearance.json"
DEFAULTS = {"theme": "深空", "accent": "#9B8AFF", "font": "Microsoft YaHei UI", "size": 12}
PALETTES = {
    "深空": {"bg": "#11131D", "panel": "#191C2B", "input": "#22263A", "text": "#E8EAF5", "muted": "#A1A7BE"},
    "明亮": {"bg": "#F3F5FB", "panel": "#FFFFFF", "input": "#E9EDF7", "text": "#20263B", "muted": "#626D88"},
    "暖纸": {"bg": "#F2EDE2", "panel": "#FCF8EF", "input": "#E9E2D3", "text": "#343E35", "muted": "#6A7468"},
}


def validate_settings(value):
    result = DEFAULTS.copy()
    if not isinstance(value, dict):
        return result
    if isinstance(value.get("theme"), str) and value["theme"] in PALETTES:
        result["theme"] = value["theme"]
    if isinstance(value.get("accent"), str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value["accent"]):
        result["accent"] = value["accent"]
    if isinstance(value.get("font"), str) and value["font"].strip():
        result["font"] = value["font"].strip()[:80]
    size = value.get("size")
    if type(size) is int and 10 <= size <= 20:
        result["size"] = size
    return result


def load_settings(path=SETTINGS_FILE):
    try:
        return validate_settings(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return DEFAULTS.copy()


def save_settings(value, path=SETTINGS_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(validate_settings(value), stream, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def accent_text(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    luminance = sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))
    return "#11131D" if luminance > .179 else "#FFFFFF"
