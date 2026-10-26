# -*- coding: utf-8 -*-
"""Build 《山水有信》 into one standalone HTML file.

Run from anywhere:  python tools/build_shanshui_youxin.py
Needs: Python 3.10+ and markdown-it-py (pip install -r requirements.txt).
"""
import base64
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOOK = REPO / "books" / "shanshui-youxin"
OUT = REPO / "dist" / "shanshui-youxin.html"

import sys
VENDOR = Path(__file__).resolve().parent / "_vendor"
if VENDOR.is_dir():
    sys.path[:0] = [str(VENDOR)]
from markdown_it import MarkdownIt

MANIFEST = json.loads((BOOK / "manifest.json").read_text(encoding="utf-8"))
MD = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})

CN_NUM = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
EN_NUM = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX"]


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def data_uri(rel: str) -> str:
    raw = (BOOK / rel).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


MISSING = []


def load_markdown(rel: str) -> tuple[str, str]:
    path = BOOK / rel
    if not path.exists():
        MISSING.append(rel)
        return "", "<p>（本篇尚在写作中）</p>"
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    # the Markdown carries a navigation footer for GitHub; the book itself does not need it
    text = re.sub(r"\n<!-- nav -->.*", "", text, count=1, flags=re.S).strip()
    lines = text.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    return body, MD.render(body)


def strip_prefix(title: str) -> str:
    return re.sub(r"^(序|后记)[：:]\s*", "", title)


book = MANIFEST["book"]
volumes = MANIFEST["volumes"]

# ---- collect content -------------------------------------------------------
front = MANIFEST["front"]
front_body, front_html = load_markdown(front["file"])
back = MANIFEST["back"]
back_body, back_html = load_markdown(back["file"])

for vol in volumes:
    for essay in vol["essays"]:
        essay["_body"], essay["_html"] = load_markdown(essay["file"])
        essay["_count"] = cjk_count(essay["_body"])

counts = {"front": cjk_count(front_body), "back": cjk_count(back_body)}
total = counts["front"] + counts["back"] + sum(e["_count"] for v in volumes for e in v["essays"])

# ---- reading order (front, essays, back) -----------------------------------
readable = [{"anchor": "xu", "title": strip_prefix(front["title"])}]
for vol in volumes:
    for essay in vol["essays"]:
        readable.append({
            "anchor": "e-" + essay["id"],
            "title": essay["title"],
        })
readable.append({"anchor": "houji", "title": strip_prefix(back["title"])})
read_index = {item["anchor"]: i for i, item in enumerate(readable)}


def chapter_nav(anchor: str) -> str:
    i = read_index[anchor]
    prev_item = readable[i - 1] if i > 0 else None
    next_item = readable[i + 1] if i + 1 < len(readable) else None
    if prev_item:
        prev = (
            f'<a class="prev" href="#{prev_item["anchor"]}">'
            f'<span class="dir">上一篇</span><span class="t">{esc(prev_item["title"])}</span></a>'
        )
    else:
        prev = '<a class="prev empty" aria-hidden="true"><span class="dir">上一篇</span><span class="t">　</span></a>'
    if next_item:
        nxt = (
            f'<a class="next" href="#{next_item["anchor"]}">'
            f'<span class="dir">下一篇</span><span class="t">{esc(next_item["title"])}</span></a>'
        )
    else:
        nxt = '<a class="next empty" aria-hidden="true"><span class="dir">下一篇</span><span class="t">　</span></a>'
    return (
        f'<nav class="chapter-nav" aria-label="章节导航">{prev}{nxt}'
        f'<a class="toc-return" href="#toc-page">回到目录</a></nav>'
    )


# ---- table of contents -----------------------------------------------------
def toc_grid() -> str:
    blocks = []
    for vol in volumes:
        items = "".join(
            f'<li><a href="#e-{e["id"]}"><span class="no">{n:02d}</span>'
            f'<span class="ti">{esc(e["title"])}</span></a></li>'
            for n, e in enumerate(vol["essays"], 1)
        )
        blocks.append(
            f'<div class="vol-toc"><p class="kicker">卷{CN_NUM[vol["id"]]}</p>'
            f'<h3>{esc(vol["title"])}</h3><ol>{items}</ol></div>'
        )
    return "".join(blocks)


def drawer_nav() -> str:
    parts = [
        f'<a class="front-link" href="#xu"><span class="no">序</span>{esc(strip_prefix(front["title"]))}</a>'
    ]
    for vol in volumes:
        items = "".join(
            f'<li><a href="#e-{e["id"]}"><span class="no">{n:02d}</span>'
            f'<span>{esc(e["title"])}</span></a></li>'
            for n, e in enumerate(vol["essays"], 1)
        )
        parts.append(
            f'<div class="dvol"><h3>卷{CN_NUM[vol["id"]]} · VOLUME {EN_NUM[vol["id"]]}</h3>'
            f'<p class="dtitle">{esc(vol["title"])}</p><ol>{items}</ol></div>'
        )
    parts.append(
        f'<a class="front-link back-link" href="#houji"><span class="no">后</span>{esc(strip_prefix(back["title"]))}</a>'
    )
    return "".join(parts)


# ---- body sections ---------------------------------------------------------
cover = f'''
<header class="cover" id="cover">
  <div class="cover-media">
    <img src="{data_uri('assets/images/cover.jpg')}" alt="水墨山峦、云雾与一轮淡红的日，纸色天空">
  </div>
  <p class="cover-top">{esc(book["category"])}</p>
  <div class="cover-copy">
    <div class="seal" aria-hidden="true"><span>山</span><span>水</span><span>有</span><span>信</span></div>
    <h1>{esc(book["title"])}</h1>
    <p class="subtitle">{esc(book["subtitle"])}</p>
    <p class="meta">{esc(book["author"])} 著 · {esc(book["edition"])}</p>
    <p class="tagline">{esc(book["tagline"])}</p>
  </div>
  <a class="cover-cta" href="#toc-page"><span>目录</span><span class="line"></span></a>
</header>
'''

toc_page = f'''
<section class="page" id="toc-page">
  <div class="page-head"><h2>目录</h2><span>CONTENTS</span></div>
  <p class="toc-intro">六卷 · 四十八篇 · 约 {total:,} 字</p>
  <div class="toc-ends">
    <a href="#xu"><span class="k">序</span><span class="v">{esc(strip_prefix(front["title"]))}</span></a>
    <a href="#houji"><span class="k">后</span><span class="v">{esc(strip_prefix(back["title"]))}</span></a>
  </div>
  <div class="toc-grid">{toc_grid()}</div>
</section>
'''

front_section = f'''
<article class="matter" id="xu" data-crumb="序">
  <p class="kicker">序 · PREFACE</p>
  <h1>{esc(strip_prefix(front["title"]))}</h1>
  <div class="body">{front_html}</div>
</article>
{chapter_nav("xu")}
'''

volume_sections = []
for vol in volumes:
    vid = vol["id"]
    plate = f'''
<section class="volume" id="vol-{vid}" data-crumb="卷{CN_NUM[vid]} · {esc(vol["title"])}">
  <p class="volume-kicker">卷{CN_NUM[vid]} · VOLUME {EN_NUM[vid]}</p>
  <h2>{esc(vol["title"])}</h2>
  <p class="latin">{esc(vol["latin"])}</p>
  <blockquote>{esc(vol["epigraph"])}</blockquote>
  <figure class="plate">
    <img src="{data_uri(vol["image"])}" alt="{esc(vol["image_alt"])}" loading="lazy" decoding="async">
    <figcaption>{esc(vol["image_caption"])}</figcaption>
  </figure>
</section>
'''
    volume_sections.append(plate)
    for n, essay in enumerate(vol["essays"], 1):
        volume_sections.append(f'''
<article class="essay" id="e-{essay["id"]}" data-crumb="{esc(essay["title"])}">
  <p class="kicker">卷{CN_NUM[vid]} · {n:02d}</p>
  <h1>{esc(essay["title"])}</h1>
  <div class="body">{essay["_html"]}</div>
</article>
{chapter_nav("e-" + essay["id"])}
''')

back_section = f'''
<article class="matter back" id="houji" data-crumb="后记">
  <p class="kicker">后记 · AFTERWORD</p>
  <h1>{esc(strip_prefix(back["title"]))}</h1>
  <div class="body">{back_html}</div>
</article>
{chapter_nav("houji")}
'''

colophon = f'''
<section class="colophon">
  <div class="seal" aria-hidden="true"><span>山</span><span>水</span><span>有</span><span>信</span></div>
  <h2>{esc(book["title"])}</h2>
  <p class="sub">{esc(book["subtitle"])}</p>
  <p>{esc(book["author"])} 著<br>{esc(book["category"])}<br>{esc(book["edition"])}</p>
  <p>全书六卷，四十八篇，约 {total:,} 字。</p>
  <p class="fine">卷五《人间烟火》中的人物均为化名，细节经过文学处理。<br>本书为虚构作品。插图由 AI 生成，经裁切与调色。</p>
</section>
'''

CSS = r'''
:root{
  --paper:#f5f0e6;
  --paper-soft:#faf7f0;
  --paper-deep:#ece4d5;
  --ink:#20241f;
  --ink-soft:#3c4038;
  --muted:#797268;
  --faint:#a29a8d;
  --line:#d9d0bf;
  --clay:#a7442e;
  --clay-soft:#c76a4e;
  --forest:#1f2c25;
  --forest-soft:#2b3a31;
  --cream:#f2eadb;
  --serif:"Noto Serif SC","Songti SC","STSong","SimSun",Georgia,serif;
  --sans:"Avenir Next","Inter","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --measure:33rem;
  --fs:18px;
}
html.fs-s{--fs:16px}
html.fs-l{--fs:20.5px}
html.night{
  --paper:#171b17;
  --paper-soft:#1d221d;
  --paper-deep:#121612;
  --ink:#e6dfd0;
  --ink-soft:#c9c2b4;
  --muted:#948d80;
  --faint:#6f6a60;
  --line:#343a32;
  --clay:#b9563e;
  --clay-soft:#cf7659;
  --forest:#101410;
  --forest-soft:#1b211b;
  --cream:#efe7d7;
}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  margin:0;
  background:
    radial-gradient(circle at 92% 6%,rgba(167,68,46,.055),transparent 26rem),
    radial-gradient(circle at 4% 58%,rgba(87,105,82,.05),transparent 32rem),
    var(--paper);
  color:var(--ink-soft);
  font-family:var(--serif);
  font-size:var(--fs);
  line-height:2.05;
  overflow-x:hidden;
}
html.night body{
  background:
    radial-gradient(circle at 92% 6%,rgba(185,86,62,.06),transparent 26rem),
    radial-gradient(circle at 4% 58%,rgba(120,140,112,.05),transparent 32rem),
    var(--paper);
}
body.locked{overflow:hidden}
body::before{
  content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.55;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.05'/%3E%3C/svg%3E");
}
main{position:relative;z-index:1}
a{color:inherit;text-decoration:none}
img{max-width:100%}
::selection{background:rgba(167,68,46,.22)}
:focus-visible{outline:2px solid var(--clay);outline-offset:4px}

.skip{position:absolute;left:-999px;top:0;z-index:200;background:var(--forest);color:var(--cream);padding:.7rem 1rem;font-family:var(--sans);font-size:.8rem}
.skip:focus{left:1rem;top:1rem}

/* ---------- top bar ---------- */
.readbar{
  position:fixed;top:0;left:0;right:0;height:2px;background:var(--clay);
  transform:scaleX(0);transform-origin:0 50%;z-index:100;pointer-events:none;
}
.topbar{
  position:fixed;top:0;left:0;right:0;height:56px;z-index:90;
  display:flex;align-items:center;gap:1rem;
  padding:0 clamp(1rem,4vw,2.6rem);
  background:rgba(245,240,230,.9);
  -webkit-backdrop-filter:blur(16px) saturate(1.1);
  backdrop-filter:blur(16px) saturate(1.1);
  border-bottom:1px solid var(--line);
  font-family:var(--sans);
  transform:translateY(-102%);
  transition:transform .4s ease;
}
html.night .topbar{background:rgba(23,27,23,.9)}
.topbar.show{transform:none}
.tb-btn{
  appearance:none;background:none;border:0;font:inherit;
  font-size:.64rem;letter-spacing:.26em;color:var(--ink);
  cursor:pointer;padding:.55rem .2rem;display:flex;align-items:center;gap:.55rem;
}
.tb-btn:hover{color:var(--clay)}
.bars{display:flex;flex-direction:column;gap:3px;width:16px}
.bars i{display:block;height:1px;background:currentColor}
.brand{font-family:var(--serif);font-size:.95rem;letter-spacing:.16em;color:var(--ink);white-space:nowrap}
.crumb{
  flex:1;text-align:center;font-size:.66rem;letter-spacing:.14em;color:var(--muted);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;
}
.theme{width:2.2rem;justify-content:center;border:1px solid var(--line);border-radius:999px;letter-spacing:0}

/* ---------- cover ---------- */
.cover{
  position:relative;min-height:100svh;display:flex;align-items:flex-end;
  overflow:hidden;background:var(--forest);scroll-margin-top:0;
}
.cover-media{position:absolute;inset:0}
.cover-media img{
  width:100%;height:100%;object-fit:cover;object-position:50% 38%;
  filter:saturate(.88) contrast(1.03);
}
.cover-media::after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(20,26,22,0) 28%,rgba(18,24,20,.28) 52%,rgba(15,21,17,.86) 90%);
}
.cover-top{
  position:absolute;top:clamp(1.2rem,4vw,2.4rem);left:clamp(1.4rem,5vw,4rem);z-index:2;margin:0;
  font-family:var(--sans);font-size:.68rem;letter-spacing:.34em;
  color:rgba(32,36,31,.66);
}
.cover-copy{
  position:relative;z-index:2;max-width:62rem;
  padding:clamp(2rem,6vw,5rem) clamp(1.6rem,6vw,5rem) clamp(3.2rem,8vw,6rem);
  color:var(--cream);
}
.seal{
  display:inline-grid;grid-template-columns:1fr 1fr;place-items:center;
  width:58px;height:58px;background:var(--clay);color:#fff8ec;
  font-family:var(--serif);font-size:.9rem;line-height:1;letter-spacing:0;
  box-shadow:inset 0 0 0 1px rgba(255,248,236,.28);
}
.cover .seal{margin-bottom:1.5rem}
.cover h1{
  margin:0;font-size:clamp(3.2rem,10vw,7rem);line-height:1.06;
  letter-spacing:.1em;font-weight:500;color:var(--cream);
  text-shadow:0 2px 34px rgba(0,0,0,.38);
}
.cover .subtitle{
  margin:1rem 0 0;font-size:clamp(.95rem,2.1vw,1.3rem);
  letter-spacing:.4em;color:rgba(242,234,219,.84);
}
.cover .meta{
  margin:1.5rem 0 0;font-family:var(--sans);font-size:.72rem;
  letter-spacing:.22em;color:rgba(242,234,219,.66);
}
.cover .tagline{
  margin:2rem 0 0;max-width:27em;font-size:.9rem;line-height:1.95;
  color:rgba(242,234,219,.62);
}
.cover-cta{
  position:absolute;right:clamp(1.4rem,5vw,4rem);bottom:clamp(2rem,6vw,4rem);z-index:2;
  display:flex;flex-direction:column;align-items:center;gap:.9rem;
  font-family:var(--sans);font-size:.64rem;letter-spacing:.32em;
  color:rgba(242,234,219,.78);
}
.cover-cta .line{display:block;width:1px;height:2.8rem;background:rgba(242,234,219,.38)}
.cover-cta:hover{color:#fff}

/* ---------- contents page ---------- */
.page{
  max-width:1120px;margin:0 auto;
  padding:clamp(4rem,10vw,8rem) clamp(1.4rem,6vw,4rem);
  scroll-margin-top:56px;
}
.page-head{
  display:flex;justify-content:space-between;align-items:flex-end;
  border-bottom:1px solid var(--line);padding-bottom:1.1rem;
}
.page-head h2{
  margin:0;font-size:clamp(2rem,4.4vw,3rem);font-weight:500;
  letter-spacing:.14em;color:var(--ink);
}
.page-head span{font-family:var(--sans);font-size:.64rem;letter-spacing:.34em;color:var(--muted)}
.toc-intro{margin:1.2rem 0 0;font-size:.86rem;letter-spacing:.06em;color:var(--muted)}
.toc-ends{
  display:grid;grid-template-columns:1fr 1fr;gap:2rem;
  margin:2.6rem 0 0;
}
.toc-ends a{
  display:flex;align-items:baseline;gap:.9rem;padding:.9rem 0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  font-size:.95rem;color:var(--ink-soft);
}
.toc-ends a:hover{color:var(--clay)}
.toc-ends .k{font-family:var(--sans);font-size:.62rem;letter-spacing:.2em;color:var(--clay)}
.toc-ends .v{flex:1}
.toc-grid{display:grid;grid-template-columns:1fr 1fr;gap:3.2rem 4.5rem;margin-top:3.4rem}
.vol-toc .kicker{font-family:var(--sans);font-size:.6rem;letter-spacing:.32em;color:var(--clay);margin:0}
.vol-toc h3{margin:.4rem 0 1rem;font-size:1.3rem;font-weight:600;letter-spacing:.1em;color:var(--ink)}
.vol-toc ol{list-style:none;margin:0;padding:0}
.vol-toc li{border-top:1px solid var(--line)}
.vol-toc li:last-child{border-bottom:1px solid var(--line)}
.vol-toc a{
  display:flex;align-items:baseline;gap:1rem;padding:.6rem 0;
  font-size:.9rem;color:var(--ink-soft);transition:color .2s ease;
}
.vol-toc a:hover{color:var(--clay)}
.vol-toc .no{font-family:var(--sans);font-size:.62rem;letter-spacing:.08em;color:var(--faint)}
.vol-toc .ti{flex:1}

/* ---------- volume opener ---------- */
.volume{
  min-height:100svh;display:grid;place-content:center;justify-items:center;
  text-align:center;padding:clamp(3rem,7vh,6rem) clamp(1.4rem,6vw,4rem);
  scroll-margin-top:56px;
}
.volume-kicker{
  margin:0;font-family:var(--sans);font-size:.62rem;letter-spacing:.4em;
  color:var(--clay);text-transform:uppercase;
}
.volume h2{
  margin:.9rem 0 .2rem;font-size:clamp(2.1rem,5.2vw,3.6rem);
  font-weight:500;letter-spacing:.18em;color:var(--ink);
}
.volume .latin{
  margin:0 0 1.9rem;font-family:var(--sans);font-size:.6rem;
  letter-spacing:.38em;color:var(--muted);
}
.volume blockquote{
  display:flex;align-items:center;gap:1rem;margin:0 0 2.2rem;
  font-size:.94rem;letter-spacing:.05em;color:var(--muted);
}
.volume blockquote::before,.volume blockquote::after{
  content:"";width:2.2rem;height:1px;background:var(--line);
}
.plate{
  margin:0;padding:.55rem;border:1px solid var(--line);background:var(--paper-soft);
  width:fit-content;max-width:min(100%,860px);
  box-shadow:0 30px 70px -50px rgba(32,36,31,.5);
}
.plate img{
  display:block;width:auto;height:auto;max-width:100%;max-height:47svh;
  filter:saturate(.86) contrast(.97);
}
html.night .plate img,html.night .cover-media img{filter:brightness(.8) saturate(.8)}
.plate figcaption{
  margin-top:.55rem;font-family:var(--sans);font-size:.58rem;
  letter-spacing:.22em;color:var(--faint);text-align:right;
}

/* ---------- essay ---------- */
.essay,.matter{
  max-width:var(--measure);margin:0 auto;
  padding:clamp(3.4rem,8vw,6.4rem) clamp(1.3rem,5vw,2rem) clamp(2.4rem,5vw,3.6rem);
  scroll-margin-top:56px;
}
.matter{max-width:calc(var(--measure) + 2rem)}
.kicker{
  display:flex;align-items:center;gap:.9rem;margin:0;
  font-family:var(--sans);font-size:.62rem;letter-spacing:.3em;
  color:var(--clay);text-transform:uppercase;
}
.kicker::after{content:"";height:1px;flex:1;background:var(--line)}
.matter .kicker{justify-content:center}
.matter .kicker::after{display:none}
.essay h1,.matter h1{
  margin:1.1rem 0 2.4rem;font-size:clamp(1.85rem,4.6vw,2.7rem);
  line-height:1.38;letter-spacing:.05em;font-weight:600;color:var(--ink);
}
.matter h1{text-align:center;margin-bottom:3.2rem}
.body{
  color:var(--ink-soft);
  font-size:1em;line-height:2.05;
  text-align:justify;text-justify:inter-ideograph;
  overflow-wrap:break-word;
}
.body p{margin:0 0 1em;text-indent:2em}
.body p:last-child{margin-bottom:0}
.body hr{
  border:0;height:auto;margin:2.7em 0;text-align:center;
}
.body hr::after{
  content:"＊　＊　＊";font-family:var(--serif);font-size:.64rem;
  letter-spacing:.18em;color:var(--faint);
}
.body blockquote{
  margin:1.6em 2em;padding-left:1.1em;border-left:1px solid var(--line);
  color:var(--muted);
}
.body em{font-style:normal;color:var(--ink)}

.chapter-nav{
  max-width:var(--measure);margin:0 auto;
  padding:1.8rem clamp(1.3rem,5vw,2rem) clamp(3rem,7vw,5rem);
  display:grid;grid-template-columns:1fr 1fr;gap:1.4rem;
  border-top:1px solid var(--line);
}
.chapter-nav a{display:flex;flex-direction:column;gap:.45rem;min-width:0}
.chapter-nav .dir{font-family:var(--sans);font-size:.58rem;letter-spacing:.3em;color:var(--muted)}
.chapter-nav .t{
  font-size:.98rem;line-height:1.55;color:var(--ink);
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;max-width:100%;
}
.chapter-nav a:hover .t{color:var(--clay)}
.chapter-nav .next{text-align:right;align-items:flex-end}
.chapter-nav .empty{visibility:hidden}
.toc-return{
  grid-column:1/-1;align-items:center;text-align:center;
  padding-top:1.5rem;margin-top:.4rem;border-top:1px dashed var(--line);
  font-family:var(--sans);font-size:.6rem;letter-spacing:.3em;color:var(--muted);
}
.toc-return:hover{color:var(--clay)}

/* ---------- colophon ---------- */
.colophon{
  max-width:32rem;margin:0 auto;text-align:center;
  padding:clamp(5rem,11vw,9rem) 1.5rem clamp(4rem,8vw,6rem);
  border-top:1px solid var(--line);
}
.colophon .seal{margin-bottom:2rem}
.colophon h2{margin:0;font-size:1.9rem;font-weight:500;letter-spacing:.2em;color:var(--ink)}
.colophon .sub{margin:.5rem 0 2rem;font-size:.78rem;letter-spacing:.3em;color:var(--muted)}
.colophon p{margin:0 0 1.2rem;font-size:.82rem;line-height:2;color:var(--muted)}
.colophon .fine{
  margin-top:2.4rem;padding-top:1.6rem;border-top:1px solid var(--line);
  font-size:.68rem;letter-spacing:.08em;line-height:2;color:var(--faint);
}

/* ---------- drawer ---------- */
.scrim{
  position:fixed;inset:0;z-index:110;background:rgba(15,20,16,.46);
  opacity:0;pointer-events:none;transition:opacity .32s ease;
}
.scrim.show{opacity:1;pointer-events:auto}
.drawer{
  position:fixed;top:0;right:0;bottom:0;z-index:120;
  width:min(88vw,400px);overflow-y:auto;overscroll-behavior:contain;
  padding:1.6rem 1.6rem 3rem;
  background:var(--forest);color:var(--cream);
  transform:translateX(102%);
  transition:transform .42s cubic-bezier(.22,.8,.28,1);
  box-shadow:-30px 0 70px rgba(0,0,0,.28);
}
.drawer.open{transform:none}
.drawer-head{
  display:flex;justify-content:space-between;align-items:center;
  padding-bottom:1.1rem;border-bottom:1px solid rgba(242,234,219,.14);
}
.drawer-head h2{margin:0;font-size:.95rem;font-weight:500;letter-spacing:.3em;color:var(--cream)}
.drawer-close{
  width:34px;height:34px;border-radius:50%;cursor:pointer;
  background:none;border:1px solid rgba(242,234,219,.24);
  color:var(--cream);font-size:1rem;line-height:1;
}
.drawer-close:hover{background:rgba(242,234,219,.08)}
.drawer a{color:rgba(242,234,219,.76)}
.drawer a:hover{color:#fff}
.front-link{
  display:flex;align-items:baseline;gap:.9rem;
  padding:.85rem 0;border-bottom:1px solid rgba(242,234,219,.1);
  font-size:.88rem;
}
.front-link .no,.dvol .no{
  font-family:var(--sans);font-size:.58rem;letter-spacing:.14em;
  color:rgba(242,234,219,.36);min-width:1.7em;
}
.dvol{margin-top:1.7rem}
.dvol h3{
  margin:0 0 .35rem;font-family:var(--sans);font-size:.55rem;
  letter-spacing:.28em;color:var(--clay-soft);
}
.dvol .dtitle{margin:0 0 .45rem;font-size:.92rem;letter-spacing:.1em;color:var(--cream)}
.dvol ol{list-style:none;margin:0;padding:0}
.dvol li a{display:flex;gap:.85rem;padding:.4rem 0;font-size:.82rem}
.back-link{margin-top:1.8rem}
.drawer-foot{
  margin-top:2.2rem;padding-top:1.4rem;border-top:1px solid rgba(242,234,219,.14);
  font-family:var(--sans);font-size:.56rem;letter-spacing:.24em;
  color:rgba(242,234,219,.46);
}
.fs-row{display:flex;gap:.45rem;margin-top:.8rem}
.fs-row button{
  flex:1;padding:.55rem 0;cursor:pointer;
  background:transparent;border:1px solid rgba(242,234,219,.2);
  color:rgba(242,234,219,.66);
  font-family:var(--sans);font-size:.58rem;letter-spacing:.2em;
}
.fs-row button:hover{border-color:rgba(242,234,219,.45)}
.fs-row button.active{background:var(--clay);border-color:var(--clay);color:#fff8ec}

/* ---------- responsive ---------- */
@media (max-width:900px){
  .toc-grid{grid-template-columns:1fr;gap:2.6rem}
  .crumb{display:none}
  .brand{flex:1;text-align:center}
  .topbar{gap:.6rem}
  .cover{min-height:100svh}
  .cover-copy{padding-bottom:5.4rem}
  .cover-cta{bottom:1.4rem;flex-direction:row;gap:.7rem}
  .cover-cta .line{width:2.2rem;height:1px}
  .chapter-nav{grid-template-columns:1fr;gap:1.2rem}
  .chapter-nav .next{text-align:left;align-items:flex-start}
  .chapter-nav .empty{display:none}
  .volume{min-height:auto;padding-top:5rem;padding-bottom:4rem}
}
@media (max-width:520px){
  :root{--fs:17px}
  html.fs-s{--fs:15.5px}
  html.fs-l{--fs:19.5px}
  .topbar{height:52px}
  .page,.volume,.essay,.matter{scroll-margin-top:52px}
  .cover h1{letter-spacing:.06em}
  .cover .subtitle{letter-spacing:.28em}
  .cover-top{font-size:.6rem;letter-spacing:.24em}
  .plate{padding:.4rem}
  .toc-ends{grid-template-columns:1fr;gap:.4rem}
  .essay h1{margin-bottom:2rem}
  .volume blockquote::before,.volume blockquote::after{display:none}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation:none!important;transition:none!important}
}

/* ---------- print ---------- */
@media print{
  @page{size:A5;margin:16mm 15mm}
  :root,html.night{
    --paper:#fff;--paper-soft:#fff;--paper-deep:#fff;
    --ink:#000;--ink-soft:#111;--muted:#333;--faint:#666;
    --line:#999;--cream:#111;
  }
  html,body{background:#fff!important}
  body::before{display:none}
  body{font-size:10.5pt;line-height:1.9}
  .topbar,.readbar,.drawer,.scrim,.skip,.chapter-nav,.cover-cta{display:none!important}
  .cover{
    min-height:auto;display:block;background:#fff;
    page-break-after:always;padding:36mm 0 0;text-align:center;
    -webkit-print-color-adjust:exact;print-color-adjust:exact;
  }
  .cover-media{display:none}
  .cover-top{position:static;color:#333;margin:0 0 18mm}
  .cover-copy{padding:0;color:#111;max-width:none}
  .cover .seal{background:#a7442e;color:#fff;margin-bottom:8mm}
  .cover h1{color:#111;text-shadow:none;font-size:40pt;letter-spacing:.12em}
  .cover .subtitle{color:#333;margin-top:6mm}
  .cover .meta{color:#333;margin-top:8mm}
  .cover .tagline{color:#444;margin:12mm auto 0;max-width:90%}
  .page{max-width:none;padding:0;page-break-after:always}
  .toc-grid{grid-template-columns:1fr 1fr;gap:6mm 10mm;margin-top:8mm}
  .vol-toc a{padding:1mm 0;font-size:8pt}
  .toc-ends{margin-top:6mm}
  .volume{
    min-height:auto;display:block;text-align:center;
    page-break-before:always;page-break-inside:avoid;padding:6mm 0 0;
  }
  .volume h2{margin:4mm 0 2mm;font-size:26pt}
  .volume blockquote{margin-bottom:6mm;display:block;font-size:9pt}
  .volume blockquote::before,.volume blockquote::after{display:none}
  .plate{max-width:100%;padding:2mm;box-shadow:none;page-break-inside:avoid}
  .plate img{max-height:none;filter:none}
  .essay,.matter{
    max-width:none;padding:0;page-break-before:always;
  }
  .matter h1{text-align:left}
  .essay h1{font-size:20pt;margin:4mm 0 7mm}
  .matter h1{font-size:20pt;margin:4mm 0 8mm}
  .kicker{font-size:7pt;color:#a7442e}
  .body{font-size:10.5pt;line-height:1.9;text-align:justify}
  .body p{orphans:3;widows:3}
  .body hr{margin:5mm 0}
  .colophon{page-break-before:always;border-top:0}
  .seal{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  a{color:#000;text-decoration:none}
}
'''

JS = r'''
(function(){
  var doc = document.documentElement;
  var topbar = document.querySelector('.topbar');
  var bar = document.querySelector('.readbar');
  var drawer = document.querySelector('.drawer');
  var scrim = document.querySelector('.scrim');
  var crumb = document.querySelector('.crumb');
  var themeBtn = document.querySelector('.theme');
  var cover = document.querySelector('.cover');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('[data-crumb]'));

  function syncTheme(){
    var night = doc.classList.contains('night');
    themeBtn.textContent = night ? '昼' : '夜';
    themeBtn.setAttribute('aria-label', night ? '切换到日间模式' : '切换到夜间模式');
  }
  syncTheme();
  themeBtn.addEventListener('click', function(){
    doc.classList.toggle('night');
    try{ localStorage.setItem('sxs-theme', doc.classList.contains('night') ? 'night' : 'day'); }catch(e){}
    syncTheme();
  });

  var sizes = ['fs-s','fs-m','fs-l'];
  var fsButtons = Array.prototype.slice.call(document.querySelectorAll('[data-fs]'));
  var currentFs = 'fs-m';
  try{ currentFs = localStorage.getItem('sxs-fs') || 'fs-m'; }catch(e){}
  sizes.forEach(function(s){ doc.classList.toggle(s, s === currentFs); });
  fsButtons.forEach(function(btn){
    btn.classList.toggle('active', btn.dataset.fs === currentFs);
    btn.addEventListener('click', function(){
      var v = btn.dataset.fs;
      sizes.forEach(function(s){ doc.classList.toggle(s, s === v); });
      fsButtons.forEach(function(b){ b.classList.toggle('active', b === btn); });
      try{ localStorage.setItem('sxs-fs', v); }catch(e){}
    });
  });

  function openDrawer(){
    drawer.classList.add('open');
    scrim.classList.add('show');
    document.body.classList.add('locked');
    drawer.setAttribute('aria-hidden','false');
    drawer.inert = false;
    menuBtn.setAttribute('aria-expanded','true');
  }
  function closeDrawer(){
    drawer.classList.remove('open');
    scrim.classList.remove('show');
    document.body.classList.remove('locked');
    drawer.setAttribute('aria-hidden','true');
    drawer.inert = true;
    menuBtn.setAttribute('aria-expanded','false');
  }
  var menuBtn = document.querySelector('.menu-btn');
  menuBtn.addEventListener('click', openDrawer);
  document.querySelector('.drawer-close').addEventListener('click', closeDrawer);
  scrim.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){ closeDrawer(); }
  });

  document.addEventListener('click', function(e){
    var a = e.target && e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if(!a) return;
    var href = a.getAttribute('href');
    if(!href || href === '#') return;
    var target = document.querySelector(href);
    if(!target) return;
    e.preventDefault();
    var wasOpen = drawer.classList.contains('open');
    if(wasOpen) closeDrawer();
    var dist = Math.abs(target.getBoundingClientRect().top);
    var behavior = dist > window.innerHeight * 2 ? 'instant' : 'smooth';
    window.setTimeout(function(){
      target.scrollIntoView({behavior: behavior, block: 'start'});
    }, wasOpen ? 90 : 0);
  });

  var ticking = false;
  function update(){
    ticking = false;
    var max = doc.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    bar.style.transform = 'scaleX(' + p + ')';

    if(cover){
      topbar.classList.toggle('show', window.scrollY > cover.offsetHeight - 80);
    }

    var current = null;
    for(var i = 0; i < chapters.length; i++){
      if(chapters[i].getBoundingClientRect().top <= 150){ current = chapters[i]; }
      else { break; }
    }
    if(current && crumb.textContent !== current.dataset.crumb){
      crumb.textContent = current.dataset.crumb;
    }
  }
  window.addEventListener('scroll', function(){
    if(!ticking){ ticking = true; requestAnimationFrame(update); }
  }, {passive:true});
  window.addEventListener('resize', update);
  update();

  document.addEventListener('keydown', function(e){
    if(drawer.classList.contains('open')) return;
    if(e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if(/INPUT|TEXTAREA|SELECT/.test(tag)) return;
    var idx = -1;
    for(var i = 0; i < chapters.length; i++){
      if(chapters[i].getBoundingClientRect().top <= 160) idx = i;
      else break;
    }
    var next = e.key === 'ArrowRight' ? chapters[idx + 1] : chapters[idx - 1];
    if(next){
      e.preventDefault();
      next.scrollIntoView({behavior:'smooth', block:'start'});
    }
  });
})();
'''

HEADS = r'''<script>(function(){try{var t=localStorage.getItem('sxs-theme');var d=document.documentElement;if(t==='night')d.classList.add('night');var f=localStorage.getItem('sxs-fs')||'fs-m';d.classList.add(f);}catch(e){}})();</script>'''

page = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f5f0e6">
<title>{esc(book["title"])} · {esc(book["subtitle"])}</title>
<meta name="description" content="{esc(book["tagline"])}">
{HEADS}
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#toc-page">跳到目录</a>
<div class="readbar" aria-hidden="true"></div>
<div class="topbar">
  <button class="tb-btn menu-btn" type="button" aria-label="打开目录" aria-controls="book-toc" aria-expanded="false">
    <span class="bars" aria-hidden="true"><i></i><i></i><i></i></span><span>目录</span>
  </button>
  <a class="brand" href="#cover">{esc(book["title"])}</a>
  <span class="crumb" aria-live="polite"></span>
  <button class="tb-btn theme" type="button" aria-label="切换到夜间模式">夜</button>
</div>

<div class="scrim" aria-hidden="true"></div>
<aside class="drawer" id="book-toc" aria-hidden="true" aria-label="全书目录" inert>
  <div class="drawer-head">
    <h2>目录</h2>
    <button class="drawer-close" type="button" aria-label="关闭目录">×</button>
  </div>
  {drawer_nav()}
  <div class="drawer-foot">
    字号
    <div class="fs-row">
      <button type="button" data-fs="fs-s">小</button>
      <button type="button" data-fs="fs-m">中</button>
      <button type="button" data-fs="fs-l">大</button>
    </div>
    键盘 ← → 翻页
  </div>
</aside>

<main>
{cover}
{toc_page}
{front_section}
{''.join(volume_sections)}
{back_section}
{colophon}
</main>
<script>{JS}</script>
</body>
</html>
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8", newline="\n")  # 仓库里统一 LF

print("WROTE", OUT, OUT.stat().st_size, "bytes")
print("front", counts["front"], "back", counts["back"])
missing = []
for vol in volumes:
    for e in vol["essays"]:
        flag = "" if e["_count"] >= 4000 else "  <-- SHORT"
        print(f'{e["id"]} {e["_count"]}{flag}')
        if e["_count"] < 4000:
            missing.append(e["id"])
print("TOTAL CJK", total)
print("SHORT", missing)
print("MISSING FILES", len(MISSING), MISSING)
