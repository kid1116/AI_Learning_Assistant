"""桌面线程结果分发与失败恢复：用临时数据和假模型验证。"""
from pathlib import Path
import tempfile
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

import long_term_memory
import memory
from appearance import DEFAULTS
from chat import ChatResult
from desktop import ChatWindow
from long_term_memory import LongTermMemory


class Memories:
    def get_memories(self):
        return []


def test_desktop_memory_editor_saves_selected_item_and_can_discard_draft():
    with tempfile.TemporaryDirectory() as folder, \
         patch.object(memory, "MEMORY_FILE", Path(folder) / "memory.json"), \
         patch.object(long_term_memory, "LONG_TERM_MEMORY_FILE", Path(folder) / "long_term_memory.json"), \
         patch("desktop.load_settings", return_value=DEFAULTS.copy()):
        memories = LongTermMemory()
        memories.add_memory("旧内容", "learning", "source-session")
        memories.add_memory("另一条记忆", "goal")
        original_id = memories.get_memories()[0]["id"]
        root = tk.Tk()
        window = ChatWindow(root, memory.SessionMemory(), memories)
        try:
            root.update()
            window.memory_button.invoke()
            dialog = next(child for child in root.winfo_children() if isinstance(child, tk.Toplevel))
            body = dialog.winfo_children()[0]
            editor = next(child for child in body.winfo_children() if isinstance(child, tk.Text))
            controls = body.winfo_children()[-1]
            picker = next(child for child in controls.winfo_children() if isinstance(child, ttk.Combobox))
            buttons = {child.cget("text"): child for child in controls.winfo_children()
                       if isinstance(child, ttk.Button)}

            assert editor.get("1.0", "end-1c") == "旧内容"
            editor.delete("1.0", "end")
            editor.insert("1.0", "新的学习偏好")
            picker.set("preference")
            buttons["保存修改"].invoke()

            first, second = LongTermMemory().get_memories()
            assert (first["id"], first["content"], first["category"], first["source_session_id"]) == (
                original_id, "新的学习偏好", "preference", "source-session",
            )
            assert second["content"] == "另一条记忆"

            editor.insert("end-1c", "未保存")
            with patch("desktop.messagebox.askyesno", return_value=False) as confirm:
                buttons["关闭"].invoke()
                confirm.assert_called_once()
                assert dialog.winfo_exists()
            with patch("desktop.messagebox.askyesno", return_value=True):
                buttons["关闭"].invoke()
            assert not dialog.winfo_exists()
            assert LongTermMemory().get_memories()[0]["content"] == "新的学习偏好"

            window.memory_button.invoke()
            dialog = next(child for child in root.winfo_children() if isinstance(child, tk.Toplevel))
            controls = dialog.winfo_children()[0].winfo_children()[-1]
            delete = next(child for child in controls.winfo_children()
                          if isinstance(child, ttk.Button) and child.cget("text") == "删除")
            with patch("desktop.messagebox.askyesno", return_value=False):
                delete.invoke()
            assert len(LongTermMemory().get_memories()) == 2
            with patch("desktop.messagebox.askyesno", return_value=True):
                delete.invoke()
                assert [item["content"] for item in LongTermMemory().get_memories()] == ["另一条记忆"]
                delete.invoke()
            assert not LongTermMemory().get_memories()
            assert delete.instate(["disabled"])
        finally:
            root.after_cancel(window.poll_id)
            root.destroy()


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
