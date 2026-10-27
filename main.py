"""命令行入口：处理交互和命令，单轮对话交给 ChatService。"""

from chat import ChatService
from long_term_memory import LongTermMemory
from memory import SessionMemory


def show_help():
    print("\n========== 命令 ==========\n"
          "/help: 查看命令\n"
          "/new: 新建对话\n"
          "/history: 查看所有对话\n"
          "/switch 会话ID: 切换对话\n"
          "/delete 会话ID: 删除对话\n"
          "/memory: 查看长期记忆\n"
          "/forget 记忆ID: 删除长期记忆\n"
          "/exit: 退出程序\n"
          "==========================\n")


def handle_command(text, sessions, memories):
    """返回 False 表示退出；按完整命令名匹配。"""
    parts = text.split()
    command, arguments = parts[0], parts[1:]
    arity = {"/help": 0, "/exit": 0, "/new": 0, "/history": 0,
             "/memory": 0, "/switch": 1, "/delete": 1, "/forget": 1}
    if command not in arity:
        print("未知命令，输入 /help 查看可用命令。")
        return True
    if len(arguments) != arity[command]:
        suffix = " 记忆ID" if command == "/forget" else " 会话ID" if arity[command] else ""
        print(f"用法：{command}{suffix}")
        return True

    if command == "/exit":
        return False
    if command == "/help":
        show_help()
    elif command == "/new":
        print(f"已创建新对话：{sessions.create_session()}")
    elif command == "/history":
        for item in sessions.list_sessions():
            marker = " ← 当前" if item["id"] == sessions.get_current_session_id() else ""
            print(f"{item['title']} [{item['id']}]{marker}")
    elif command == "/switch":
        if sessions.switch_session(arguments[0]):
            print(f"已切换到：{sessions.get_current_session_title()}")
        else:
            print("找不到这个会话。")
    elif command == "/memory":
        items = memories.get_memories()
        if not items:
            print("暂无长期记忆。")
        for item in items:
            print(f"[{item['id']}] [{item['category']}] {item['content']}")
    elif command == "/delete":
        target = next((item for item in sessions.list_sessions() if item["id"] == arguments[0]), None)
        if target is None:
            print("找不到这个会话。")
        elif input(f"确定删除「{target['title']}」？输入 y 确认：").strip().lower() == "y":
            sessions.delete_session(target["id"])
            print("会话已删除。")
        else:
            print("已取消。")
    elif command == "/forget":
        target = next((item for item in memories.get_memories() if item["id"] == arguments[0]), None)
        if target is None:
            print("找不到这条长期记忆。")
        elif input(f"确定删除「{target['content']}」？输入 y 确认：").strip().lower() == "y":
            memories.delete_memory(target["id"])
            print("长期记忆已删除。")
        else:
            print("已取消。")
    return True


def chat_loop(sessions, memories):
    service = ChatService(sessions, memories)
    print(f"\n当前会话：{sessions.get_current_session_title()}")
    print("输入 /help 查看可用命令。")
    while True:
        try:
            text = input(f"[{sessions.get_current_session_title()}] You: ").strip()
            if not text:
                continue
            if text.startswith("/"):
                if not handle_command(text, sessions, memories):
                    break
                continue
            result = service.reply(text)
            if result.answer is None:
                print("AI 服务暂时不可用，本轮未保存，请重试。")
                continue
            print(f"\nAI assistant:\n{result.answer}")
            if result.added_memories:
                print(f"\n[Memory] 新增 {result.added_memories} 条长期记忆。")
            for warning in result.warnings:
                print(f"[提示] {warning}")
        except (EOFError, KeyboardInterrupt):
            break
        except (ValueError, OSError) as error:
            print(f"操作失败：{error}")
    print("AI assistant exit")


def main():
    try:
        sessions = SessionMemory()
        memories = LongTermMemory()
    except (ValueError, OSError) as error:
        print(f"无法加载记忆文件，请检查 data 目录，原文件未被重置：{error}")
        return 1
    chat_loop(sessions, memories)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
