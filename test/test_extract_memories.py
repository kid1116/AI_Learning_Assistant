"""验证 extract_memories 的 JSON 解析兜底：不联网，直接把 ask_llm 换成假回复。

覆盖的模型回复形态：
  1. 干净的 JSON 数组
  2. 外包 ```json 代码块
  3. 前面带一句解释（不是合法 JSON）
  4. 完全不是 JSON
  5. 返回对象而不是数组
  6. content 为 None
  7. ask_llm 调用失败（返回 None）
  8. 数组里有非法项（缺 content、category 越界、非 dict）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import long_term_memory
from long_term_memory import LongTermMemory


class FakeMessage:
    def __init__(self, content):
        self.content = content


# (说明, 假的模型回复, 期望结果)
CASES = [
    (
        "干净的 JSON 数组",
        '[{"content": "用户在学习 Agent", "category": "learning"}]',
        [{"content": "用户在学习 Agent", "category": "learning"}],
    ),
    (
        "外包 ```json 代码块",
        '```json\n[{"content": "用户喜欢数学推导", "category": "preference"}]\n```',
        [{"content": "用户喜欢数学推导", "category": "preference"}],
    ),
    (
        "前面带一句解释",
        '好的，我分析了这轮输入：\n[{"content": "用户在读 ReAct 论文", "category": "learning"}]\n以上。',
        [{"content": "用户在读 ReAct 论文", "category": "learning"}],
    ),
    (
        "完全不是 JSON",
        "这轮输入没有值得长期保存的信息。",
        [],
    ),
    (
        "只有空数组",
        "[]",
        [],
    ),
    (
        "返回对象而不是数组",
        '{"content": "用户在学习 Agent", "category": "learning"}',
        [],
    ),
    (
        "content 为 None",
        None,
        [],
    ),
    (
        "数组里有非法项",
        '[{"content": "  合法项  ", "category": "不存在的分类"},'
        ' {"category": "learning"}, {"content": ""}, "我是个字符串", 42]',
        [{"content": "合法项", "category": "other"}],
    ),
]


def _extract_with(fake_reply):
    """把 ask_llm 替换成固定回复，然后调用 extract_memories。"""
    long_term_memory.ask_llm = (
        lambda messages, _content=fake_reply: FakeMessage(_content)
    )

    return LongTermMemory.extract_memories(
        user_input="测试输入",
        existing_memories=[]
    )


def test_reply_variants_never_crash():
    """任何形态的模型回复都不能让程序崩，且结果必须是合法列表。"""
    for name, fake_reply, expected in CASES:
        actual = _extract_with(fake_reply)

        assert actual == expected, (
            f"{name}: 期望 {expected!r}，实际 {actual!r}"
        )


def test_llm_failure_returns_empty():
    """ask_llm 调用失败时返回 None，此时应该当作没有记忆。"""
    long_term_memory.ask_llm = lambda messages: None

    assert LongTermMemory.extract_memories(
        user_input="测试输入",
        existing_memories=[]
    ) == []


def test_content_none_is_handled():
    """只返回工具调用时 content 可能是 None，不能抛 AttributeError。"""
    actual = _extract_with(None)

    assert actual == []


def test_json_array_is_extracted_from_prose():
    """回复外面裹了人话时，要能把数组救回来。"""
    actual = _extract_with(
        '我先说明一下：\n[{"content": "用户在做 SRTP 项目", "category": "project"}]\n以上是我的判断。'
    )

    assert actual == [{"content": "用户在做 SRTP 项目", "category": "project"}]


def test_invalid_items_are_dropped():
    actual = _extract_with(
        '[{"content": "  保留我  ", "category": "learning"},'
        ' {"content": "分类越界", "category": "海豚"},'
        ' {"category": "learning"}, {"content": "   "}, 42, "字符串", null]'
    )

    assert actual == [
        {"content": "保留我", "category": "learning"},
        {"content": "分类越界", "category": "other"},
    ]


def main():
    from run_all import run_module

    return run_module(__name__, dict(globals()))


if __name__ == "__main__":
    sys.exit(main())
