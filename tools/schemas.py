#让llm理解Tool

calculator_schema = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "计算数学表达式",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如 123*456"
                }
            },
            "required": [
                "expression"
            ]
        }
    }
}


TOOLS_SCHEMA = [
    calculator_schema
]