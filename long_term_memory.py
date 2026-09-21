import json
import uuid
from datetime import datetime
from pathlib import Path

from llm import ask_llm

BASE_DIR = Path(__file__).parent

LONG_TERM_MEMORY_FILE = (BASE_DIR/"data"/"long_term_memory.json")

class LongTermMemory:
    def __init__(self):
        self.data = self.load()

    def now(self):
        return datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

    #加载长期记忆
    def load(self):
        if not LONG_TERM_MEMORY_FILE.exists():
            return {
                "memories":[]
            }

        with open(
            LONG_TERM_MEMORY_FILE,
            "r",
            encoding = "utf-8"
        )as f:
            data = json.load(f)

        if not isinstance(data, dict):
                return {"memories": []}

        if "memories" not in data:
                data["memories"] = []

        return data

    def save(self):
         LONG_TERM_MEMORY_FILE.parent.mkdir(
              parents=True,
              exist_ok=True
         )

         with open(
            LONG_TERM_MEMORY_FILE,
            "W",
            encoding="utf-8"
         ) as f:
              json.dump(
                   self.data,
                   f,
                   ensure_ascii=False,
                   indent = 4
              )

    #获取所有长期记忆
    def get_memories(self):
         return self.data["memories"]

    #添加记忆
    def add_memory(self,content,category="other",source_session_id=None):
        content=content.strip()

        if not content:
            return False

         #防止重复：
        normalized = content.lower()
        for memory in self.data["memories"]:
            if(
                memory["content"].strip().lower() == normalized
            ):
                memory["updated_at"] = self.now()

                self.save()

                return False
            
        memory = {
             "id": uuid.uuid4().hex[:8],
             "content": content,
             "category": category,
             "created_at": self.now(),
             "updated_at": self.now(),
             "source_session_id": (source_session_id)
            }

        self.data["memories"].append(memory)

        self.save

        return True

    #删除记忆
    def delete_memory(self,memory_id):
        for memory in self.data["memories"]:
            if memory["id"] == memory_id:
                self.data["memories"].remove(memory)

                self.save()

                return True

        return False

    #利用AI自动提取长期记忆
    def extract_memories(user_input,existing_memories):
        existing_memory_text = json.dumps(
            existing_memories,
            ensure_ascii=False,
            indent = 2
        )

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
        response.strip()

        if response.startswith("```"):
            lines = response.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

        response = "\n".join(lines)

        result = json.loads(response)

        if not isinstance(result, list):
            return []

        # 验证数据
        valid_memories = []

        allowed_categories = {

            "profile",
            "goal",
            "learning",
            "project",
            "preference",
            "other"
        }

        for item in result:
            if not isinstance(item, dict):
                continue

            content = item.get(
                "content",
                ""
            )

            category = item.get(
                "category",
                "other"
            )

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            if category not in allowed_categories:
                category = "other"

            valid_memories.append({
                "content": content,
                "category": category
            })

        return valid_memories
