#!/usr/bin/env python3
"""data/snapshot.json から、日用品の単価比較サイト(HTML)を dist/tanka/ に作ります。

使い方:
  python3 sites/tanka/build.py                 # 公開用
  python3 sites/tanka/build.py --demo          # ダミーデータで見た目を確認(APIもIDも不要)

公開先のURLは環境変数 TANKA_BASE_URL(例: https://tanka-erabu.com)で指定します。
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import date, datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from unitprice import rank_category, yen_unit  # noqa: E402

sys.path.insert(0, str(ROOT / "sites" / "common"))
from quantity import normalize  # noqa: E402
from reviews import review_html  # noqa: E402
from notfound import not_found_body  # noqa: E402
from hero import hero_html  # noqa: E402
from news import article_html, load_articles, news_cards  # noqa: E402

CSS_VERSION = hashlib.sha1((HERE / "style.css").read_bytes()).hexdigest()[:8]
FONTS = ("https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;600"
         "&family=Cormorant+Garamond:wght@500;600&display=swap")

SORT_JS = """
document.querySelectorAll('[data-controls]').forEach(function (c) {
  c.hidden = false;
  var list = document.querySelector('[data-list]');
  var items = Array.prototype.slice.call(list.children);
  c.addEventListener('change', function () {
    var key = c.querySelector('[data-sort]').value;
    items.sort(function (a, b) {
      if (key === 'price') return a.dataset.price - b.dataset.price;
      if (key === 'reviews') return b.dataset.reviews - a.dataset.reviews;
      return a.dataset.unit - b.dataset.unit;
    }).forEach(function (el) { list.appendChild(el); });
  });
});
"""


def e(text):
    return escape(str(text), quote=True)


def yen(n):
    return f"{n:,}円"


def median(values):
    v = sorted(values)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def sponsored(url):
    return f'href="{e(url)}" rel="nofollow sponsored noopener" target="_blank"'


class Site:
    def __init__(self, config, snapshot, overrides, base_url, today, demo=False):
        self.c = config
        self.base = base_url.rstrip("/")
        self.today = today
        self.demo = demo
        fetched = snapshot.get("fetched_at", "")
        dt = datetime.fromisoformat(fetched) if fetched else None
        self.updated = dt.strftime("%-m月%-d日 %H:%M") if dt else ""
        self.updated_day = dt.strftime("%-m月%-d日") if dt else "今日"
        self.updated_short = dt.strftime("%-m/%-d") if dt else ""
        self.year = today.year
        self.results = {}
        for cat in config["categories"]:
            ranked = rank_category(snapshot.get("categories", {}).get(cat["slug"], []), cat, overrides,
                                   config.get("min_review_count", 5), top=300)
            if len(ranked) >= config.get("min_ranked_to_publish", 3):
                self.results[cat["slug"]] = (cat, ranked)
            else:
                print(f"  - {cat['title']}: 比較できる商品が{len(ranked)}件のため、ページを作りません", file=sys.stderr)
        # 銘柄・容量・種類で絞り込んだページ。3件以上あり、元のページと中身が同じにならないときだけ作る
        self.subpages = {}
        for slug, (cat, ranked) in self.results.items():
            subs = {}
            for sub in cat.get("subpages", []):
                pool = [p for p in ranked if self.matches_sub(p, sub)]
                if len(pool) >= 3 and len(pool) < len(ranked):
                    subs[sub["slug"]] = (sub, pool)
            self.subpages[slug] = subs
        self.groups = []
        for cat, _ in self.results.values():
            if cat["group"] not in self.groups:
                self.groups.append(cat["group"])

    @staticmethod
    def matches_sub(p, sub):
        name = normalize(p.name)
        if sub.get("keywords") and not any(normalize(k) in name for k in sub["keywords"]):
            return False
        if any(normalize(k) in name for k in sub.get("not_keywords", [])):
            return False
        if sub.get("amount"):
            lo, hi = sub["amount"]
            if p.amount < lo or (hi is not None and p.amount > hi):
                return False
        return True

    def news_init(self):
        self.news = load_articles(HERE / "news", self.today)
        self.item_urls = {}
        for slug, (cat, ranked) in self.results.items():
            for p in ranked:
                self.item_urls.setdefault(p.code, p.url)

    def resolve_item(self, code):
        return self.item_urls.get(code)

    def news_index(self):
        body = f"""<h1 class="ch1">ニュース</h1>
<p class="lead">値下がりや変化を、データから自動でまとめた記事と、お知らせです。</p>
{news_cards(self.news)}"""
        return self.layout("/news/", f"ニュース | {self.c['site_name']}", "データから自動でまとめた記事と、お知らせの一覧。", body, current="news")

    def news_page(self, i):
        a = self.news[i]
        newer = self.news[i - 1] if i > 0 else None
        older = self.news[i + 1] if i + 1 < len(self.news) else None
        body = article_html(a, "ch1", newer, older, self.resolve_item)
        return self.layout(a.path, f"{a.title} | {self.c['site_name']}", a.summary, body, current="news")

    def news_section(self):
        if not self.news:
            return ""
        return f"""<h2 class="band"><span>新着ニュース</span></h2>
{news_cards(self.news, 3)}
<p class="pager"><a href="/news/">ニュースの一覧へ</a></p>"""

    # ---------- 共通部品 ----------
    def layout(self, path, title, description, body, noindex=False, current=""):
        canonical = self.base + path
        robots = '<meta name="robots" content="noindex">' if (noindex or self.demo) else ""
        nav = "".join(f'<a class="{"on" if s == current else ""}" href="/{s}/">{e(c["title"])}</a>'
                      for s, (c, _) in self.results.items())
        nav = f'<a class="{"on" if current == "news" else ""}" href="/news/">ニュース</a>' + nav
        demo = '<div class="demo">デモ表示です(ダミーデータ)。公開しないでください。</div>' if self.demo else ""
        return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
{robots}
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{e(self.c['site_name'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/style.css?v={CSS_VERSION}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
</head>
<body>
{demo}
<header class="top"><div class="wrap">
<a class="logo" href="/"><span class="logo-s">日用品を</span><span class="logo-l">単価で<em>えらぶ</em></span></a>
<span class="burst"><span>送料込み<br>で比較</span></span>
<span class="pr-tag">PR<small>広告を含みます</small></span>
</div>
<p class="ticker"><span class="wrap">{e(self.updated)} 更新 ／ 楽天市場の送料込みの商品を、1枚・1L・1kgあたりの値段で毎日くらべています</span></p>
</header>
<nav class="cats"><div class="wrap">{nav}</div></nav>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">
<p class="foot-logo">単価で<em>えらぶ</em></p>
<p class="foot-pr">PR ｜ このサイトは楽天アフィリエイトの広告リンクを使っています。リンク先で購入すると、運営者に紹介料が入ります。</p>
<p><a href="/about/">運営者・計算方法</a> ／ <a href="/privacy/">プライバシーポリシー</a></p>
<p>価格・在庫・送料の条件は変わります。購入する前に、楽天市場の商品ページで最新の内容を確かめてください。</p>
<p>© {self.year} {e(self.c['operator_name'])}</p>
</div></footer>
<script>{SORT_JS}</script>
</body>
</html>
"""

    def price_tag(self, p, cat, size=""):
        return (f'<p class="tag {size}"><span class="tag-k">{e(cat["per"]["label"])}あたり</span>'
                f'<span class="tag-v">{yen_unit(p.unit_price)}<small>円</small></span></p>')

    def card(self, p, cat, rank):
        link = sponsored(p.url)
        img = (f'<img src="{e(p.image)}" alt="" width="160" height="160" loading="lazy">'
               if p.image else '<span class="noimg"></span>')
        if rank <= 3:
            badge = f'<span class="star s{rank}"><small>おすすめ</small><b>{rank}</b><small>位</small></span>'
        else:
            badge = f'<span class="no">{rank}</span>'
        note = f'<p class="note">{e(p.note)}</p>' if p.note else ""
        return f"""<li class="cell" data-unit="{p.unit_price:.4f}" data-price="{p.price}" data-reviews="{p.review_count}">
{badge}<a class="ph" {link}>{img}</a>
<p class="nm"><a {link}>{e(p.short_name)}</a></p>
{self.price_tag(p, cat)}
<p class="sub"><b>{yen(p.price)}</b>(送料込み)で {e(p.amount_text)}</p>
{review_html(p.review_count, p.review_average)}
<p class="meta">{e(p.shop)}</p>{note}
<a class="go" {link}>楽天で見る</a>
</li>"""

    # ---------- 各ページ ----------
    def index(self):
        sections = []
        for g in self.groups:
            cells = []
            for slug, (cat, ranked) in self.results.items():
                if cat["group"] != g:
                    continue
                top = ranked[0]
                img = f'<img src="{e(top.image)}" alt="" width="96" height="96" loading="lazy">' if top.image else ""
                cells.append(f"""<a class="flyer" href="/{slug}/">
<span class="fl-t">{e(cat['title'])}</span>
{img}
{self.price_tag(top, cat, 'big')}
<span class="fl-n">{e(top.short_name[:30])}</span>
<span class="fl-more">ランキングを見る</span>
</a>""")
            sections.append(f'<h2 class="band"><span>{e(g)}</span></h2><div class="flyers">{"".join(cells)}</div>')
        images = {f.name for f in (HERE / "static").iterdir()}
        carousel = hero_html(self.c.get("hero_slides", []), images, self.c.get("hero_brand", ""))
        body = f"""{carousel}
<section class="hero">
<p class="hero-k">{e(self.updated_day)}の 安い単価</p>
<h1>1枚・1Lあたりで、<br class="sp">くらべる。</h1>
<p class="hero-s">楽天市場の日用品を<b>送料込み</b>の値段で集めて、<br class="sp">1枚・1L・1kgあたりの値段が安い順に並べています。毎朝更新。</p>
</section>
{''.join(sections)}
{self.news_section()}
<section class="memo">
<h2 class="band"><span>このサイトのこと</span></h2>
<p>「お得そう」に見える大容量パックも、1枚あたりで割ってみると意外と高いことがあります。このサイトでは、楽天市場の商品のうち<b>送料込みの商品だけ</b>を集めて、商品名に書かれた量で値段を割り、単価の安い順に並べています。</p>
<p>種類や個数を選ぶ商品、量が読み取れない商品は、計算を間違えないように外しています。品質や使い心地の評価ではないので、レビューもあわせて確かめてください。</p>
<p class="sign">運営 {e(self.c['operator_name'])}</p>
</section>"""
        title = f"単価でえらぶ日用品【{self.year}年】水・おむつ・トイレットペーパーを1枚・1Lあたりで比較"
        desc = "楽天市場の日用品を送料込みの値段で集め、1枚・1L・1kgあたりの単価が安い順に毎朝更新。水、おむつ、おしりふき、トイレットペーパー、お米など。"
        return self.layout("/", title, desc, body)

    def list_page(self, path, cat, ranked, name, crumbs, intro, current, extra=""):
        """単価ランキングのページ(品目のページと、絞り込みのページで共通)。"""
        per = cat["per"]["label"]
        top = ranked[0]
        typical = median(p.unit_price for p in ranked)
        cells = "".join(self.card(p, cat, i) for i, p in enumerate(ranked[:30], 1))
        unit_note = f"<li>{e(cat['unit_note'])}</li>" if cat.get("unit_note") else ""
        others = "".join(f'<a href="/{s}/">{e(c["title"])}</a>' for s, (c, _) in self.results.items() if s != cat["slug"])
        body = f"""<nav class="crumbs">{crumbs}</nav>
<h1 class="ch1"><small>{e(self.updated_day)}の</small>{e(name)}<br>単価ランキング</h1>
<p class="verdict">{e(per)}あたり、ふつうは<b>{yen_unit(typical)}円</b>前後。<br>
いちばん安いのは<b class="red">{yen_unit(top.unit_price)}円</b>です。<small>(送料込みの{len(ranked)}件を比較)</small></p>
<p class="lead">{e(intro)}</p>
{extra}
<div class="controls" data-controls hidden>
<label>並び順<select data-sort><option value="unit">{e(per)}あたりが安い順</option><option value="price">値段が安い順</option><option value="reviews">レビューが多い順</option></select></label>
</div>
<ol class="cells" data-list>{cells}</ol>
<section class="memo">
<h2 class="band"><span>数え方</span></h2>
<ul>
<li>{e(per)}あたりの値段＝送料込みの値段÷商品名に書かれた量。{e(self.updated)}時点の値段です。</li>
<li>送料が別にかかる商品、種類や個数を選ぶ商品、量が読み取れない商品は入れていません。</li>
{unit_note}
<li>「送料込み」でも、北海道・沖縄・離島などは送料がかかる場合があります。商品ページで確かめてください。</li>
</ul>
</section>
<p class="pager">ほかの日用品：{others}</p>"""
        title = f"{name}の単価ランキング【{self.year}年】送料込み・{per}あたりで比較"
        desc = (f"楽天市場の{name}を送料込みの値段で集め、{per}あたりの値段で比較。ふつうは{yen_unit(typical)}円、"
                f"いちばん安いのは{yen_unit(top.unit_price)}円。毎朝更新。")
        return self.layout(path, title, desc, body, current=current)

    def sub_links(self, slug, current_sub=None):
        subs = self.subpages.get(slug, {})
        if not subs:
            return ""
        links = "".join(f'<a class="{"on" if ss == current_sub else ""}" href="/{slug}/{ss}/">{e(sub["title"])}</a>'
                        for ss, (sub, _) in subs.items())
        if current_sub:
            links = f'<a href="/{slug}/">すべて</a>' + links
        return f'<p class="subs"><span>しぼりこむ</span>{links}</p>'

    def category(self, slug):
        cat, ranked = self.results[slug]
        return self.list_page(f"/{slug}/", cat, ranked, cat["title"], f'<a href="/">トップ</a> ／ {e(cat["title"])}',
                              cat["intro"], slug, self.sub_links(slug))

    def subpage(self, slug, sub_slug):
        cat, _ = self.results[slug]
        sub, pool = self.subpages[slug][sub_slug]
        intro = sub.get("intro") or (f"{cat['title']}のうち「{sub['title']}」だけを、{cat['per']['label']}あたりの値段で並べました。"
                                     f"{cat['intro']}")
        crumbs = f'<a href="/">トップ</a> ／ <a href="/{slug}/">{e(cat["title"])}</a> ／ {e(sub["title"])}'
        return self.list_page(f"/{slug}/{sub_slug}/", cat, pool, sub["title"], crumbs, intro, slug,
                              self.sub_links(slug, sub_slug))

    def about(self):
        body = f"""<h1 class="ch1">運営者・計算方法</h1>
<section class="memo">
<h2 class="band"><span>運営者</span></h2>
<p>{e(self.c['operator_name'])}<br>お問い合わせ：{e(self.c['contact'])}</p>
<h2 class="band"><span>広告について</span></h2>
<p>このサイトは、楽天グループ株式会社の「楽天アフィリエイト」を使っています。サイトのリンクから楽天市場で購入すると、運営者に紹介料が支払われます。紹介料の有無や金額で、順位を変えることはありません。</p>
<h2 class="band"><span>データと計算方法</span></h2>
<ul>
<li>商品のデータは、楽天ウェブサービスのAPIから毎朝取得しています。</li>
<li>送料込みの商品だけを比べています。ふるさと納税の返礼品は入れていません。</li>
<li>1枚・1L・1kgあたりの値段＝値段÷商品名に書かれた量。</li>
<li>種類や個数を選ぶ商品、量の表記が複数ある商品は、計算を間違えないように外しています。</li>
<li>極端な値(読み取りの誤りの可能性が高いもの)は、自動で外しています。</li>
</ul>
<h2 class="band"><span>免責事項</span></h2>
<p>内容の正確さには気をつけていますが、値段・在庫・送料の条件は変わることがあります。購入する前に、必ず商品ページで確かめてください。</p>
</section>"""
        return self.layout("/about/", f"運営者・計算方法 | {self.c['site_name']}", "運営者情報、広告について、計算方法。", body)

    def privacy(self):
        body = f"""<h1 class="ch1">プライバシーポリシー</h1>
<section class="memo">
<h2 class="band"><span>アフィリエイトについて</span></h2>
<p>このサイトは楽天アフィリエイトを使っています。リンクをクリックすると、楽天グループ株式会社がCookieなどで紹介の成果を記録することがあります。くわしくは楽天グループ株式会社のプライバシーポリシーをご覧ください。</p>
<h2 class="band"><span>アクセス解析について</span></h2>
<p>このサイトでは、閲覧数などを知るために、Cloudflare, Inc.の「Cloudflare Web Analytics」を使っています。Cookieは使わず、閲覧者を特定できる情報も集めていません。集めるのは、見られたページ、参照元、ブラウザや端末の種類、おおまかな国・地域などの統計情報です。くわしくは<a href="https://www.cloudflare.com/ja-jp/privacypolicy/" rel="noopener" target="_blank">Cloudflareのプライバシーポリシー</a>をご覧ください。</p>
<h2 class="band"><span>個人情報について</span></h2>
<p>お問い合わせでいただいた個人情報は、お返事のためだけに使い、法令にもとづく場合を除いて第三者に渡しません。</p>
<p>制定日：{self.today.isoformat()}</p>
</section>"""
        return self.layout("/privacy/", f"プライバシーポリシー | {self.c['site_name']}", "プライバシーポリシー。", body)

    def not_found(self):
        links = [("/", "トップページ")] + [(f"/{sl}/", c["title"]) for sl, (c, _) in self.results.items()]
        body = not_found_body("ch1", links, ("https://furusato-yosan.com/", "ふるさと納税の予算別の比較"))
        return self.layout("/404.html", "ページが見つかりません", "ページが見つかりません。", body, noindex=True)

    def build(self, out):
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        self.news_init()
        pages = {"index.html": self.index(), "about/index.html": self.about(),
                 "privacy/index.html": self.privacy(), "404.html": self.not_found()}
        for slug in self.results:
            pages[f"{slug}/index.html"] = self.category(slug)
            for ss in self.subpages[slug]:
                pages[f"{slug}/{ss}/index.html"] = self.subpage(slug, ss)
        pages["news/index.html"] = self.news_index()
        for i, a in enumerate(self.news):
            pages[f"news/{a.slug}/index.html"] = self.news_page(i)
        for rel, html in pages.items():
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(html, encoding="utf-8")
        shutil.copy(HERE / "style.css", out / "style.css")
        for f in (HERE / "static").iterdir():  # ファビコンなど
            shutil.copy(f, out / f.name)
        urls = (["/"] + [f"/{s}/" for s in self.results]
                + [f"/{s}/{ss}/" for s in self.results for ss in self.subpages[s]] + ["/news/"] + [a.path for a in self.news] + ["/about/"])
        sitemap = "".join(f"<url><loc>{e(self.base + u)}</loc><lastmod>{self.today.isoformat()}</lastmod></url>"
                          for u in urls)
        (out / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{sitemap}</urlset>\n", encoding="utf-8")
        robots = "User-agent: *\nDisallow: /\n" if self.demo else f"User-agent: *\nAllow: /\nSitemap: {self.base}/sitemap.xml\n"
        (out / "robots.txt").write_text(robots, encoding="utf-8")
        return len(pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="ダミーデータ(sample_snapshot.json)で作る")
    ap.add_argument("--out", default=str(ROOT / "dist" / "tanka"), help="出力先のフォルダ")
    ap.add_argument("--today", help="日付を指定する(テスト用、例: 2026-11-03)")
    args = ap.parse_args()

    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    snap_path = HERE / ("sample_snapshot.json" if args.demo else "data/snapshot.json")
    if not snap_path.exists():
        sys.exit(f"{snap_path.relative_to(ROOT)} がありません。先に fetch.py を実行してください(試すだけなら --demo)。")
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    overrides = json.loads((HERE / "overrides.json").read_text(encoding="utf-8"))
    overrides = {k: v for k, v in overrides.items() if not k.startswith("_")}
    base_url = os.environ.get(config["base_url_env"], "").strip() or config["base_url_default"]
    today = date.fromisoformat(args.today) if args.today else date.today()

    site = Site(config, snapshot, overrides, base_url, today, demo=args.demo)
    if not site.results:
        sys.exit("公開できるカテゴリがありません。")
    n = site.build(Path(args.out))
    print(f"{n}ページを作りました: {args.out}")


if __name__ == "__main__":
    main()
