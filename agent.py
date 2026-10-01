from llm import ask_llm
from executor import execute_tool
from tools.schemas import TOOLS_SCHEMA

# 单轮对话里最多允许几轮“调工具 -> 再问模型”，防止模型无限打转
MAX_STEPS = 5


def run_agent(messages):
    """ReAct 循环：调模型 -> 若要求调工具则执行并回填 -> 再调模型，
    直到模型不再要求调工具，返回最终文本。
    """
    for _ in range(MAX_STEPS):
        message = ask_llm(messages, tools=TOOLS_SCHEMA)

        if message is None:
            return None

        # assistant 消息（含 tool_calls）必须先进入消息列表，
        # 否则后面的 tool 消息找不到对应的 tool_call_id，协议会报错
        messages.append(
            message.model_dump(exclude_none=True)
        )

        if not message.tool_calls:
            return message.content

        # 一次可能要求并行调多个工具，逐个执行并回填
        for tool_call in message.tool_calls:
            result = execute_tool(tool_call)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

    return "（达到最大工具调用步数，已停止）"
