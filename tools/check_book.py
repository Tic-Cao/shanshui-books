#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按本书的写作规矩检查一（或两）本书。

用法：
    python tools/check_book.py                      # 两本都查
    python tools/check_book.py books/shanshui-youhui

读 manifest.json，逐篇打开 Markdown，检查：文件在不在、首行标题对不对、有没有
导航页脚、禁词、半角标点、直引号、繁简混排、同篇内的重复段落、字数分布。
有问题时退出码为 1，可以直接当提交前的检查用。
"""
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 作者自己定的禁词：这些词一出现，句子基本就空了。
BANNED = ["治愈", "内耗", "松弛感", "岁月静好", "人间值得", "诗和远方",
          "在这个快节奏的时代", "愿你", "不忘初心", "仪式感", "小确幸"]

# 改稿时最容易混进来的繁体字（常用的一部分；两边同形的字不放进来）。
TRAD = set("後於個們來時說對開關間問閱讀書寫見長門東車馬風雲讓還進遠應該覺麼樣種選離學實現經過經濟關係")
# 确实该保留的写法：地名、人名、引文里的繁体不算错。
TRAD_OK = {"於": ("於潜", "姓於")}

ASCII_PUNCT = re.compile(r"[,;?!]")      # 冒号不算：commit 标题、SQL 里常见
CODE_SPAN = re.compile(r"`[^`]*`")       # 行内代码不参与标点与引号检查
OBJ_SPAN = re.compile(r"[\[{][^\]}]*[\]}]")  # 正文里直接抄出来的代码片段，如 { level: 'read' }
CJK = re.compile(r"[\u4e00-\u9fff]")
NAV = "<!-- nav -->"


def prose_lines(text):
    """逐行给出普通正文（跳过代码块、纯代码行、HTML 注释）。"""
    in_fence = False
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.strip().startswith("<!--"):
            continue
        if not CJK.search(line):
            continue
        yield i, OBJ_SPAN.sub("", CODE_SPAN.sub("", line))


def check(book_dir):
    problems = []
    man = json.loads((book_dir / "manifest.json").read_text(encoding="utf-8"))
    front, back = man["front"], man["back"]
    entries = [(front["file"], front["title"])]
    for v in man["volumes"]:
        entries += [(e["file"], e["title"]) for e in v["essays"]]
    entries.append((back["file"], back["title"]))
    ends = {front["file"], back["file"]}

    counts, nav_ok, total = {}, 0, 0
    for rel, title in entries:
        path = book_dir / rel
        if not path.exists():
            problems.append("MISSING  %s" % rel)
            continue
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append("BOM      %s" % rel)
        if b"\r\n" in raw:
            problems.append("CRLF     %s" % rel)
        text = raw.decode("utf-8-sig")

        first = text.split("\n")[0].strip()
        if first != "# " + title:
            problems.append("TITLE    %s  首行=%r 期望=%r" % (rel, first, "# " + title))

        body = text.split(NAV)[0].strip()
        if NAV not in text:
            problems.append("NONAV    %s" % rel)
        else:
            nav_ok += 1

        for i, line in prose_lines(body):
            for w in BANNED:
                if w in line:
                    problems.append("BAN      %s:%d %s // %s" % (rel, i, w, line.strip()[:60]))
            if '"' in line or "'" in line:
                problems.append("STRTQ    %s:%d // %s" % (rel, i, line.strip()[:60]))
            hit = ASCII_PUNCT.findall(line)
            if hit:
                problems.append("ASCIIQ   %s:%d %s // %s" % (rel, i, "".join(sorted(set(hit))), line.strip()[:60]))
            tr = sorted({c for c in line if c in TRAD
                         and not any(ctx in line for ctx in TRAD_OK.get(c, ()))})
            if tr:
                problems.append("TRAD     %s:%d %s" % (rel, i, "".join(tr)))

        if re.search(r"\n[ \t]*\n[ \t]*\n[ \t]*\n", body):
            problems.append("BLANKS   %s 三行以上空行" % rel)

        seen = {}
        for p in body.split("\n"):
            p = p.strip()
            if len(p) > 16 and p != "---":
                seen[p] = seen.get(p, 0) + 1
        for p, n in seen.items():
            if n > 1:
                problems.append("DUPPARA  %s ×%d // %s" % (rel, n, p[:48]))

        body_only = body.split("\n", 1)[1] if body.startswith("# ") else body
        counts[rel] = len(CJK.findall(body_only))
        total += counts[rel]

    per_vol = {v["id"]: len(v["essays"]) for v in man["volumes"]}
    essays = {k: v for k, v in counts.items() if k not in ends}
    out = io.StringIO()
    out.write("《%s》 · %s\n" % (man["book"]["title"], book_dir.name))
    out.write("  篇数：%d（序 1 + 正文 %d + 后记 1），各卷 %s\n"
              % (len(entries), sum(per_vol.values()), sorted(per_vol.values())))
    out.write("  字数：%s（序 %s · 正文 %s · 后记 %s）\n"
              % (format(total, ","), format(counts[front["file"]], ","),
                 format(total - counts[front["file"]] - counts[back["file"]], ","),
                 format(counts[back["file"]], ",")))
    out.write("  单篇：最短 %s（%s）/ 最长 %s（%s）/ 正文低于 4000 的：%s\n"
              % (min(essays.values()), min(essays, key=essays.get).split("/")[-1],
                 max(essays.values()), max(essays, key=essays.get).split("/")[-1],
                 ", ".join(sorted(k for k, v in essays.items() if v < 4000)) or "无"))
    out.write("  导航页脚：%d/%d 篇\n" % (nav_ok, len(entries)))
    out.write("  问题：%d 条\n" % len(problems))
    for p in problems:
        out.write("    " + p + "\n")
    return out.getvalue(), problems


def main():
    targets = sys.argv[1:] or sorted("books/" + p.name for p in (REPO / "books").iterdir() if p.is_dir())
    bad = 0
    for t in targets:
        d = REPO / t
        text, problems = check(d)
        print(text)
        bad += len(problems)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
