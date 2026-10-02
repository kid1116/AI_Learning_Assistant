"""真实调用 DeepSeek 验证「模型是否会用工具」：能返回 tool_calls 才算通过。

默认跳过（联网/计费）。单独跑：
    python test/test_tool_call.py

注意：这个文件以前在 import 时就真的调了 API，现在改成只在一个测试函数里调用，
      所以跑整个测试套件时不会再偷偷消耗额度。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_all import skip

from llm import ask_llm
from tools.schemas import TOOLS_SCHEMA

SKIP_REASON = "会真实调用 DeepSeek API（联网/计费），需要时单独运行"


def _ask(question):
    return ask_llm(
        [{"role": "user", "content": question}],
        tools=TOOLS_SCHEMA
    )


@skip(SKIP_REASON)
def test_model_requests_calculator_tool():
    message = _ask("算一下 2**100")

    assert message is not None, "模型调用失败"
    assert message.tool_calls, f"模型没有请求调用工具：{message.content!r}"

    tool_call = message.tool_calls[0]

    assert tool_call.function.name == "calculator"
    assert "expression" in (tool_call.function.arguments or "")


@skip(SKIP_REASON)
def test_model_answers_directly_when_no_tool_needed():
    """闲聊类问题不该强行调工具。"""
    message = _ask("你好")

    assert message is not None, "模型调用失败"
    assert message.content, "模型没有返回文本"


def main():
    from run_all import run_module

    # 单独运行时强制执行，忽略 skip 标记
    forced = {}

    for name, value in dict(globals()).items():
        if name.startswith("test_"):
            value.__skip_reason__ = None
            forced[name] = value

    return run_module(__name__, forced)


if __name__ == "__main__":
    sys.exit(main())
