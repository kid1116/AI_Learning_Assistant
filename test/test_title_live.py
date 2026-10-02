"""真实调用 DeepSeek 验证会话标题的概括效果（默认跳过，因为会联网花钱）。

单独跑：
    python test/test_title_live.py

或者把 SKIP_REASON 改成 None 后跑整个测试套件。

安全说明：存储路径指向临时目录，不会改动项目里的 data/memory.json。
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_all import skip

import memory
from memory import SessionMemory

# 默认跳过；想真跑就把这里改成 None
SKIP_REASON = "会真实调用 DeepSeek API（联网/计费），需要时单独运行"

# (用户的话, 期望标题包含的关键词)
CASES = [
    ("请告诉我怎么读论文效率最高", "论文"),
    (
        "请记住我现在要做关于心脏仿真建模的srtp项目，需要长期跟进",
        "SRTP",
    ),
]


def _title_for(question):
    with tempfile.TemporaryDirectory() as tmp:
        memory.MEMORY_FILE = Path(tmp) / "memory.json"

        session = SessionMemory()
        session.add_message("user", question)

        return session.get_current_session_title()


@skip(SKIP_REASON)
def test_titles_are_concise_and_keep_keywords():
    for question, keyword in CASES:
        title = _title_for(question)

        print(f"  {question[:20]}... -> {title}")

        assert title, "标题不能为空"
        assert len(title) <= memory.MAX_TITLE_LENGTH, f"标题过长：{title}"
        # 概括后必须保留关键信息，而不是被截断丢掉
        assert keyword.lower() in title.lower(), (
            f"标题丢了关键信息「{keyword}」：{title}"
        )


def main():
    from run_all import run_module

    return run_module(__name__, dict(globals()))


if __name__ == "__main__":
    # 单独运行时强制执行，忽略 skip 标记
    function = test_titles_are_concise_and_keep_keywords
    function.__skip_reason__ = None

    sys.exit(run_module(__name__, {function.__name__: function}))
