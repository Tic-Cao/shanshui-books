# tools/

五个文件，两本书的排版脚本、两个检查脚本、一个许可。

| 文件 | 干什么 |
|---|---|
| `build_shanshui_youxin.py` | 把 `books/shanshui-youxin/` 排成一个 HTML 文件，写到 `dist/shanshui-youxin.html` |
| `build_shanshui_youhui.py` | 同上，做《山水有回信》 |
| `check_book.py` | 按写作规矩检查正文，有问题退出码 1 |
| `check_links.py` | 检查所有 Markdown 与落地页里的相对链接是否指向存在的文件 |
| `LICENSE` | 脚本本身的 MIT 许可（正文与图片不在范围内） |

## 跑起来

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python tools/build_shanshui_youhui.py
python tools/check_book.py books/shanshui-youhui
python tools/check_links.py            # 目录页与 README 的链接是否都还在
```

脚本用相对自身的路径找仓库根，从任何目录调用都行。如果不想装依赖，把 `markdown-it-py`
解压到 `tools/_vendor/`，脚本会优先用那里的一份。

## 一本书由哪些东西组成

`books/<书>/manifest.json` 是唯一的依据：

```
book      书名、副题、作者、类别、版本、题记、目标字数
front     序：篇名 + 文件 + 目标字数
volumes   六卷。每卷有 id / title / latin（英文小标题）/ epigraph（题辞）/
          image + image_alt + image_caption / essays[]
back      后记
```

每篇 Markdown 只有三条格式要求：首行必须是 `# 篇名`（要和 manifest 一致），正文用短段，
段间需要停顿的地方用单独一行 `---`。篇末的导航块由 `<!-- nav -->` 这一行标记：

```markdown
<!-- nav -->

[← 上一篇](01-xxx.md) · [全书目录](../../README.md) · [下一篇 →](03-xxx.md)
```

它是给 GitHub 上读的人准备的，排版脚本读到 `<!-- nav -->` 就停，所以这一行以及它下面
的内容不会进入书里。这也是为什么改了导航、加了目录跳转之后，`dist/` 里的成书仍然和
上一版逐字节相同。

插图是 `assets/images/` 里的七个 JPEG（封面加六卷各一张），构建时以 base64 内嵌，所以
成书是一个自包含的文件，断网也能读。图片本身是 AI 生成后裁切调色的，见
[../docs/names-and-images.md](../docs/names-and-images.md)。

## 成书里的阅读功能

单文件 HTML 里带的东西都在脚本末尾那段 CSS/JS 里，值得知道的有：

- 夜间模式与三档字号，写在 `localStorage`（`shx-theme` / `shx-fs`，《山水有信》那份是 `sxs-*`），
  首页加载时由 `<head>` 里一段小脚本先套上，避免闪白。
- 顶部进度条、当前篇名的面包屑、目录抽屉（宽屏是常驻目录，窄屏收成抽屉）。
- 键盘左右键跳上下一卷/下一篇，滚动监听用 `requestAnimationFrame` 节流。
- 卷首与封底：封底有字数、印数与化名声明。

## check_book.py 检查什么

`MISSING` 文件不在 · `TITLE` 首行与 manifest 篇名不符 · `NONAV` 没有导航块 · `BOM`/`CRLF`
编码或换行不干净 · `BAN` 禁词（治愈、内耗、松弛感、岁月静好、人间值得、诗和远方、
在这个快节奏的时代、愿你、不忘初心、仪式感、小确幸）· `STRTQ` 直引号 · `ASCIIQ` 半角
标点 · `TRAD` 混进繁体 · `BLANKS` 三行以上空行 · `DUPPARA` 同篇里出现两遍以上的整段。

行内代码（反引号之间）和抄在正文里的代码片段（`{ ... }`、`[ ... ]`）不参与标点与引号
检查；不含汉字的整行视为代码或表格。地名与人名里的繁体在 `TRAD_OK` 里放行，目前一条：
临安的“於潜”。

## 加一篇、改一篇之后

1. 写或改 `content/vol*/NN-篇名.md`；新增的话在 `manifest.json` 对应卷的 `essays` 里加一条。
2. 跑 `python tools/check_book.py`，把问题清零。
3. 跑对应的 `build_*.py`，看末尾的 `TOTAL CJK` 与 `SHORT`。
4. 如果字数变了，把 `books/<书>/README.md` 目录里那一行的数字改掉（每篇字数、每卷小计、
   顶部“规模”与“字数构成”四处），或者直接重写那个目录块；`check_book.py` 打印的就是
   同一口径的数字，可以直接抄。
