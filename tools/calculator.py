import ast
import math

# 允许调用的函数白名单：名字 -> 真正的函数
ALLOWED_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "sqrt": math.sqrt,
}

# 允许出现在表达式里的节点类型
ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Call,
    ast.Name,
    ast.Load,
    # 运算符本身也是节点，需要一并放行
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
)

# 幂运算结果的数量级上限：防止 9**9**9 这类表达式把内存和 CPU 打满
MAX_POWER_DIGITS = 100000

# 表达式长度上限，顺手挡住超长输入
MAX_EXPRESSION_LENGTH = 200

# 括号嵌套深度上限
MAX_DEPTH = 30


# 判断一个值是不是可以参与运算的普通数字（bool 是 int 的子类，要排除）
def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# 先把整棵语法树校验一遍，全部合法才允许求值
def _check_node(node):
    if not isinstance(node, ALLOWED_NODES):
        raise ValueError(f"表达式里不允许出现 {type(node).__name__}")

    if isinstance(node, ast.Constant):
        # 只允许数字，字符串（"a"*3）也在这里被拒绝
        if not _is_number(node.value):
            raise ValueError("表达式里只允许出现数字")

    if isinstance(node, ast.Name):
        # 名称只能是白名单里的函数名
        if node.id not in ALLOWED_FUNCTIONS:
            raise ValueError(f"不允许使用名称 {node.id}")

    if isinstance(node, ast.Call):
        # 必须是白名单里的函数，且不能有关键字参数或 * 参数
        if not isinstance(node.func, ast.Name):
            raise ValueError("不允许这种函数调用形式")

        if node.func.id not in ALLOWED_FUNCTIONS:
            raise ValueError(f"不允许调用函数 {node.func.id}")

        if node.keywords:
            raise ValueError("函数调用不允许使用关键字参数")

        if any(isinstance(arg, ast.Starred) for arg in node.args):
            raise ValueError("函数调用不允许使用 * 参数")

    for child in ast.iter_child_nodes(node):
        _check_node(child)


# 检查幂运算的规模，超上限就拒绝（否则可能直接吃满内存）
def _check_power_size(left, right):
    if not (_is_number(left) and _is_number(right)):
        return

    base = abs(left)

    # |结果| = base ** right，取十进制位数来判断规模
    if base <= 1:
        return

    if right * math.log10(base) > MAX_POWER_DIGITS:
        raise ValueError("幂运算结果过大，已拒绝计算")


# 递归求值
def _eval_node(node, depth=0):
    # 括号嵌套过深时直接拒绝，避免递归过深
    if depth > MAX_DEPTH:
        raise ValueError("表达式嵌套太深")

    if isinstance(node, ast.Expression):
        return _eval_node(node.body, depth + 1)

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        # _check_node 已经保证名字在白名单里
        return ALLOWED_FUNCTIONS[node.id]

    if isinstance(node, ast.Call):
        function = ALLOWED_FUNCTIONS[node.func.id]
        args = [_eval_node(arg, depth + 1) for arg in node.args]

        return function(*args)

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, depth + 1)

        if isinstance(node.op, ast.USub):
            return -operand

        return +operand

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, depth + 1)
        right = _eval_node(node.right, depth + 1)

        if isinstance(node.op, ast.Add):
            return left + right

        if isinstance(node.op, ast.Sub):
            return left - right

        if isinstance(node.op, ast.Mult):
            return left * right

        if isinstance(node.op, ast.Div):
            return left / right

        if isinstance(node.op, ast.FloorDiv):
            return left // right

        if isinstance(node.op, ast.Mod):
            return left % right

        if isinstance(node.op, ast.Pow):
            _check_power_size(left, right)
            return left ** right

    raise ValueError(f"不支持的运算 {type(node).__name__}")


def calculator(expression):
    """计算数学表达式，例如 123*456、sqrt(2)、2**10。"""
    if not isinstance(expression, str):
        return "计算失败：表达式必须是字符串"

    text = expression.strip()

    if not text:
        return "计算失败：表达式为空"

    if len(text) > MAX_EXPRESSION_LENGTH:
        return f"计算失败：表达式过长（超过 {MAX_EXPRESSION_LENGTH} 个字符）"

    try:
        tree = ast.parse(text, mode="eval")
        _check_node(tree)
        return _eval_node(tree)

    except SyntaxError:
        return f"计算失败：表达式语法错误 {expression}"

    except RecursionError:
        # 括号嵌套太深时，Python 解析器本身会先抛递归错误
        return "计算失败：表达式嵌套太深"

    except Exception as e:
        return f"计算失败：{e}"


#测试
if __name__ == "__main__":
    print(calculator("111*555"))
    print(calculator("111/0"))
    print(calculator("2**10"))
    print(calculator("sqrt(2)"))
    print(calculator('__import__("os").system("echo hacked")'))
