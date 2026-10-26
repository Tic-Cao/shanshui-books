#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查仓库里所有 Markdown 与 dist/index.html 的相对链接是否指向存在的文件。

用法：  python tools/check_links.py
外链（http/https/mailto）与页面内锚点只列出，不检查可达性。
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)|src="([^"]+)"|href="([^"]+)"')
FENCE = re.compile(r"```.*?```", re.S)


def refs(text):
    for m in LINK.finditer(FENCE.sub("", text)):   # 代码块里的示例链接不算
        for g in m.groups():
            if g:
                yield g


def main():
    files = [p for p in REPO.rglob("*") if p.suffix in (".md", ".html") and "_vendor" not in p.parts]
    bad, ext = [], []
    for p in files:
        text = p.read_text(encoding="utf-8")
        for r in refs(text):
            if r.startswith(("http://", "https://", "mailto:", "#", "data:")):
                if not r.startswith("#"):
                    ext.append(r)
                continue
            target = (p.parent / unquote(r.split("#")[0])).resolve()
            if not target.exists():
                bad.append("%s -> %s" % (p.relative_to(REPO), r))
    print("检查 %d 个文件（.md / .html）" % len(files))
    print("外链 %d 条，未验证可达性" % len(set(ext)))
    if bad:
        print("断链 %d 条：" % len(bad))
        for b in bad:
            print("  " + b)
        return 1
    print("断链 0 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
