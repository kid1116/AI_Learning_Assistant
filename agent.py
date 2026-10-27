from llm import ask_llm
from executor import execute_tool
from tools.schemas import TOOLS_SCHEMA
from config import MAX_AGENT_STEPS, MAX_TOOL_RESULT_CHARS

# 单轮对话里最多允许几轮“调工具 -> 再问模型”，防止模型无限打转
MAX_STEPS = MAX_AGENT_STEPS


def run_agent(messages):
    """ReAct 循环：调模型 -> 若要求调工具则执行并回填 -> 再调模型，
    直到模型不再要求调工具，返回最终文本。
    """
    messages = [dict(message) for message in messages]
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
                "content": _bounded_result(result)
            })

    # 工具预算耗尽后，再允许一次不带工具的总结请求。
    messages.append({
        "role": "system",
        "content": "工具调用预算已用完。请根据已有结果回答，明确未完成的部分，不要编造结果。"
    })
    final = ask_llm(messages)
    if final is not None and not final.tool_calls and final.content:
        return final.content
    return "（已达到工具调用上限，暂时无法完成回答。请缩小问题范围后重试。）"


def _bounded_result(result):
    text = str(result)
    marker = "\n[工具结果过长，已截断]"
    if len(text) > MAX_TOOL_RESULT_CHARS:
        return text[:MAX_TOOL_RESULT_CHARS - len(marker)] + marker
    return text
