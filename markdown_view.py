"""Tk Text 中的轻量 Markdown 展示；不加载 HTML 或远程图片。"""
import re
from urllib.parse import urlparse
import webbrowser


INLINE = re.compile(
    r"(?P<escape>\\[\\`*_[\]()>#+.!~-])"
    r"|(?P<code>`+)(?P<literal>.+?)(?P=code)(?!`)"
    r"|(?P<link>\[(?P<label>[^\]\n]+)\]\((?P<url>[^\s)]+)\))"
    r"|(?P<strong>\*\*|__)(?P<bold>.+?)(?P=strong)"
    r"|(?P<strike>~~)(?P<deleted>.+?)(?P=strike)"
    r"|(?P<em>\*|(?<!\w)_)(?P<italic>[^\n]+?)(?P=em)(?!\w)"
)


def inline_spans(text, tags=(), depth=0):
    """返回 (显示文字, 样式元组, 可选链接)，代码内部保持原样。"""
    if depth >= 12:
        return [(text, tags, None)]
    spans, start = [], 0
    for match in INLINE.finditer(text):
        if match.start() > start:
            spans.append((text[start:match.start()], tags, None))
        if match.group("escape"):
            spans.append((match.group()[1:], tags, None))
        elif match.group("code"):
            spans.append((match.group("literal"), tags + ("md_code",), None))
        elif match.group("link"):
            url = match.group("url")
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https") and parsed.hostname:
                spans.extend((part, style + ("md_link",), url)
                             for part, style, _ in inline_spans(match.group("label"), tags, depth + 1))
            else:
                spans.append((match.group(), tags, None))
        else:
            value, style = ((match.group("bold"), "md_strong") if match.group("strong") else
                            (match.group("deleted"), "md_strike") if match.group("strike") else
                            (match.group("italic"), "md_em"))
            spans.extend(inline_spans(value, tags + (style,), depth + 1))
        start = match.end()
    if start < len(text):
        spans.append((text[start:], tags, None))
    return spans


class MarkdownView:
    def __init__(self, widget):
        self.widget = widget
        self.link_tags = []
        self.next_link = 0

    def configure(self, family, size, palette, accent):
        text = self.widget
        text.tag_configure("md_strong", font=(family, size, "bold"))
        text.tag_configure("md_em", font=(family, size, "italic"))
        text.tag_configure("md_strong_em", font=(family, size, "bold italic"))
        text.tag_configure("md_strike", overstrike=True)
        for level in range(1, 7):
            text.tag_configure(f"md_h{level}", font=(family, size + max(1, 9 - level * 2), "bold"),
                               spacing1=14, spacing3=8)
        text.tag_configure("md_quote", foreground=palette["muted"], lmargin1=16, lmargin2=16)
        text.tag_configure("md_list", lmargin1=8, lmargin2=28)
        text.tag_configure("md_link", foreground=accent, underline=True)
        text.tag_configure("md_code", font=("Consolas", size), background=palette["panel"])
        text.tag_configure("md_block", font=("Consolas", size), background=palette["panel"],
                           lmargin1=12, lmargin2=12, spacing1=0, spacing3=0)
        text.tag_configure("md_rule", foreground=palette["muted"])

    def clear_links(self):
        for name in self.link_tags:
            self.widget.tag_delete(name)
        self.link_tags.clear()

    def insert_inline(self, text, tags=()):
        for value, styles, url in inline_spans(text, tags):
            if "md_strong" in styles and "md_em" in styles:
                styles += ("md_strong_em",)
            if url:
                name = f"md_url_{self.next_link}"
                self.next_link += 1
                self.link_tags.append(name)
                self.widget.tag_bind(name, "<Button-1>", lambda event, target=url: webbrowser.open(target))
                self.widget.tag_bind(name, "<Enter>", lambda event: self.widget.configure(cursor="hand2"))
                self.widget.tag_bind(name, "<Leave>", lambda event: self.widget.configure(cursor="arrow"))
                styles += (name,)
            self.widget.insert("end", value, styles)

    def insert(self, source):
        fence = None
        for line in source.splitlines():
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if fence:
                if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                    fence = None
                else:
                    self.widget.insert("end", line + "\n", ("md_block",))
                continue
            if marker:
                fence = marker[1]
                continue
            heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$", line)
            listing = re.match(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$", line)
            quote = re.match(r"^\s*>\s?(.*)$", line)
            if heading:
                self.insert_inline(heading[2], (f"md_h{len(heading[1])}",))
            elif re.fullmatch(r"\s*(?:\*\s*){3,}|\s*(?:-\s*){3,}|\s*(?:_\s*){3,}", line):
                self.widget.insert("end", "─" * 28, ("md_rule",))
            elif listing:
                bullet = "•" if listing[2] in "-+*" else listing[2]
                self.insert_inline(listing[1] + bullet + "  " + listing[3], ("md_list",))
            elif quote:
                self.insert_inline("│ " + quote[1], ("md_quote",))
            else:
                self.insert_inline(line)
            self.widget.insert("end", "\n")
        self.widget.insert("end", "\n")
