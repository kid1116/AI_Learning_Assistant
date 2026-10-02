"""极简测试运行器：不依赖 pytest，任何 Python 环境都能跑。

用法：
    python test/run_all.py            # 跑 test/ 下所有 test_*.py
    python test/test_calculator.py    # 也可以单独跑某个文件

约定：
    - 文件名 test_*.py
    - 函数名 test_*，没有参数
    - 用 assert 断言；也可以继续用 print 输出中间信息
    - 需要标记为「人工/联网」的测试，用 @skip 装饰器
"""

import importlib
import pathlib
import sys
import traceback

TEST_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent

# 让测试文件能 import 项目根目录的模块
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def skip(reason):
    """标记一个默认跳过的测试（例如会联网、会花钱的测试）。"""
    def decorator(function):
        function.__skip_reason__ = reason
        return function

    return decorator


def collect(namespace):
    """按定义顺序收集 test_* 函数。"""
    return [
        (name, value)
        for name, value in namespace.items()
        if name.startswith("test_") and callable(value)
    ]


def run_module(name, namespace, verbose=True):
    """执行一个测试模块里的全部 test_* 函数，返回失败数量。"""
    tests = collect(namespace)

    if not tests:
        print("没有找到 test_* 函数")
        return 0

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_function in tests:
        reason = getattr(test_function, "__skip_reason__", None)

        if reason:
            skipped += 1
            print(f"[SKIP] {test_name} —— {reason}")
            continue

        try:
            test_function()

        except Exception:
            failed += 1
            print(f"[FAIL] {test_name}")
            traceback.print_exc()

        else:
            passed += 1
            print(f"[ OK ] {test_name}")

    print()
    print(f"{name}: 通过 {passed}，失败 {failed}，跳过 {skipped}")

    return failed


def main():
    files = sorted(TEST_DIR.glob("test_*.py"))

    if not files:
        print("test/ 目录下没有 test_*.py")
        return 1

    total_failed = 0

    for path in files:
        print("=" * 62)
        print(f"运行 {path.name}")
        print("=" * 62)

        module = importlib.import_module(path.stem)
        total_failed += run_module(path.name, vars(module))

        print()

    print("=" * 62)

    if total_failed:
        print(f"总计 {total_failed} 个测试失败")
        return 1

    print("全部测试通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
