"""使用模拟模型验证工具协议和循环停止条件，不联网。"""
from types import SimpleNamespace
from unittest.mock import patch

import agent


class Message:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def model_dump(self, **kwargs):
        data = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [
                {"id": call.id, "type": "function",
                 "function": {"name": "calculator", "arguments": "{}"}}
                for call in self.tool_calls
            ]
        return data


def test_tools_are_paired_and_caller_history_is_unchanged():
    calls = [SimpleNamespace(id="a"), SimpleNamespace(id="b")]
    messages = [{"role": "user", "content": "计算"}]

    def fake_llm(current, tools=None):
        if len(current) == 1:
            return Message(tool_calls=calls)
        assert current[1]["role"] == "assistant"
        assert [item["tool_call_id"] for item in current[2:]] == ["a", "b"]
        return Message("计算结果")

    with patch.object(agent, "ask_llm", side_effect=fake_llm), \
         patch.object(agent, "execute_tool", return_value="2"):
        assert agent.run_agent(messages) == "计算结果"
    assert messages == [{"role": "user", "content": "计算"}]


def test_exhausted_tool_budget_gets_one_tool_free_summary():
    seen = []

    def fake_llm(messages, tools=None):
        seen.append(tools)
        return Message(tool_calls=[SimpleNamespace(id="a")]) if tools else Message("已有结果和未完成部分")

    with patch.object(agent, "MAX_STEPS", 2), \
         patch.object(agent, "ask_llm", side_effect=fake_llm), \
         patch.object(agent, "execute_tool", return_value="结果"):
        assert agent.run_agent([]) == "已有结果和未完成部分"
    assert len(seen) == 3 and seen[-1] is None


def test_model_failure_does_not_modify_input():
    messages = [{"role": "user", "content": "问题"}]
    with patch.object(agent, "ask_llm", return_value=None):
        assert agent.run_agent(messages) is None
    assert len(messages) == 1


def test_tool_result_has_explicit_truncation_marker():
    result = agent._bounded_result("字" * 10000)
    assert len(result) <= agent.MAX_TOOL_RESULT_CHARS
    assert "已截断" in result
