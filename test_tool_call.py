from llm import ask_llm
from tools.schemas import TOOLS_SCHEMA


messages = [
    {"role":"user",
     "content":"算一下123*456"
    }
]

response = ask_llm(
    messages,
    tools = TOOLS_SCHEMA
)

print(response)