from llm import ask_llm
from prompt import SYSTEM_PROMPT
from memory import load_memory, save_memory, clear_memory


history = load_memory()

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]
messages.extend(history)


while True:

    user_input = input("\n你:")

    if user_input == "exit":
        print("AI助手退出")
        break

    if user_input == "clear":
        clear_memory()
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        print("历史聊天记录已清空")
        continue

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    answer = ask_llm(messages)

    print("\nAI助手:")
    print(answer)

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    save_memory(messages[1:])  # 保存历史聊天记录