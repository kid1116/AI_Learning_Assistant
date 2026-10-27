"""参数错误在发出 HTTP 请求前返回，测试不依赖搜索密钥。"""
from importlib import import_module
from unittest.mock import patch

web = import_module("tools.web_search")


def test_invalid_search_arguments_never_make_requests():
    with patch.object(web, "BOCHA_API_KEY", "fake"), \
         patch.object(web.urllib.request, "urlopen") as request:
        for query, count in [(None, 5), (" ", 5), ("AI", 0), ("AI", 11),
                             ("AI", "5"), ("AI", True)]:
            assert web.web_search(query, count).startswith("搜索失败：")
        request.assert_not_called()
