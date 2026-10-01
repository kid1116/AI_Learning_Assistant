import json
from tools import TOOLS

#实际调用对应的tool
def execute_tool(tool_call):
    tool_name = tool_call.function.name

    tool_function = TOOLS.get(tool_name)
    if tool_function is None:
        return f"工具 {tool_name} 不存在"

    # 参数由模型生成，可能是空串或非法 JSON，解析失败要把原因回传给模型
    try:
        arguments = json.loads(
            tool_call.function.arguments or "{}"
        )

    except json.JSONDecodeError:
        return (
            "参数解析失败："
            f"{tool_call.function.arguments}"
        )

    # 工具自身报错也转成文本，让模型读到原因后能换个方式重试
    try:
        return tool_function(**arguments)

    except Exception as e:
        return f"工具执行出错：{e}"
