"""验证安全计算器：正常表达式要算对，危险表达式要被拒绝。

重点：模型生成的参数是不受信任的输入，这里逐条验证它不能突破白名单。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.calculator import calculator


# --- 正常计算 ---

def test_basic_arithmetic():
    assert calculator("123*456") == 56088
    assert calculator("1+2") == 3
    assert calculator("10-4") == 6
    assert calculator("7/2") == 3.5
    assert calculator("7//2") == 3
    assert calculator("7%3") == 1
    assert calculator("2**10") == 1024
    assert calculator("111/0") == "计算失败：division by zero"


def test_parentheses_and_priority():
    assert calculator("(1+2)*3") == 9
    assert calculator("2+3*4") == 14
    assert calculator("-5+3") == -2
    assert calculator("+5") == 5
    assert calculator("-(2**3)") == -8


def test_big_integers():
    # 这是这个工具存在的意义：大数运算比模型心算可靠
    assert calculator("2**100") == 1267650600228229401496703205376
    assert calculator("99999*99999") == 9999800001


def test_whitelisted_functions():
    assert calculator("abs(-7)") == 7
    assert calculator("round(3.14159, 2)") == 3.14
    assert calculator("min(3, 1, 2)") == 1
    assert calculator("max(3, 1, 2)") == 3
    assert calculator("pow(2, 8)") == 256
    assert calculator("sqrt(16)") == 4


def test_input_edges():
    assert calculator("  42  ") == 42
    assert calculator("") == "计算失败：表达式为空"
    assert calculator("   ") == "计算失败：表达式为空"
    assert calculator(None) == "计算失败：表达式必须是字符串"
    assert calculator(123) == "计算失败：表达式必须是字符串"
    # 语法错误要给出提示而不是抛异常
    assert calculator("1+").startswith("计算失败：")
    assert calculator("(1+2").startswith("计算失败：")


# --- 安全：这些都必须被拒绝 ---

# 每条都是「如果真的执行了会出事」的表达式
DANGEROUS = [
    '__import__("os").system("echo hacked")',
    '__import__("os").remove("important.txt")',
    'open("data/memory.json", "w").write("x")',
    'open("secret.txt").read()',
    'eval("1+1")',
    'exec("print(1)")',
    'compile("1","<s>","eval")',
    'globals()',
    'locals()',
    'vars()',
    'dir()',
    'getattr(object, "__class__")',
    '(1).__class__',
    '().__class__.__bases__',
    'lambda: 1',
    '[x for x in range(3)]',
    '{1: 2}',
    '[1, 2, 3]',
    '(1, 2)',
    'x',
    'x := 1',
    '1 if True else 2',
    'print(1)',
    '"abc"',
    '"a" * 3',
    'True',
    'None',
    'f"{1+1}"',
    'os.system("echo x")',
    'int("1")',
]


def test_dangerous_expressions_are_rejected():
    for expression in DANGEROUS:
        result = calculator(expression)

        assert isinstance(result, str), f"没有拒绝：{expression} -> {result!r}"
        assert result.startswith("计算失败："), (
            f"没有拒绝：{expression} -> {result!r}"
        )
        # 不能真的算出结果
        assert result != "计算失败：表达式为空"


def test_result_is_never_executed():
    """用文件系统做真实校验：危险表达式不能创建出文件。"""
    import tempfile
    from pathlib import Path as _Path

    with tempfile.TemporaryDirectory() as tmp:
        marker = _Path(tmp) / "pwned.txt"
        target = str(marker).replace("\\", "/")

        for expression in (
            f'__import__("pathlib").Path("{target}").write_text("x")',
            f'open(r"{target}", "w").write("x")',
            f'__import__("os").system("echo x > {target}")',
        ):
            result = calculator(expression)
            assert result.startswith("计算失败："), result

        assert not marker.exists(), "危险表达式真的创建了文件！"


def test_power_bomb_is_rejected():
    """9**9**9 这类表达式必须被规模检查拦住，而不是去分配内存。"""
    for expression in ("9**9**9", "9**9**9**9", "10**100000000", "2**99999999999"):
        result = calculator(expression)

        assert result.startswith("计算失败："), (
            f"没有拦住幂运算炸弹：{expression} -> {result!r}"
        )

    # 正常规模的幂运算仍然要能算
    assert calculator("2**1000") == 2 ** 1000


def test_long_expression_is_rejected():
    assert calculator("1+" * 200 + "1").startswith("计算失败：表达式过长")
    # 200 字符上限刚好挡住 99 层括号
    assert calculator("(" * 99 + "1" + ")" * 99) == 1


def test_deep_nesting_is_rejected():
    """括号在 AST 里不加深嵌套，真正加深的是一元运算符链和幂运算链。"""
    assert calculator("-" * 50 + "1") == "计算失败：表达式嵌套太深"
    assert calculator("-" * 199 + "1") == "计算失败：表达式嵌套太深"
    assert calculator("**".join(["2"] * 50)) == "计算失败：表达式嵌套太深"

    # 浅层的一元运算仍然正常
    assert calculator("--5") == 5
    assert calculator("2**3**2") == 512


def test_error_message_is_model_friendly():
    """返回给模型的是文本而不是异常，模型才能读懂原因并重试。"""
    result = calculator('__import__("os")')

    assert result.startswith("计算失败：")
    assert "不允许" in result or "只在" in result or "只允许" in result


def main():
    from run_all import collect, run_module

    return run_module(__name__, {name: value for name, value in globals().items()})


if __name__ == "__main__":
    sys.exit(main())
