from llm import ask_llm
from prompt import SYSTEM_PROMPT
from memory import SessionMemory
from long_term_memory import (LongTermMemory,extract_memories)

#初始化memory
session_memory = SessionMemory()
Long_term_memory = LongTermMemory()

def show_help():
    print("\n========== 命令 ==========")

    print("/new: 新建一个对话")
    print("/history: 查看所有对话")
    print("/switch 会话ID: 切换到指定对话")
    print("/delete 会话ID: 删除指定对话")
    print("/memory: 查看长期记忆")
    print("/forget <Memory ID>: 删除指定长期记忆")
    print("/exit”: 退出程序")

    print("==========================\n")

#显示历史session
def show_history():

    sessions = session_memory.list_sessions()

    current_id = session_memory.get_current_session_id()

    print("\n========== 对话历史 ==========")

    for index, session in enumerate(
        sessions,
        start=1
    ):

        marker = ""

        if session["id"] == current_id:
            marker = " ← 当前"

        print(
            f"{index}. "
            f"{session['title']} "
            f"[{session['id']}]"
            f"{marker}"
        )

    print("==============================\n")

#查看长期记忆
def show_memory():
    memories = (Long_term_memory.get_memories())

    print("\n===== Long-term Memory =====")

    if not memories:
        print("not exist long-term memory")

    else:
        for index,memory_item in enumerate(memories,start=1):
            print(
                
            )


#主程序：
print(
    f"\nCurrrent Session:{memory.get_current_session_title()}"
)
print("Input \"/help\" to view available instructions")

while True:
    user_input = input(
        f"[{memory.get_current_session_title()}] You:"
    ).strip()

    if not user_input:
        continue

    if user_input == "/exit":
        print("AI assistant exit")
        break

    if user_input == "/help":
        show_help()
        continue

    if user_input == "/new":
        session_id = memory.create_session()
        print("\n已创建新对话")
        print(f"session id:{session_id}")
        continue

    if user_input == "/history":
        show_history()
        continue

    #切换session
    if user_input.startswith("/switch"):
        parts = user_input.split()
        if len(parts) != 2:
            print(
                "\n用法:/switch 会话ID"
            )
            continue

        session_id = parts[1]
        success = memory.switch_session(
            session_id
        )

        if success:
            print(
                f"\n已切换到:"
                f"{memory.get_current_session_title()}"
            )
        else:
            print(
                "\n找不到这个 Session。"
            )
        continue

    #删除session
    if user_input.startswith("/delete"):
        parts = user_input.split()
        if len(parts) != 2:
            print(
                "\n用法:/delete 会话ID"
            )
            continue

        session_id = parts[1]
        # 找不到 Session
        if session_id not in memory.data["sessions"]:
            print(
                "\n找不到这个 Session。"
            )
            continue

        session = memory.data["sessions"][session_id]

        # 二次确认
        confirm = input(
            f"\n确定删除「{session['title']}」吗？"
            "\n输入 y 确认："
        )

        if confirm.lower() == "y":
            memory.delete_session(
                session_id
            )
            print(
                "\nSession 已删除。"
            )
            print(
                f"当前会话："
                f"{memory.get_current_session_title()}"
            )
        else:
            print(
                "\n已取消删除。"
            )
        continue

   
    history = memory.get_current_session_messages()
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # 添加当前 Session 历史
    messages.extend(history)

    # 添加本次用户问题
    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    answer = ask_llm(messages)

    print("\nAI assistant:")
    print(answer)

    memory.add_message(
            "user",
            user_input
        )

    memory.add_message(
            "assistant",
            answer
        )
