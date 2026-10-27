"""单轮对话服务，供 CLI 和未来的 Web/API 入口共用。"""

from dataclasses import dataclass, field

from agent import run_agent
from context import build_messages
from long_term_memory import LongTermMemory


@dataclass
class ChatResult:
    answer: str | None
    added_memories: int = 0
    warnings: list[str] = field(default_factory=list)


class ChatService:
    def __init__(self, session_memory, long_term_memory, agent=None, extractor=None):
        self.sessions = session_memory
        self.memories = long_term_memory
        self.agent = agent if agent is not None else run_agent
        self.extractor = extractor if extractor is not None else LongTermMemory.extract_memories

    def reply(self, user_input):
        messages = build_messages(
            user_input,
            self.sessions.get_current_session_messages(),
            self.memories.get_memories(),
        )
        answer = self.agent(messages)
        if not isinstance(answer, str) or not answer.strip():
            return ChatResult(None)
        result = ChatResult(answer)
        try:
            self.sessions.add_turn(user_input, answer)
        except Exception as error:
            result.warnings.append(f"回答已生成，但会话保存失败：{error}")
            return result

        # 辅助记忆失败不影响已完成的问答。
        try:
            extracted = self.extractor(
                user_input=user_input,
                existing_memories=self.memories.get_memories(),
            )
            for item in extracted:
                added = self.memories.add_memory(
                    content=item["content"], category=item["category"],
                    source_session_id=self.sessions.get_current_session_id(),
                )
                result.added_memories += int(added)
        except Exception as error:
            result.warnings.append(f"本轮长期记忆更新失败：{error}")
        return result
