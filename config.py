import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY 未配置")

# 博查联网搜索的 Key。没配不报错，只让 web_search 工具返回提示，不影响其他功能
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")
