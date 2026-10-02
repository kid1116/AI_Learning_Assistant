import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from llm import ask_llm

# 获取当前项目目录
BASE_DIR = Path(__file__).parent

# 拼接完整目录
MEMORY_FILE = BASE_DIR / "data" / "memory.json"

# 会话标题的长度上限，防止模型不听话时把标题写太长
MAX_TITLE_LENGTH = 24


# 清洗模型生成的标题：去掉换行和首尾引号，并限制长度
def clean_title(text):
    title = " ".join((text or "").split()).strip()

    # 模型偶尔会用引号或书名号把标题包起来
    title = title.strip('"\'“”‘’《》【】[]')

    return title[:MAX_TITLE_LENGTH].strip()


# 让模型把用户的第一句话概括成简短标题
# 调用失败或结果为空时返回 None，由调用方回退到截断文案
def generate_title(user_input):
    prompt = (
        "请把下面这句话概括成一个简短的中文标题，用来标识一段对话。\n\n"
        "要求：\n"
        "1. 不超过 20 个字\n"
        "2. 直接输出标题本身，不要引号、不要句号、不要任何解释\n"
        "3. 保留关键的专有名词(比如 Agent、RAG、Transformer)\n\n"
        f"用户的话：{user_input}"
    )

    messages = [
        {
            "role": "system",
            "content": "你负责为对话生成简短标题，只输出标题本身。"
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = ask_llm(messages)

    # ask_llm 返回的是 message 对象，调用失败时返回 None
    if response is None:
        return None

    title = clean_title(response.content)

    return title or None


#session memory
class SessionMemory:
    def __init__(self):
        self.data = self.load()

        if not self.data["sessions"]:
            self.create_session()
        else:
            current_id = self.data.get("current_session_id")

            if current_id not in self.data["sessions"]:
                latest_session =max(
                    self.data["sessions"].values(),
                    key=lambda session: session["created_at"]
                )

                self.data["current_session_id"] = latest_session["id"]
                self.save()

    #获取当前时间
    def now(self):
        return datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

    #加载"memory.json"文件
    def load(self):
        if not MEMORY_FILE.exists():
            return {
                "current_session_id": None,
                "sessions": {}
            }

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    #保存"memory.json"文件
    def save(self):
        # 先写临时文件再原子替换，避免写入中途出错留下残缺的 JSON
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=MEMORY_FILE.parent, suffix=".tmp"
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

            os.replace(tmp_path, MEMORY_FILE)

        except BaseException:
            os.unlink(tmp_path)
            raise

    #创建新的会话
    def create_session(self,title="New Session"):
        session_id =(
            datetime.now().strftime("%Y%m%d_%H%M%S") 
            + "_" 
            + uuid.uuid4().hex[:6]   
        )

        current_time = self.now()

        self.data["sessions"][session_id] = {
            "id": session_id,
            "title": title,
            "created_at": current_time,
            "updated_at": current_time,
            "messages": []
        }

        self.data["current_session_id"] = session_id

        self.save()

        return session_id

    #获取当前会话
    def get_current_session(self):
        current_id = self.data.get("current_session_id")
        return self.data["sessions"].get(current_id)

    #获取当前session id
    def get_current_session_id(self):
        return self.data.get("current_session_id")

    #获取当前session标题
    def get_current_session_title(self):
        current_session = self.get_current_session()
        return current_session.get("title") if current_session else None

    #获取当前session消息
    def get_current_session_messages(self):
        current_session = self.get_current_session()
        return current_session.get("messages") if current_session else []

    #添加消息
    def add_message(self, role, content):
        current_session = self.get_current_session()

        current_session["messages"].append(
            {"role": role, "content": content}
            )

        current_session["updated_at"] = self.now()

        #用户的第一条消息作为session标题
        if(
            role == "user" 
            and current_session["title"] == "New Session" 
        ):
            #优先让模型概括，失败或超时则回退到截取前20个字符
            text = (content or "").strip()

            title = ""

            if text:
                #这里再清洗一次：无论模型层返回什么，进入存储前都保证是干净且不超长的标题
                title = clean_title(generate_title(text))

            current_session["title"] = title or text[:20]

        self.save()

    #切换session
    def switch_session(self, session_id):
        if session_id in self.data["sessions"]:
            self.data["current_session_id"] = session_id
            self.save()
            return True
        return False

    #获取所有session
    def list_sessions(self):
        sessions = list(
            self.data["sessions"].values()
        )

        sessions.sort(
            key = lambda session: session["updated_at"],
            reverse=True
        )

        return sessions

    #删除指定session
    def delete_session(self, session_id):

        if session_id not in self.data["sessions"]:
            return False

        del self.data["sessions"][session_id]

        # 如果删除的是当前 Session
        if self.data["current_session_id"] == session_id:

            # 还有其他 Session
            if self.data["sessions"]:
                latest_session = max(
                    self.data["sessions"].values(),
                    key=lambda session: session["updated_at"]
                )

                self.data["current_session_id"] = (
                    latest_session["id"]
                )

            # 一个 Session 都没有了
            else:

                self.data["current_session_id"] = None
                self.save()

                # 自动创建一个新 Session
                self.create_session()
                return True

        self.save()

        return True