"""外观文件使用临时目录，不修改用户配置。"""
from pathlib import Path
import tempfile

from appearance import DEFAULTS, accent_text, load_settings, save_settings, validate_settings


def test_invalid_settings_fall_back_to_safe_defaults():
    assert validate_settings(None) == DEFAULTS
    assert validate_settings({"theme": [], "accent": "red", "size": True, "font": " "}) == DEFAULTS


def test_appearance_roundtrip_and_corrupted_file_fallback():
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "appearance.json"
        assert load_settings(path) == DEFAULTS
        custom = {"theme": "暖纸", "accent": "#2266aa", "size": 16, "font": "Arial"}
        save_settings(custom, path)
        assert load_settings(path) == custom
        path.write_text("broken", encoding="utf-8")
        assert load_settings(path) == DEFAULTS


def test_accent_automatically_uses_contrasting_text():
    assert accent_text("#FFFFFF") == "#11131D"
    assert accent_text("#000000") == "#FFFFFF"
