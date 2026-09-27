def calculator(expression):
    try:
        result = eval(expression)
        return result

    except Exception as e:
        return f"计算失败：{e}"

#测试
if __name__ == "__main__":
    print(calculator("111*555"))
    print(calculator("111/0"))