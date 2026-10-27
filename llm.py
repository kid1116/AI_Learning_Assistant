from functools import lru_cache
from config import API_KEY, BASE_URL, MODEL_NAME, LLM_TIMEOUT_SECONDS

@lru_cache(maxsize=1)
def get_client():
    """只在请求模型时初始化，离线功能和导入不要求密钥。"""
    if not API_KEY:
        raise ValueError("DEEPSEEK_API_KEY 未配置，请检查项目目录下的 .env")
    from openai import OpenAI
    return OpenAI(
        api_key=API_KEY, base_url=BASE_URL,
        timeout=LLM_TIMEOUT_SECONDS, max_retries=1,
    )

def ask_llm(messages,tools=None):
    try:
        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools
        )

        return response.choices[0].message #返回整个message对象

    except Exception as e:
        print(f"LLM调用失败:{e}")
        return None

