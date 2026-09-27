from tools import TOOLS


tool_name = "calculator"

arguments = {
    "expression": "123 * 456",
}


tool = TOOLS[tool_name]

result = tool(**arguments) #相当于tool(expression="123 * 456")

print("工具执行结果：",result)