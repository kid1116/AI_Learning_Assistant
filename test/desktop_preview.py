"""手工界面预览：临时数据与模拟回答，不调用 API、不写用户记忆。"""
import sys
from pathlib import Path
import tempfile
import time
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import memory
from chat import ChatResult
from desktop import ChatWindow


class PreviewMemories:
    def get_memories(self):
        return []


class PreviewService:
    def __init__(self, sessions):
        self.sessions = sessions

    def reply(self, text):
        time.sleep(.5)
        answer = "这是离线预览回答。\n\n窗口支持多轮对话、会话切换，以及可随时调整的主题、字体和强调色。\n\n正式窗口会连接现有的 DeepSeek 对话服务。"
        self.sessions.add_turn(text, answer)
        return ChatResult(answer)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as folder, \
         patch.object(memory, "MEMORY_FILE", Path(folder) / "memory.json"), \
         patch.object(memory, "generate_title", return_value="我的学习空间"):
        sessions = memory.SessionMemory()
        root = tk.Tk()
        window = ChatWindow(root, sessions, PreviewMemories(), PreviewService(sessions))
        root.title("学习助手 · 离线界面预览")
        root.mainloop()
