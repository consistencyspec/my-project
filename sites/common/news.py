"""ニュース(ブログのように記事がたまっていくコーナー)の共通部品。2つのサイトで共通。

記事は sites/<サイト>/news/ に、1本ずつ Markdown のファイルで置きます(ファイル名: 日付-英数字.md)。

    ---
    title: 記事のタイトル
    date: 2026-11-07
    summary: 一覧に出す短い説明
    kind: auto(自動の集計) または manual(人が書いた記事)
    ---
    本文(## 見出し、- 箇条書き、| 表 |、**太字**、[リンク](URL) が使えます)

楽天へのリンク(rakuten.co.jp / hb.afl.rakuten.co.jp)には、自動で rel="sponsored" を付けます。
"""
import re
from dataclasses import dataclass, field
from datetime import date
from html import escape
from pathlib import Path

KIND_LABEL = {"auto": "データで見る", "manual": "お知らせ・コラム"}


def e(text):
    return escape(str(text), quote=True)


@dataclass
class Article:
    slug: str
    title: str
    date: date
    summary: str
    kind: str
    body_md: str
    meta: dict = field(default_factory=dict)

    @property
    def path(self):
        return f"/news/{self.slug}/"

    @property
    def date_text(self):
        return f"{self.date.year}年{self.date.month}月{self.date.day}日"


def parse_file(path):
    text = Path(path).read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = m.group(2)
    slug = Path(path).stem
    return Article(slug=slug, title=meta.get("title", slug), date=date.fromisoformat(meta.get("date", slug[:10])),
                   summary=meta.get("summary", ""), kind=meta.get("kind", "manual"), body_md=body.strip(), meta=meta)


def load_articles(folder, today=None):
    """記事を新しい順に返す。日付が未来の記事(予約)は出さない。"""
    folder = Path(folder)
    if not folder.exists():
        return []
    arts = [parse_file(p) for p in folder.glob("*.md") if re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", p.stem)]
    if today:
        arts = [a for a in arts if a.date <= today]
    return sorted(arts, key=lambda a: (a.date, a.slug), reverse=True)


# ---------- Markdown(必要な分だけ) ----------
def _inline(text, resolve=None):
    text = e(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    def link(m):
        label, url = m.group(1), m.group(2)
        if url.startswith("item:"):  # 商品の印。サイトを作るときに最新のリンクに置き換える(販売が終わっていればリンクなし)
            url = resolve(url[5:]) if resolve else None
            if not url:
                return label
        rel = ' rel="nofollow sponsored noopener" target="_blank"' if re.search(r"rakuten\.co\.jp", url) else ""
        return f'<a href="{e(url)}"{rel}>{label}</a>'
    return re.sub(r"\[(.+?)\]\((item:[^\s)]+|https?://[^\s)]+|/[^\s)]*)\)", link, text)


def render_markdown(md, resolve=None):
    out, para, lst, table = [], [], [], []

    def flush():
        nonlocal para, lst, table
        if para:
            out.append("<p>" + "<br>".join(_inline(x, resolve) for x in para) + "</p>")
        if lst:
            out.append("<ul>" + "".join(f"<li>{_inline(x, resolve)}</li>" for x in lst) + "</ul>")
        if table:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table
                    if not re.match(r"^\|?\s*:?-{2,}", r.strip())]
            if rows:
                head = "".join(f"<th>{_inline(c, resolve)}</th>" for c in rows[0])
                body = "".join("<tr>" + "".join(f"<td>{_inline(c, resolve)}</td>" for c in r) + "</tr>" for r in rows[1:])
                out.append(f'<div class="nw-table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        para, lst, table = [], [], []

    for line in md.splitlines():
        s = line.rstrip()
        if not s.strip():
            flush()
        elif s.startswith("### "):
            flush(); out.append(f"<h3>{_inline(s[4:], resolve)}</h3>")
        elif s.startswith("## "):
            flush(); out.append(f"<h2>{_inline(s[3:], resolve)}</h2>")
        elif s.lstrip().startswith("|"):
            if para or lst:
                flush()
            table.append(s)
        elif s.startswith("- "):
            if para or table:
                flush()
            lst.append(s[2:])
        else:
            if lst or table:
                flush()
            para.append(s)
    flush()
    return "\n".join(out)


# ---------- ページの部品 ----------
def news_cards(articles, limit=None):
    items = articles[:limit] if limit else articles
    if not items:
        return '<p class="nw-empty">まだ記事はありません。</p>'
    return '<ul class="nw-list">' + "".join(
        f'<li><a href="{a.path}"><span class="nw-meta"><time datetime="{a.date.isoformat()}">{a.date_text}</time>'
        f'<span class="nw-kind">{KIND_LABEL.get(a.kind, "")}</span></span>'
        f'<span class="nw-title">{e(a.title)}</span><span class="nw-sum">{e(a.summary)}</span></a></li>'
        for a in items) + "</ul>"


def article_html(a, h1_class, newer=None, older=None, resolve=None):
    has_ad = "rakuten.co.jp" in a.body_md or "](item:" in a.body_md
    pr = '<p class="nw-pr">この記事には、楽天アフィリエイトの広告リンク(PR)が含まれます。</p>' if has_ad else ""
    nav = '<nav class="nw-nav">'
    nav += f'<a class="nw-prev" href="{older.path}">← {e(older.title)}</a>' if older else "<span></span>"
    nav += f'<a class="nw-next" href="{newer.path}">{e(newer.title)} →</a>' if newer else "<span></span>"
    nav += "</nav>"
    return f"""<nav class="crumbs"><a href="/">トップ</a> ／ <a href="/news/">ニュース</a> ／ {e(a.title)}</nav>
<article class="nw-article">
<p class="nw-meta"><time datetime="{a.date.isoformat()}">{a.date_text}</time><span class="nw-kind">{KIND_LABEL.get(a.kind, "")}</span></p>
<h1 class="{h1_class} nw-h1">{e(a.title)}</h1>
{pr}
<div class="nw-body">
{render_markdown(a.body_md, resolve)}
</div>
</article>
{nav}
<p class="pager"><a href="/news/">ニュースの一覧へ</a></p>"""


NEWS_CSS = """
/* ニュース */
.nw-list { list-style: none; padding: 0; margin: 0 auto; max-width: 820px; border-top: 1px solid var(--ink); }
.nw-list li { border-bottom: 1px solid var(--rule); }
.nw-list a { display: grid; gap: 4px; padding: 20px 6px; color: var(--ink); text-decoration: none; transition: background .2s; }
.nw-list a:hover { background: var(--bg-2); }
.nw-meta { display: flex; gap: 12px; align-items: center; margin: 0; font-size: .74rem; color: var(--ink-3); letter-spacing: .1em; }
.nw-meta time { font-family: var(--latin); font-size: .86rem; color: var(--ink-2); }
.nw-kind { font-size: .66rem; letter-spacing: .12em; border: 1px solid var(--rule); padding: 0 8px; color: var(--ink-2); }
.nw-title { font-size: 1.02rem; letter-spacing: .08em; line-height: 1.7; }
.nw-sum { font-size: .8rem; color: var(--ink-2); line-height: 1.8; }
.nw-empty { text-align: center; color: var(--ink-2); }
.nw-article { max-width: 760px; margin: 0 auto; }
.nw-article > .nw-meta { justify-content: center; margin-top: 36px; }
.nw-h1 { text-align: center; font-size: 1.6rem; line-height: 1.6; margin: 14px 0 22px; letter-spacing: .12em; }
.nw-pr { text-align: center; font-size: .72rem; color: var(--ink-2); border: 1px solid var(--rule); padding: 6px 10px; }
.nw-body { font-size: .95rem; line-height: 2.1; }
.nw-body h2 { font-size: 1.15rem; font-weight: 500; letter-spacing: .12em; margin: 44px 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--ink); }
.nw-body h3 { font-size: 1rem; font-weight: 500; letter-spacing: .1em; margin: 28px 0 8px; }
.nw-body p, .nw-body li { color: var(--ink); }
.nw-body ul { padding-left: 1.2em; }
.nw-table { overflow-x: auto; margin: 18px 0; }
.nw-table table { width: 100%; border-collapse: collapse; font-size: .82rem; }
.nw-table th, .nw-table td { border-bottom: 1px solid var(--rule); padding: 10px 8px; text-align: left; vertical-align: top; }
.nw-table th { font-weight: 500; color: var(--ink-2); font-size: .74rem; letter-spacing: .1em; border-bottom: 1px solid var(--ink); white-space: nowrap; }
.nw-table td:not(:first-child) { white-space: nowrap; font-family: var(--latin); font-size: .95rem; }
.nw-nav { display: flex; justify-content: space-between; gap: 16px; max-width: 760px; margin: 48px auto 0; padding-top: 18px; border-top: 1px solid var(--rule); font-size: .8rem; }
.nw-nav a { color: var(--ink-2); text-decoration: none; max-width: 48%; }
.nw-nav a:hover { color: var(--ink); }
.nw-next { text-align: right; margin-left: auto; }
@media (max-width: 600px) { .nw-h1 { font-size: 1.3rem; } .nw-body { font-size: .9rem; } }
"""
