"""桌面线程结果分发与失败恢复：用临时数据和假模型验证。"""
from pathlib import Path
import tempfile
import time
import tkinter as tk
from unittest.mock import patch

import memory
from appearance import DEFAULTS
from chat import ChatResult
from desktop import ChatWindow


class Memories:
    def get_memories(self):
        return []


def test_input_and_send_button_remain_visible_when_window_is_small():
    with tempfile.TemporaryDirectory() as folder, \
         patch.object(memory, "MEMORY_FILE", Path(folder) / "memory.json"), \
         patch("desktop.load_settings", return_value=DEFAULTS.copy()):
        root = tk.Tk()
        window = ChatWindow(root, memory.SessionMemory(), Memories())
        try:
            for size in (12, 20):
                window.settings["size"] = size
                window.apply_theme()
                root.geometry("850x620")
                root.update()
                for widget in (window.composer, window.send_button):
                    assert widget.winfo_viewable(), f"{widget} 被历史区域挤出窗口"
                    bottom = widget.winfo_rooty() + widget.winfo_height()
                    assert bottom <= root.winfo_rooty() + root.winfo_height()
                assert window.composer.winfo_height() >= 60
        finally:
            root.after_cancel(window.poll_id)
            root.destroy()


def test_desktop_send_success_and_failure_restores_draft():
    with tempfile.TemporaryDirectory() as folder, \
         patch.object(memory, "MEMORY_FILE", Path(folder) / "memory.json"), \
         patch.object(memory, "generate_title", return_value="标题"), \
         patch("desktop.load_settings", return_value=DEFAULTS.copy()):
        sessions = memory.SessionMemory()

        class Service:
            def reply(self, text):
                if text == "失败":
                    return ChatResult(None)
                sessions.add_turn(text, "测试回答")
                return ChatResult("测试回答")

        root = tk.Tk()
        root.withdraw()
        window = ChatWindow(root, sessions, Memories(), Service())
        try:
            for question, expected in [("你好", "测试回答"), ("失败", "本轮未保存")]:
                window.composer.insert("1.0", question)
                window.send()
                assert window.busy
                deadline = time.monotonic() + 5
                while window.busy and time.monotonic() < deadline:
                    root.update()
                    time.sleep(.02)
                assert not window.busy
                assert expected in window.transcript.get("1.0", "end")
            assert window.composer.get("1.0", "end-1c") == "失败"
            assert len(sessions.get_current_session_messages()) == 2
            window.open_appearance()
            root.update()
            window.appearance_dialog.destroy()
        finally:
            root.after_cancel(window.poll_id)
            root.destroy()
