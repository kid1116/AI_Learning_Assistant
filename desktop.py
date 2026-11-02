"""独立 Tk 桌面窗口。所有 Tk 操作仅在主线程执行。"""
import queue
import threading
import tkinter as tk
from tkinter import colorchooser, font, messagebox, ttk

from appearance import DEFAULTS, PALETTES, accent_text, load_settings, save_settings
from chat import ChatService
from config import MAX_USER_INPUT_CHARS
from long_term_memory import LongTermMemory
from memory import SessionMemory


class ChatWindow:
    def __init__(self, root, sessions, memories, service=None):
        self.root, self.sessions, self.memories = root, sessions, memories
        self.service = service if service is not None else ChatService(sessions, memories)
        self.settings = load_settings()
        self.events = queue.Queue()
        self.busy = False
        self.appearance_dialog = None
        self.session_ids = []
        self.widgets = []
        root.title("学习助手 · Personal AI")
        root.geometry("1120x780")
        root.minsize(850, 620)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self.sidebar = self.frame(root, "panel", padx=20, pady=24)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.label(self.sidebar, "STUDY / SPACE", accent=True, bold=True).pack(anchor="w")
        self.label(self.sidebar, "个人 AI 学习助手", bold=True).pack(anchor="w", pady=(8, 24))
        self.new_button = self.button(self.sidebar, "＋  新建对话", self.new_session, primary=True)
        self.new_button.pack(fill="x", pady=(0, 20))
        self.label(self.sidebar, "你的对话", muted=True).pack(anchor="w", pady=(0, 10))
        self.session_list = tk.Listbox(self.sidebar, width=23, bd=0, highlightthickness=0,
                                      activestyle="none", exportselection=False)
        self.session_list.pack(fill="both", expand=True)
        self.session_list.bind("<<ListboxSelect>>", self.select_session)
        self.memory_button = self.button(self.sidebar, "长期记忆", self.show_memories)
        self.memory_button.pack(fill="x", pady=(14, 6))
        self.delete_button = self.button(self.sidebar, "删除当前对话", self.delete_session)
        self.delete_button.pack(fill="x", pady=6)
        self.button(self.sidebar, "外观与个性化", self.open_appearance).pack(fill="x", pady=(6, 0))

        self.main_panel = self.frame(root, padx=30, pady=24)
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        self.title = self.label(self.main_panel, "", bold=True)
        self.title.pack(anchor="w")
        self.label(self.main_panel, "从一个问题开始，慢慢建立自己的知识世界。", muted=True).pack(anchor="w", pady=(6, 16))
        chat_frame = self.frame(self.main_panel)
        chat_frame.pack(fill="both", expand=True)
        self.transcript = tk.Text(chat_frame, wrap="word", bd=0, padx=20, pady=20,
                                  highlightthickness=0, state="disabled", cursor="arrow")
        self.transcript.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(chat_frame, command=self.transcript.yview)
        scrollbar.pack(side="right", fill="y")
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.status = self.label(self.main_panel, "就绪", muted=True)
        self.status.pack(anchor="w", pady=(12, 8))
        self.composer = tk.Text(self.main_panel, height=4, wrap="word", bd=0,
                                padx=16, pady=12, highlightthickness=1, undo=True)
        self.composer.pack(fill="x")
        self.composer.bind("<Return>", self.on_enter)
        self.composer.bind("<Control-Return>", lambda event: self.send())
        footer = self.frame(self.main_panel)
        footer.pack(fill="x", pady=(10, 0))
        self.send_button = self.button(footer, "发送  ↗", self.send, primary=True)
        self.send_button.pack(side="right")
        self.label(footer, "Enter 发送 · Shift+Enter 换行", muted=True).pack(side="left")
        self.apply_theme()
        self.refresh_sessions()
        self.render_history()
        self.composer.focus_set()
        self.poll_id = root.after(100, self.poll_events)

    def frame(self, parent, role="bg", **kwargs):
        widget = tk.Frame(parent, **kwargs)
        self.widgets.append((widget, "frame", role))
        return widget

    def label(self, parent, text, muted=False, bold=False, accent=False):
        widget = tk.Label(parent, text=text, anchor="w", justify="left")
        self.widgets.append((widget, "label", (muted, bold, accent)))
        return widget

    def button(self, parent, text, command, primary=False):
        widget = tk.Button(parent, text=text, command=command, bd=0, padx=14, pady=10,
                           cursor="hand2", relief="flat")
        self.widgets.append((widget, "button", primary))
        return widget

    def apply_theme(self):
        settings = self.settings
        palette = PALETTES[settings["theme"]]
        accent = settings["accent"]
        family, size = settings["font"], settings["size"]
        self.root.configure(bg=palette["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=palette["panel"])
        style.configure("TLabel", background=palette["panel"], foreground=palette["text"], font=(family, size))
        style.configure("TButton", background=palette["input"], foreground=palette["text"], padding=7)
        style.configure("TCombobox", fieldbackground=palette["input"], background=palette["input"],
                        foreground=palette["text"], arrowcolor=accent)
        style.map("TCombobox", fieldbackground=[("readonly", palette["input"])],
                  foreground=[("readonly", palette["text"])])
        for widget, kind, option in self.widgets:
            if not widget.winfo_exists():
                continue
            if kind == "frame":
                widget.configure(bg=palette[option])
            elif kind == "label":
                muted, bold, use_accent = option
                widget.configure(bg=widget.master.cget("bg"),
                                 fg=accent if use_accent else palette["muted" if muted else "text"],
                                 font=(family, size, "bold" if bold else "normal"))
            else:
                widget.configure(bg=accent if option else palette["input"],
                                 fg=accent_text(accent) if option else palette["text"],
                                 activebackground=accent, activeforeground=accent_text(accent),
                                 disabledforeground=palette["muted"], font=(family, size))
        self.session_list.configure(bg=palette["panel"], fg=palette["text"],
                                    selectbackground=palette["input"], selectforeground=accent,
                                    font=(family, size), disabledforeground=palette["muted"])
        for widget in (self.transcript, self.composer):
            widget.configure(bg=palette["input"], fg=palette["text"], insertbackground=accent,
                             selectbackground=accent, selectforeground=accent_text(accent),
                             font=(family, size), highlightbackground=palette["panel"],
                             highlightcolor=accent, spacing1=5, spacing3=10)
        self.transcript.tag_configure("user", foreground=accent, font=(family, size, "bold"))
        self.transcript.tag_configure("assistant", foreground=palette["text"], font=(family, size, "bold"))
        self.transcript.tag_configure("note", foreground=palette["muted"])

    def refresh_sessions(self):
        items = self.sessions.list_sessions()
        self.session_ids = [item["id"] for item in items]
        self.session_list.delete(0, "end")
        for item in items:
            self.session_list.insert("end", item["title"] or "未命名对话")
        current = self.sessions.get_current_session_id()
        if current in self.session_ids:
            index = self.session_ids.index(current)
            self.session_list.selection_set(index)
            self.session_list.see(index)
        self.title.configure(text=self.sessions.get_current_session_title() or "新对话")

    def append(self, role, content):
        self.transcript.configure(state="normal")
        names = {"user": "你", "assistant": "学习助手", "note": "提示"}
        self.transcript.insert("end", names.get(role, role) + "\n", role)
        self.transcript.insert("end", content + "\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def render_history(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")
        messages = self.sessions.get_current_session_messages()
        if not messages:
            self.append("note", "欢迎回来。你可以讨论知识、规划学习，或继续推进自己的项目。")
        for item in messages:
            self.append(item["role"], item["content"] or "")

    def new_session(self):
        if not self.busy:
            self.sessions.create_session()
            self.refresh_sessions()
            self.render_history()

    def select_session(self, event=None):
        selected = self.session_list.curselection()
        if not self.busy and selected:
            target = self.session_ids[selected[0]]
            if target != self.sessions.get_current_session_id():
                self.sessions.switch_session(target)
                self.refresh_sessions()
                self.render_history()

    def delete_session(self):
        if not self.busy and messagebox.askyesno("删除会话", "确定永久删除当前对话？", parent=self.root):
            self.sessions.delete_session(self.sessions.get_current_session_id())
            self.refresh_sessions()
            self.render_history()

    def on_enter(self, event):
        if event.state & 1:  # Shift+Enter 保留换行
            return None
        self.send()
        return "break"

    def set_busy(self, value):
        self.busy = value
        state = "disabled" if value else "normal"
        for widget in (self.send_button, self.new_button, self.delete_button, self.memory_button, self.session_list):
            widget.configure(state=state)

    def send(self):
        if self.busy:
            return "break"
        text = self.composer.get("1.0", "end-1c").strip()
        if not text:
            return "break"
        if len(text) > MAX_USER_INPUT_CHARS:
            messagebox.showwarning("输入过长", f"请控制在 {MAX_USER_INPUT_CHARS} 字符以内。", parent=self.root)
            return "break"
        self.pending_input = text
        self.composer.delete("1.0", "end")
        self.append("user", text)
        self.set_busy(True)
        self.status.configure(text="正在思考 · 可能调用工具；随后保存对话并更新记忆…")
        threading.Thread(target=self.request, args=(text,), daemon=True).start()
        return "break"

    def request(self, text):
        try:
            self.events.put(("result", self.service.reply(text)))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                self.set_busy(False)
                if kind == "error" or value.answer is None:
                    detail = value if kind == "error" else "模型服务不可用，请检查 .env 中的密钥、模型配置或网络。"
                    self.render_history()
                    self.append("note", str(detail) + "\n本轮未保存，原问题已放回输入框。")
                    draft = self.composer.get("1.0", "end-1c")
                    self.composer.delete("1.0", "end")
                    self.composer.insert("1.0", self.pending_input + ("\n\n" + draft if draft else ""))
                    self.status.configure(text="请求未完成 · 可重试")
                else:
                    self.append("assistant", value.answer)
                    for warning in value.warnings:
                        self.append("note", warning)
                    self.refresh_sessions()
                    self.status.configure(text=f"已完成 · 新增 {value.added_memories} 条长期记忆" if not value.warnings else "已完成 · 请留意保存或记忆提示")
        except queue.Empty:
            pass
        self.poll_id = self.root.after(100, self.poll_events)

    def show_memories(self):
        if self.busy:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("长期记忆 · 只读")
        dialog.geometry("650x450")
        palette = PALETTES[self.settings["theme"]]
        text = tk.Text(dialog, wrap="word", padx=20, pady=20, bg=palette["input"],
                       fg=palette["text"], font=(self.settings["font"], self.settings["size"]))
        text.pack(fill="both", expand=True)
        items = self.memories.get_memories()
        text.insert("1.0", "\n\n".join(f"[{item['category']}] {item['content']}" for item in items) or "暂无长期记忆。")
        text.configure(state="disabled")

    def open_appearance(self):
        if self.appearance_dialog and self.appearance_dialog.winfo_exists():
            self.appearance_dialog.lift()
            return
        dialog = self.appearance_dialog = tk.Toplevel(self.root)
        dialog.title("外观与个性化")
        dialog.geometry("420x430")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        original = self.settings.copy()
        theme = tk.StringVar(value=self.settings["theme"])
        family = tk.StringVar(value=self.settings["font"])
        size = tk.IntVar(value=self.settings["size"])
        accent = tk.StringVar(value=self.settings["accent"])
        body = ttk.Frame(dialog, padding=24)
        body.pack(fill="both", expand=True)
        for label, variable, values in (
            ("主题", theme, list(PALETTES)),
            ("字体", family, sorted(set(font.families(self.root)))),
            ("字号", size, list(range(10, 21))),
        ):
            ttk.Label(body, text=label).pack(anchor="w", pady=(8, 4))
            ttk.Combobox(body, textvariable=variable, values=values, state="readonly").pack(fill="x")

        def choose_color():
            color = colorchooser.askcolor(accent.get(), parent=dialog)[1]
            if color:
                accent.set(color)

        ttk.Button(body, text="选择强调色…", command=choose_color).pack(fill="x", pady=(16, 4))

        def preview(*args):
            self.settings = {"theme": theme.get(), "font": family.get(), "size": size.get(), "accent": accent.get()}
            self.apply_theme()

        def cancel():
            self.settings = original
            self.apply_theme()
            dialog.destroy()

        def save():
            try:
                save_settings(self.settings)
            except OSError as error:
                messagebox.showerror("保存失败", str(error), parent=dialog)
                return
            dialog.destroy()

        def reset():
            theme.set(DEFAULTS["theme"])
            family.set(DEFAULTS["font"])
            size.set(DEFAULTS["size"])
            accent.set(DEFAULTS["accent"])

        for variable in (theme, family, size, accent):
            variable.trace_add("write", preview)
        controls = ttk.Frame(body)
        controls.pack(fill="x", pady=16)
        ttk.Button(controls, text="恢复默认", command=reset).pack(side="left")
        ttk.Button(controls, text="保存", command=save).pack(side="right")
        ttk.Button(controls, text="取消", command=cancel).pack(side="right", padx=6)
        dialog.protocol("WM_DELETE_WINDOW", cancel)

    def close(self):
        if self.busy:
            messagebox.showinfo("请求进行中", "请等本轮请求和保存完成后再关闭窗口。", parent=self.root)
            return
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    # 同时打开多个桌面实例会覆盖 JSON；用操作系统文件锁阻止重复启动。
    from pathlib import Path
    import msvcrt
    root = tk.Tk()
    root.withdraw()
    root.report_callback_exception = lambda kind, error, trace: messagebox.showerror("操作失败", str(error), parent=root)
    lock_path = Path(__file__).resolve().parent / "data" / "desktop.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = lock_path.open("a+b")
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        messagebox.showinfo("助手已打开", "已有桌面窗口正在运行，请在任务栏查找。", parent=root)
        lock.close()
        root.destroy()
        return
    try:
        ChatWindow(root, SessionMemory(), LongTermMemory())
        root.deiconify()
        root.mainloop()
    except Exception as error:
        messagebox.showerror("启动失败", str(error), parent=root)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
