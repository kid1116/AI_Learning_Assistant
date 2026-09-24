import json
import uuid
from datetime import datetime
from pathlib import Path

from llm import ask_llm

BASE_DIR = Path(__file__).parent

LONG_TERM_MEMORY_FILE = BASE_DIR / "data" / "long_term_memory.json"

#extract_memories 允许的记忆分类，与提示词里的 category 说明保持一致
ALLOWED_CATEGORIES = {
    "profile",
    "goal",
    "learning",
    "project",
    "preference",
    "other"
}

#去掉模型偶尔包裹在 JSON 外面的 ``` / ```json 代码块
def strip_code_fence(text):
    #没有代码块就直接返回
    if not text.startswith("```"):
        return text

    lines = text.splitlines()

    #丢掉第一行（``` 或 ```json）
    if lines:
        lines = lines[1:]

    #丢掉结尾的 ```
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines)


class LongTermMemory:
    def __init__(self):
        self.data = self.load()

    #获取当前时间
    def now(self):
        return datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

    #加载长期记忆
    def load(self):
        #文件还不存在时，返回一个空的记忆结构
        if not LONG_TERM_MEMORY_FILE.exists():
            return {"memories": []}

        with open(
            LONG_TERM_MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        #文件里不是预期的字典结构时，同样当作空记忆处理
        if not isinstance(data, dict):
            return {"memories": []}

        if "memories" not in data:
            data["memories"] = []

        return data

    #保存长期记忆文件
    def save(self):
        #确保 data 目录存在
        LONG_TERM_MEMORY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            LONG_TERM_MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=4
            )

    #获取所有长期记忆
    def get_memories(self):
        return self.data["memories"]

    #添加记忆
    def add_memory(self, content, category="other", source_session_id=None):
        content = content.strip()

        #内容为空时不保存
        if not content:
            return False

        #防止重复：内容相同就只刷新更新时间，不新增
        normalized = content.lower()
        for memory in self.data["memories"]:
            if memory["content"].strip().lower() == normalized:
                memory["updated_at"] = self.now()

                self.save()

                return False

        memory = {
            "id": uuid.uuid4().hex[:8],
            "content": content,
            "category": category,
            "created_at": self.now(),
            "updated_at": self.now(),
            "source_session_id": source_session_id
        }

        self.data["memories"].append(memory)

        self.save()

        return True

    #删除记忆
    def delete_memory(self, memory_id):
        for memory in self.data["memories"]:
            if memory["id"] == memory_id:
                self.data["memories"].remove(memory)

                self.save()

                return True

        return False

    #利用AI自动提取长期记忆
    #返回 [{"content": ..., "category": ...}, ...]；没有可保存的信息时返回 []
    @staticmethod
    def extract_memories(user_input,existing_memories):
        #把已有记忆序列化成文本
        existing_memory_text = json.dumps(
            existing_memories,
            ensure_ascii=False,
            indent=2
        )

        #提取规则
        prompt = f"""
你是一个个人AI学习助手的长期记忆提取器。

你的任务：
判断用户本轮输入中，是否存在值得长期保存的信息。

允许保存：
1. 用户身份
2. 用户长期学习方向
3. 用户长期学习目标
4. 用户正在进行的长期项目
5. 用户长期偏好
6. 其他未来多次对话有帮助的信息

不要保存：
1. 一次性的普通问题
2. 临时聊天内容
3. AI自己的推测
4. 没有被用户明确表达的信息
5. API Key、密码、Token等凭证
6. 没有长期价值的技术细节

非常重要：
只能根据用户明确表达的内容判断。
不能根据用户的问题推测用户的身份、目标或偏好。

已有长期记忆：
{existing_memory_text}

用户本轮输入：
{user_input}

请严格返回 JSON 数组：
[
    {{
        "content": "值得长期保存的信息",
        "category": "learning"
    }}
]

category 必须是以下之一：
profile
goal
learning
project
preference
other

如果没有任何值得长期保存的信息：
[]

只能输出 JSON,不要输出其他内容。
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "你负责提取用户的长期记忆。"
                    "不要进行普通聊天。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = ask_llm(messages)

        #去掉首尾空白，并剥掉模型可能加上的 ``` 代码块
        response = response.strip()
        response = strip_code_fence(response)

        result = json.loads(response)

        if not isinstance(result, list):
            return []

        #逐条校验模型返回的数据，丢弃不合法的项
        valid_memories = []

        for item in result:
            if not isinstance(item, dict):
                continue

            content = item.get("content", "")
            category = item.get("category", "other")

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            #category 不在允许范围内时，统一回退为 other
            if category not in ALLOWED_CATEGORIES:
                category = "other"

            valid_memories.append({
                "content": content,
                "category": category
            })

        return valid_memories
