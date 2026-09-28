from executor import execute_tool

class FakeFunction:
    name = "calculator"
    arguments ='{"expression":"111*222"}'

class FakeToolCall:
    function=FakeFunction()

result = execute_tool(
    FakeToolCall()
)


print(result)