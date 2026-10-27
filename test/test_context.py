"""验证上下文裁剪保留完整最近问答，且不改写原始历史。"""
from context import build_messages, build_memory_context, select_history
from config import MAX_USER_INPUT_CHARS


def test_recent_complete_turns_fit_budget():
    history = [
        {"role": "user", "content": "旧问题"},
        {"role": "assistant", "content": "旧回答"},
        {"role": "user", "content": "新问题"},
        {"role": "assistant", "content": "新回答"},
    ]
    selected = select_history(history, max_chars=6)
    assert selected == history[-2:]
    selected[0]["content"] = "修改副本"
    assert history[-2]["content"] == "新问题"


def test_orphan_messages_and_oversized_turn_are_not_sent():
    history = [
        {"role": "assistant", "content": "孤立回答"},
        {"role": "user", "content": "长问题"},
        {"role": "assistant", "content": "长" * 100},
        {"role": "user", "content": "未完成的问题"},
    ]
    assert select_history(history, max_chars=10) == []


def test_memory_budget_prefers_recent_whole_facts():
    memories = [
        {"content": "旧" * 100, "updated_at": "2025"},
        {"content": "用户学习 Agent", "updated_at": "2026"},
    ]
    context = build_memory_context(memories, max_chars=100)
    assert len(context) <= 100
    assert "用户学习 Agent" in context
    assert "旧" not in context
    assert build_memory_context(memories, max_chars=1) == ""


def test_current_question_is_preserved_in_full():
    text = "当前问题" * 100
    messages = build_messages(text, [], [])
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": text}


def test_oversized_input_is_rejected_without_silent_truncation():
    try:
        build_messages("字" * (MAX_USER_INPUT_CHARS + 1), [], [])
    except ValueError as error:
        assert "输入过长" in str(error)
    else:
        raise AssertionError("超长输入应被明确拒绝")
