"""校验示例、实际 Tk 样式、代码原文与链接边界。"""
import tkinter as tk
from unittest.mock import patch

from appearance import PALETTES
from markdown_view import MarkdownView, inline_spans


def test_inline_emphasis_escapes_and_code():
    spans = inline_spans(r"**粗体** 与 *斜体* 和 `**代码**` 及 \*文字\*")
    assert "".join(item[0] for item in spans) == "粗体 与 斜体 和 **代码** 及 *文字*"
    assert ("粗体", ("md_strong",), None) in spans
    assert ("斜体", ("md_em",), None) in spans
    assert ("**代码**", ("md_code",), None) in spans


def test_only_http_links_are_interactive_and_rendering_opens_nothing():
    with patch("markdown_view.webbrowser.open") as opened:
        spans = inline_spans("[网站](https://example.com) [脚本](javascript:alert)")
        assert spans[0][2] == "https://example.com"
        assert "[脚本](javascript:alert)" in "".join(item[0] for item in spans)
        opened.assert_not_called()


def test_example_has_heading_bold_and_literal_fenced_code_in_tk():
    root = tk.Tk()
    root.withdraw()
    try:
        widget = tk.Text(root)
        view = MarkdownView(widget)
        view.configure("Arial", 12, PALETTES["深空"], "#9B8AFF")
        view.insert('# 先说结论\n\n**值得进，但“进组”本身并不难。**\n\n- 列表\n> 引用\n```python\n# 注释\nprint("**原文**")\n```\n[链接](https://example.com)')
        rendered = widget.get("1.0", "end")
        assert rendered.startswith("先说结论\n")
        assert "**值得进" not in rendered
        assert '# 注释\nprint("**原文**")' in rendered
        for tag in ("md_h1", "md_strong", "md_block", "md_quote", "md_list", "md_link"):
            assert widget.tag_ranges(tag), f"缺少样式：{tag}"
        view.clear_links()
        assert not any(tag.startswith("md_url_") for tag in widget.tag_names())
    finally:
        root.destroy()
