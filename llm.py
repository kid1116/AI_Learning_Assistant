from openai import OpenAI
from config import API_KEY

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)

def ask_llm(messages):

    try:
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"LLM调用失败:{e}")
        return None

    