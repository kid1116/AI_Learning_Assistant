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


web_search_schema = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "联网搜索网页信息。当问题涉及最新动态、"
            "实时数据、新闻时事，或超出你知识范围的内容时使用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，尽量具体"
                },
                "count": {
                    "type": "integer",
                    "description": "返回结果条数，1-10，默认 5"
                }
            },
            "required": [
                "query"
            ]
        }
    }
}


TOOLS_SCHEMA = [
    calculator_schema,
    web_search_schema
]