# 山水有信 · 山水有回信

两本散文集，作者林深。都是私人印本，不售卖，也不上架；这里放的是全文，供自己留档，也供认识的读者点开就读。

| | |
|---|---|
| 书名 | 《山水有信》· 写给日常的长信 |
| 版本 | 私人印本 · 二〇二六年十一月印三百册 |
| 规模 | 六卷四十八篇，约 208,045 字（序 3,196 · 正文 202,943 · 后记 1,906） |
| 阅读 | [全书目录](books/shanshui-youxin/README.md) · [单文件版](dist/shanshui-youxin.html) |

| | |
|---|---|
| 书名 | 《山水有回信》· 写给往后的日子 |
| 版本 | 私人印本 · 二〇二七年（第一本寄出以后写的） |
| 规模 | 六卷五十四篇，约 244,317 字（序 2,119 · 正文 240,020 · 后记 2,178） |
| 阅读 | [全书目录](books/shanshui-youhui/README.md) · [单文件版](dist/shanshui-youhui.html) |

## 这两本写的是什么

第一本写的是把日子慢下来的那一年：早上六点四十的回收喇叭、一碗面的时间、阳台上的一场雨、山里的一个没有信号的周末，以及楼下的早餐店、修伞的人、夜班的司机。四十八篇，每篇都是一件具体的事，价钱、时间、手上的伤都写在里面。

第二本从第一本印出来那天写起。书寄出去三百册，回信一封一封到了：沈阳的退休调度、合肥的护士、常山的高中生、深圳的程序员。这一卷里我在杭州租下带院子的房，量房子、挪树、跟工人一起排工期；母亲做了白内障手术，父亲在电话里问我一只表的上油钱；修表的老许把一只没人领的钟卖给我，交代了一句上弦的时候人在就好。卷五写的是巷子里那些把名字借给我的人，他们用的是化名。五十四篇比四十八篇多出百分之十七，不是加长，是这一年发生的事比上一年多。

写的全是普通人的普通日子，没有奇事。谁读着觉得像自己，那就像自己。

## 怎么读

- **在 GitHub 上直接读**：点上面任意一本的“全书目录”，每篇是独立的 Markdown，篇末有上一篇、下一篇和回目录的跳转。
- **下载一本读**：[dist/shanshui-youxin.html](dist/shanshui-youxin.html) 与 [dist/shanshui-youhui.html](dist/shanshui-youhui.html)，各自一个文件，封面与六卷插图都在里面，双击就能在浏览器打开，也能拷进手机。夜间模式、三档字号、目录抽屉、进度条都在，不需要联网。
- **开个网页读**：仓库设置里 Pages 选 Deploy from a branch，目录选 `/dist`，就会得到 `https://<用户名>.github.io/<仓库名>/`，落地页是 [dist/index.html](dist/index.html)。

## 仓库结构

```
books/shanshui-youxin/    《山水有信》：manifest.json + content/（序 + 48 篇 + 后记）+ assets/
books/shanshui-youhui/    《山水有回信》：同一套结构，正文 54 篇
dist/                     两本书的单文件 HTML 与一个落地页，给 Pages 用
tools/                    排版脚本、体例检查、链接检查
docs/                     写作规矩、校对记录、名字与插图说明；drafts/ 是当时的备忘与扫描日志
```

正文的文件名是“编号-篇名.md”，例如 `content/vol4/02-表停了.md`；卷号在目录名里（`vol1`…`vol6`），顺序就是书的阅读顺序。`manifest.json` 里有每篇的篇名、路径、卷的题辞与插图说明，是排版脚本的唯一依据。

## 重排与检查

```bash
pip install -r requirements.txt        # 只需要 markdown-it-py
python tools/build_shanshui_youxin.py  # → dist/shanshui-youxin.html
python tools/build_shanshui_youhui.py  # → dist/shanshui-youhui.html
python tools/check_book.py             # 体例、标点、繁简、重复段检查，有问题时退出码 1
python tools/check_links.py            # 目录页与 README 的链接是否都还在
```

两个脚本输出的 HTML 与仓库里现成的 `dist/` 完全一致（逐字节比对过）。改稿之后重跑一遍即可，不需要手工搬动任何文字。详见 [tools/README.md](tools/README.md)。

## 想看看这些书是怎么做的

[docs/writing-notes.md](docs/writing-notes.md)（写作规矩与全书口径）·
[docs/qa-report.md](docs/qa-report.md)（校对记录，包括通读时抓出的十一处硬伤）·
[docs/names-and-images.md](docs/names-and-images.md)（化名、细节改动与插图流程）·
[docs/drafts/](docs/drafts/)（开工前的备忘、分卷提纲、当时的扫描日志，原样放着）

## 关于名字、插图与版权

书里的人是真实的，伞铺的老金、缝纫机的阿珍、送奶的老蒋、修表的老许、打印店的小吕，他们的名字是我借来的，化名与细节处理的范围写在 [docs/names-and-images.md](docs/names-and-images.md)。封面与卷首插图由 AI 生成，再裁切调色。

文本与图片的版权保留，未经许可请勿转载、改编或用于任何商业用途（含投喂模型与朗读带货）。详见 [LICENSE](LICENSE)。要读可以，直接把这个仓库的链接发给别人就行。

二〇二六年十月，杭州。
