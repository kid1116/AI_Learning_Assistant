import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")

MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 字符预算是工程限制，并非精确的 token 计数。
MAX_HISTORY_CHARS = 24000
MAX_MEMORY_CHARS = 4000
MAX_USER_INPUT_CHARS = 12000
MAX_TOOL_RESULT_CHARS = 3000
MAX_AGENT_STEPS = 5
LLM_TIMEOUT_SECONDS = 60

# 博查联网搜索的 Key。没配不报错，只让 web_search 工具返回提示，不影响其他功能
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")
