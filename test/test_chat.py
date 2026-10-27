"""对话服务的成功、模型失败、磁盘失败和辅助记忆失败路径。"""
from chat import ChatService


class Sessions:
    def __init__(self):
        self.turns = []

    def get_current_session_messages(self):
        return []

    def get_current_session_id(self):
        return "session1"

    def add_turn(self, question, answer):
        self.turns.append((question, answer))


class Memories:
    def __init__(self):
        self.items = []

    def get_memories(self):
        return self.items

    def add_memory(self, **kwargs):
        self.items.append(kwargs)
        return True


def test_success_saves_turn_and_links_memory_to_session():
    sessions, memories = Sessions(), Memories()
    service = ChatService(sessions, memories, agent=lambda messages: "回答",
                          extractor=lambda **kwargs: [{"content": "学习 Agent", "category": "learning"}])
    result = service.reply("问题")
    assert sessions.turns == [("问题", "回答")]
    assert result.added_memories == 1 and not result.warnings
    assert memories.items[0]["source_session_id"] == "session1"


def test_model_failure_does_not_save_or_extract():
    sessions, memories = Sessions(), Memories()

    def unexpected(**kwargs):
        raise AssertionError("模型失败不应提取记忆")

    result = ChatService(sessions, memories, agent=lambda messages: None,
                         extractor=unexpected).reply("问题")
    assert result.answer is None
    assert not sessions.turns and not memories.items


def test_memory_failure_keeps_answer_and_saved_turn():
    sessions, memories = Sessions(), Memories()

    def failing_extractor(**kwargs):
        raise RuntimeError("提取失败")

    result = ChatService(sessions, memories, agent=lambda messages: "回答",
                         extractor=failing_extractor).reply("问题")
    assert result.answer == "回答" and sessions.turns
    assert "长期记忆更新失败" in result.warnings[0]


def test_save_failure_keeps_answer_and_skips_extraction():
    sessions, memories = Sessions(), Memories()

    def fail_save(*args):
        raise OSError("磁盘不可写")

    def unexpected(**kwargs):
        raise AssertionError("保存失败不应提取记忆")

    sessions.add_turn = fail_save
    result = ChatService(sessions, memories, agent=lambda messages: "回答",
                         extractor=unexpected).reply("问题")
    assert result.answer == "回答"
    assert "会话保存失败" in result.warnings[0]
    assert not memories.items
