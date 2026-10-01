import json
import urllib.error
import urllib.request

from config import BOCHA_API_KEY

SEARCH_URL = "https://api.bochaai.com/v1/web-search"

# 单条摘要的截断长度，防止返回内容把上下文撑爆
MAX_SUMMARY_CHARS = 500


def web_search(query, count=5):
    """博查 Web Search：返回前 count 条结果的 标题 / 链接 / 摘要 文本。"""
    if not BOCHA_API_KEY:
        return "联网搜索不可用：未配置 BOCHA_API_KEY"

    payload = json.dumps({
        "query": query,
        "count": count,
        "freshness": "noLimit",
        "summary": True
    }).encode("utf-8")

    request = urllib.request.Request(
        SEARCH_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {BOCHA_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request, timeout=15
        ) as response:
            body = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:200]
        return f"搜索失败：HTTP {e.code} {detail}"

    except Exception as e:
        return f"搜索失败：{e}"

    if body.get("code") != 200:
        return (
            "搜索失败："
            f"{body.get('msg') or body.get('code')}"
        )

    pages = (body.get("data") or {}).get("webPages") or {}
    results = pages.get("value") or []

    if not results:
        return f"没有找到「{query}」的相关结果"

    lines = []

    for index, item in enumerate(
        results[:count], start=1
    ):
        title = item.get("name") or "(无标题)"
        url = item.get("url") or ""
        text = (
            item.get("summary")
            or item.get("snippet")
            or ""
        )[:MAX_SUMMARY_CHARS]

        lines.append(
            f"{index}. {title}\n"
            f"   链接：{url}\n"
            f"   摘要：{text}"
        )

    return "\n".join(lines)


#测试
if __name__ == "__main__":
    print(web_search("DeepSeek 最新模型"))
