from llm import ask_llm
from prompt import SYSTEM_PROMPT


messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


while True:

    user_input = input("\n你:")


    if user_input == "exit":
        break


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