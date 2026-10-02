"""验证会话标题：首条消息由 AI 概括，失败时回退到截断，且只生效一次。

安全说明：所有用例都把 memory.MEMORY_FILE 指向临时目录，
        绝对不会动到项目里的 data/memory.json。
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory
from memory import SessionMemory, clean_title

LONG_INPUT = "请记住我现在要做关于心脏仿真建模的srtp项目并且需要长期follow"


def _new_memory(tmp_dir, fake_reply):
    """把存储路径指到临时目录，把模型返回换成固定值，返回 SessionMemory。"""
    memory.MEMORY_FILE = Path(tmp_dir) / "memory.json"
    memory.generate_title = lambda user_input: fake_reply

    return SessionMemory()


# --- 纯函数：clean_title ---

def test_clean_title_strips_quotes():
    assert clean_title('"Agent 学习路线"') == "Agent 学习路线"
    assert clean_title("《ReAct 论文笔记》") == "ReAct 论文笔记"
    assert clean_title("【心脏仿真】") == "心脏仿真"
    assert clean_title("'引号'") == "引号"


def test_clean_title_normalizes_whitespace():
    assert clean_title("Agent\n学习\n路线") == "Agent 学习 路线"
    assert clean_title("  两边有空格  ") == "两边有空格"
    assert clean_title("带\t制表符") == "带 制表符"


def test_clean_title_limits_length():
    assert clean_title("字" * 50) == "字" * memory.MAX_TITLE_LENGTH
    assert len(clean_title("字" * 50)) == memory.MAX_TITLE_LENGTH


def test_clean_title_handles_empty():
    assert clean_title("") == ""
    assert clean_title(None) == ""
    assert clean_title("   ") == ""


# --- 标题生成流程 ---

def test_first_message_uses_model_title():
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, "Agent 学习路线规划")
        session.add_message("user", "帮我规划一下接下来三个月怎么学 Agent")

        assert session.get_current_session_title() == "Agent 学习路线规划"


def test_dirty_model_reply_is_cleaned_before_saving():
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, '  "《心脏仿真建模 SRTP 项目长期跟进与推演》" \n')
        session.add_message("user", LONG_INPUT)

        title = session.get_current_session_title()

        # 引号、书名号、换行都要被清掉，且不能超长
        assert title == "心脏仿真建模 SRTP 项目长期跟进与推演"[:memory.MAX_TITLE_LENGTH]
        assert "\n" not in title
        assert '"' not in title
        assert "《" not in title


def test_none_reply_falls_back_to_truncation():
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, None)
        session.add_message("user", LONG_INPUT)

        assert session.get_current_session_title() == LONG_INPUT[:20]


def test_empty_reply_falls_back_to_truncation():
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, "")
        session.add_message("user", LONG_INPUT)

        assert session.get_current_session_title() == LONG_INPUT[:20]


def test_dirty_reply_that_cleans_to_empty_falls_back():
    """模型只返回一堆引号时，清洗后为空，也必须回退。"""
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, '  ""  ')
        session.add_message("user", LONG_INPUT)

        assert session.get_current_session_title() == LONG_INPUT[:20]


def test_title_is_only_generated_once():
    with tempfile.TemporaryDirectory() as tmp:
        session = _new_memory(tmp, "AI 概括标题")
        session.add_message("user", "第一个问题：什么是 ReAct")
        first_title = session.get_current_session_title()

        # 之后即使模型能返回别的标题，也不该再改
        memory.generate_title = lambda user_input: "不该出现的标题"

        session.add_message("user", "第二个问题：什么是 Reflexion")
        assert session.get_current_session_title() == first_title

        session.add_message("assistant", "assistant 的回复")
        assert session.get_current_session_title() == first_title


def test_generate_title_is_not_called_after_first_message():
    """用调用计数确认：只有首条消息会触发模型调用。"""
    with tempfile.TemporaryDirectory() as tmp:
        memory.MEMORY_FILE = Path(tmp) / "memory.json"

        calls = []

        def counting_generate(user_input):
            calls.append(user_input)
            return "标题"

        memory.generate_title = counting_generate
        session = SessionMemory()

        session.add_message("user", "第一条")
        session.add_message("user", "第二条")
        session.add_message("assistant", "回复")

        assert calls == ["第一条"]


def test_blank_input_falls_back_without_calling_model():
    with tempfile.TemporaryDirectory() as tmp:
        calls = []

        memory.MEMORY_FILE = Path(tmp) / "memory.json"
        memory.generate_title = lambda user_input: calls.append(user_input) or "标题"

        session = SessionMemory()
        session.add_message("user", "   ")

        # 空白输入不该调用模型（省一次调用），标题回退为空串
        assert calls == []
        assert session.get_current_session_title() == ""


def test_existing_session_keeps_its_title():
    with tempfile.TemporaryDirectory() as tmp:
        memory_file = Path(tmp) / "memory.json"
        memory_file.write_text(
            json.dumps(
                {
                    "current_session_id": "s1",
                    "sessions": {
                        "s1": {
                            "id": "s1",
                            "title": "已有标题",
                            "created_at": "2026-01-01T00:00:00+08:00",
                            "updated_at": "2026-01-01T00:00:00+08:00",
                            "messages": [],
                        }
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        memory.MEMORY_FILE = memory_file
        memory.generate_title = lambda user_input: "不该出现的标题"

        session = SessionMemory()

        assert session.get_current_session_title() == "已有标题"


def main():
    from run_all import run_module

    return run_module(__name__, dict(globals()))


if __name__ == "__main__":
    sys.exit(main())
