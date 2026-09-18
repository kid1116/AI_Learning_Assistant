import json
import uuid
from datetime import datetime
from pathlib import Path

# 当前项目目录
BASE_DIR = Path(__file__).parent

# 记忆文件
MEMORY_FILE = BASE_DIR / "data" / "memory.json"

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
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

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
            and current_session["title"] == "new session" 
        ):
            title = content.strip()[:20]  # 截取前20个字符作为标题
            current_session["title"] = title

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