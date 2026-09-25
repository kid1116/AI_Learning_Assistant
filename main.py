from llm import ask_llm
from prompt import SYSTEM_PROMPT
from memory import SessionMemory
from long_term_memory import LongTermMemory

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
                f"{index}."
                f"[{memory_item['id']}]"
                f"[{memory_item['category']}]"
            )

            print(
                f"{memory_item['content']}"
            )

    print("=============================\n")

def build_memory_context():
    memories =(
        Long_term_memory.get_memories()
    )

    if not memories:
        return ""

    memory_lines = []

    for memory_item in memories:
        memory_lines.append("- "+memory_item["content"])

    return (
        "\n\n"
        "以下是关于用户的长期记忆。"
        "回答时仅在相关情况下使用,不要主动暴露完整记忆列表： \n"
        +"\n".join(memory_lines)
    )

#主程序：
print(
    f"\nCurrrent Session:{session_memory.get_current_session_title()}"
)
print("Input \"/help\" to view available instructions")

while True:
    user_input = input(
        f"[{session_memory.get_current_session_title()}] You:"
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
        session_id = session_memory.create_session()
        print("\n已创建新对话")
        print(f"session id:{session_id}")
        continue

    if user_input == "/history":
        show_history()
        continue

    #查看长期记忆
    if user_input == "/memory":
        show_memory()
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
        success = session_memory.switch_session(
            session_id
        )

        if success:
            print(
                f"\n已切换到:"
                f"{session_memory.get_current_session_title()}"
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
        sessions = (session_memory.data["sessions"])
        # 找不到 Session
        if session_id not in sessions:
            print(
                "\n找不到这个 Session。"
            )
            continue

        target = sessions[session_id]

        # 二次确认
        confirm = input(
            f"\n确定删除「{target['title']}」吗？"
            "\n输入 y 确认："
        )

        if confirm.lower() == "y":
            session_memory.delete_session(
                session_id
            )
            print(
                "\nSession 已删除。"
            )
            print(
                f"当前会话："
                f"{session_memory.get_current_session_title()}"
            )
        else:
            print(
                "\n已取消删除。"
            )
        continue

    #删除长期记忆：
    if user_input.startswith("/forget"):
        parts = user_input.split()

        if len(parts) != 2:
            print(
                "\n用法: /forget <MemoryID>"
            )

            continue

        memory_id = parts[1]
        memories = (
            Long_term_memory.get_memories()
        )

        target = None

        for memory_item in memories:
            if memory_item["id"] == memory_id:
                target = memory_item
                break

        if target is None:
            print(
                "\n长期记忆不存在。"
            )
            continue

        confirm = input(
            "\n确定删除这条长期记忆吗?"
            f"\n「{target['content']}」"
            "\n输入 y 确认："
        )

        if confirm.lower() == "y":
            Long_term_memory.delete_memory(
                memory_id
            )
            print(
                "\n长期记忆已删除。"
            )

        else:
            print(
                "\n已取消。"
            )
        continue


    #获取当前Session历史
    history = session_memory.get_current_session_messages()

    #读取长期记忆
    memory_context =(build_memory_context())

    system_prompt =(SYSTEM_PROMPT + memory_context)

    #构造消息
    messages =[
        {"role":"system",
         "content": system_prompt 
        }
    ]

    messages.extend(history)
    messages.append({
        "role": "user",
        "content": user_input
    })

    # 调用 DeepSeek
    answer = ask_llm(messages)

    if answer is None:
        print("AI 服务不可用")
        continue
    
    print("\nAI assistant:")
    print(answer)

    # 保存当前 Session
    session_memory.add_message(
        "user",
        user_input
    )

    session_memory.add_message(
        "assistant",
        answer
    )

    # 提取 Long-term Memory
    extracted_memories = (
        LongTermMemory.extract_memories(
            user_input=user_input,
            existing_memories=(
                Long_term_memory.get_memories()
            )
        )
    )

    added_count = 0

    for extracted in extracted_memories:
        success = (
            Long_term_memory.add_memory(

                content=(
                    extracted["content"]
                ),

                category=(
                    extracted["category"]                  
                ),

                source_session_id=(
                    session_memory
                    .get_current_session_id()
                )
            )
        )

        if success:
            added_count += 1

    # 显示 Memory 反馈
    if added_count > 0:
        print(
            "\n[Memory] "
            f"新增 {added_count} 条长期记忆。"
        )

    # except Exception as e:
    #     print("\n调用模型失败:")
    #     print(e)
