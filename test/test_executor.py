"""验证 executor 的工具分发逻辑：不联网、不调用模型。

覆盖：
  1. 正常工具调用
  2. 不存在的工具名
  3. 参数不是合法 JSON
  4. 工具内部报错
  5. 参数缺失或为空（模型偶尔会漏）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from executor import execute_tool


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, name, arguments):
        self.function = FakeFunction(name, arguments)


def test_calculator_tool_is_dispatched():
    result = execute_tool(FakeToolCall("calculator", '{"expression": "2**10"}'))

    assert result == 1024


def test_unknown_tool_returns_message():
    result = execute_tool(FakeToolCall("不存在的工具", "{}"))

    assert "不存在" in result
    assert "不存在的工具" in result


def test_broken_json_is_reported_to_model():
    result = execute_tool(FakeToolCall("calculator", '{"expression": '))

    assert result.startswith("参数解析失败")
    # 要带上原始参数，模型才能看出自己错在哪
    assert '{"expression": ' in result


def test_tool_error_is_returned_as_text():
    """工具抛异常时要转成文本，不能中断对话循环。"""
    import executor

    def exploding_tool(**kwargs):
        raise RuntimeError("工具内部炸了")

    executor.TOOLS["exploding"] = exploding_tool

    try:
        result = execute_tool(FakeToolCall("exploding", "{}"))

        assert isinstance(result, str)
        assert result.startswith("工具执行出错")
        assert "工具内部炸了" in result

    finally:
        executor.TOOLS.pop("exploding", None)


def test_missing_required_argument_is_reported():
    """模型漏参数时应该回传错误文本，而不是抛 TypeError。"""
    result = execute_tool(FakeToolCall("calculator", "{}"))

    assert result.startswith("工具执行出错")


def test_empty_arguments_are_treated_as_empty_object():
    """arguments 可能为空串，按 {} 处理。"""
    result = execute_tool(FakeToolCall("calculator", ""))

    assert result.startswith("工具执行出错")


def main():
    from run_all import run_module

    return run_module(__name__, dict(globals()))


if __name__ == "__main__":
    sys.exit(main())
