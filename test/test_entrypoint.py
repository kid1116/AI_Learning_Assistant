"""入口导入无副作用、无密钥可用离线模块，以及问答落盘的完整性。"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import memory
from memory import SessionMemory


def test_import_main_needs_no_key_input_or_memory_initialization():
    code = (
        "from unittest.mock import patch; "
        "import llm; "
        "assert not llm.API_KEY; "
        "guard = lambda *a, **k: (_ for _ in ()).throw(AssertionError('side effect')); "
        "p = patch('memory.SessionMemory.__init__', guard); p.start(); "
        "q = patch('builtins.input', guard); q.start(); "
        "import main; assert callable(main.main)"
    )
    env = {**os.environ, "DEEPSEEK_API_KEY": ""}
    result = subprocess.run([sys.executable, "-c", code], env=env,
                            cwd=Path(__file__).resolve().parent.parent,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_add_turn_saves_both_messages_once_and_restores_on_failure():
    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(memory, "MEMORY_FILE", Path(tmp) / "memory.json"), \
         patch.object(memory, "generate_title", return_value="新标题"):
        sessions = SessionMemory()
        with patch.object(sessions, "save", wraps=sessions.save) as save:
            sessions.add_turn("问题", "回答")
            assert save.call_count == 1
        assert sessions.get_current_session_title() == "新标题"
        assert len(SessionMemory().get_current_session_messages()) == 2
        with patch.object(sessions, "save", side_effect=OSError("不可写")):
            try:
                sessions.add_turn("第二问", "第二答")
            except OSError:
                pass
            else:
                raise AssertionError("应向调用方报告保存失败")
        assert len(sessions.get_current_session_messages()) == 2


def test_command_requires_exact_name_and_expected_arguments():
    from main import handle_command
    with patch("builtins.print") as output:
        assert handle_command("/switchxxx s1", None, None)
        assert "未知命令" in output.call_args.args[0]
        assert handle_command("/exit extra", None, None)
        assert "用法" in output.call_args.args[0]
        assert handle_command("/exit", None, None) is False
