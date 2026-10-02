"""让 test/ 目录下的测试无论在哪个工作目录运行都能 import 到项目模块。

当前项目没装 pytest，用 test/run_all.py 跑；将来装了 pytest，直接跑
    python -m pytest test
也能用，测试文件本身不需要改动。
"""

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
