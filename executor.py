import json
from tools import TOOLS

#实际调用对应的tool
def execute_tool(tool_call):
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    tool_function = TOOLS.get(tool_name)
    if tool_function is None:
        return f"工具{tool_name}不存在"

    result = tool_function(**arguments)

    return result