#!/usr/bin/env python3
"""data/snapshot.json から、静的サイト(HTML)を dist/furusato/ に作ります。

使い方:
  python3 sites/furusato/build.py                 # 公開用
  python3 sites/furusato/build.py --demo          # ダミーデータで見た目を確認(APIもIDも不要)

公開先のURLは環境変数 FURUSATO_BASE_URL(例: https://furusato-cospa.com)で指定します。
"""
import argparse
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

from rank import per10k_text, rank_category  # noqa: E402

FAMILY_UNIT = {"weight": "kg", "volume": "L", "roll": "ロール", "box": "箱"}


def e(text):
    return escape(str(text), quote=True)


def yen(n):
    return f"{n:,}円"


class Site:
    def __init__(self, config, snapshot, overrides, base_url, today, demo=False):
        self.c = config
        self.snap = snapshot
        self.overrides = overrides
        self.base = base_url.rstrip("/")
        self.today = today
        self.demo = demo
        fetched = snapshot.get("fetched_at", "")
        self.updated = datetime.fromisoformat(fetched).strftime("%Y年%-m月%-d日 %H:%M") if fetched else ""
        self.year = today.year
        m, d = (int(x) for x in config["deadline_month_day"].split("-"))
        self.days_left = (date(today.year, m, d) - today).days
        self.results = {}
        for cat in config["categories"]:
            ranked, popular = rank_category(snapshot.get("categories", {}).get(cat["slug"], []), cat, overrides,
                                            config.get("min_review_count", 10))
            if len(ranked) >= config.get("min_ranked_to_publish", 3):
                self.results[cat["slug"]] = (cat, ranked, popular)
            else:
                print(f"  - {cat['title']}: 比較できる返礼品が{len(ranked)}件のため、ページを作りません", file=sys.stderr)

    # ---------- 共通部品 ----------
    def layout(self, path, title, description, body, noindex=False):
        canonical = self.base + path
        robots = '<meta name="robots" content="noindex">' if (noindex or self.demo) else ""
        nav = "".join(f'<a href="/{slug}/">{e(cat["title"])}</a>' for slug, (cat, _, _) in self.results.items())
        demo = '<div class="demo">⚠️ デモ表示です(ダミーデータ)。公開しないでください。</div>' if self.demo else ""
        return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
{robots}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{e(self.c['site_name'])}">
<link rel="stylesheet" href="/style.css">
</head>
<body>
{demo}
<header class="site-header"><div class="wrap">
<a class="logo" href="/">{e(self.c['site_name'])}</a>
<nav class="cats">{nav}</nav>
</div></header>
<div class="pr-bar"><div class="wrap">当サイトは楽天アフィリエイト(広告)を利用しています。リンク先で寄付すると、運営者に紹介料が入ります。</div></div>
<main class="wrap">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p><a href="/about/">運営者情報・計算方法</a> ・ <a href="/privacy/">プライバシーポリシー</a></p>
<p>寄付額・在庫・内容は変わることがあります。お申し込みの前に、必ず楽天ふるさと納税の返礼品ページで最新の内容を確認してください。</p>
<p>© {self.year} {e(self.c['site_name'])}</p>
</div></footer>
</body>
</html>
"""

    def gift_card(self, g, family, rank=None):
        badge = f'<span class="rank rank-{rank}">{rank}</span>' if rank else ""
        img = (f'<img src="{e(g.image)}" alt="{e(g.short_name)}" width="120" height="120" loading="lazy">'
               if g.image else '<div class="noimg"></div>')
        stars = f"★{g.review_average:.2f}({g.review_count:,}件)" if g.review_count else "レビューなし"
        if g.per10k is not None:
            metric = (f'<div class="metric"><span class="label">1万円あたり</span>'
                      f'<span class="value">{e(per10k_text(g, family))}</span></div>'
                      f'<div class="facts">寄付額 {yen(g.price_min)} / 量 {e(g.amount_text)}</div>')
        else:
            price = yen(g.price_min) if g.price_min == g.price_max else f"{yen(g.price_min)}〜{yen(g.price_max)}"
            metric = f'<div class="facts">寄付額 {price}(容量・回数で変わります)</div>'
        note = f'<div class="note">{e(g.note)}</div>' if g.note else ""
        return f"""<article class="gift">
{badge}<a class="thumb" href="{e(g.url)}" rel="nofollow sponsored noopener" target="_blank">{img}</a>
<div class="body">
<h3><a href="{e(g.url)}" rel="nofollow sponsored noopener" target="_blank">{e(g.short_name)}</a></h3>
<div class="shop">{e(g.shop)} ・ {e(stars)}</div>
{metric}{note}
<a class="btn" href="{e(g.url)}" rel="nofollow sponsored noopener" target="_blank">楽天で見る(PR)</a>
</div>
</article>"""

    def deadline_text(self):
        if self.days_left < 0:
            return ""
        return (f'<p class="deadline">{self.year}年分のふるさと納税の締め切り(12月31日)まで、'
                f'<strong>あと{self.days_left}日</strong>です。</p>')

    # ---------- 各ページ ----------
    def index(self):
        cards = []
        for slug, (cat, ranked, _) in self.results.items():
            top = ranked[0]
            cards.append(f"""<a class="cat-card" href="/{slug}/">
<h2>{e(cat['title'])}</h2>
<p class="top">1位:{e(per10k_text(top, cat['family']))}/1万円</p>
<p class="small">{e(top.shop)} ・ {e(top.short_name[:28])}</p>
<span class="more">ランキングを見る →</span>
</a>""")
        body = f"""<section class="hero">
<h1>ふるさと納税、1万円あたりで比べると?</h1>
<p>{e(self.c['tagline'])}。楽天ふるさと納税の人気返礼品を、<strong>寄付額1万円あたりに届く量</strong>で並べています。</p>
{self.deadline_text()}
<p class="updated">データ更新:{e(self.updated)}(毎日自動で更新)</p>
</section>
<section class="cat-grid">{''.join(cards)}</section>
<section class="howto">
<h2>このサイトの見方</h2>
<ul>
<li><strong>1万円あたりの量</strong> = 返礼品の量 ÷ 寄付額 × 10,000 で計算しています。</li>
<li>商品名から量をはっきり読み取れた返礼品だけを比べています。容量や回数を選べる返礼品は、寄付額と量の組み合わせが分からないため、別の一覧にしています。</li>
<li>レビューが{self.c.get('min_review_count', 10)}件未満の返礼品は載せていません。</li>
<li>量が多いことと、品質や味の良さは別です。レビューや発送時期もあわせて確認してください。</li>
</ul>
<p><a href="/about/">計算方法と注意点をくわしく見る</a></p>
</section>"""
        title = f"ふるさと納税コスパ比較【{self.year}年】1万円あたりの量ランキング"
        desc = "楽天ふるさと納税の人気返礼品(お米・肉・日用品など)を、寄付額1万円あたりに届く量で比較。毎日自動更新。"
        return self.layout("/", title, desc, body)

    def category(self, slug):
        cat, ranked, popular = self.results[slug]
        family = cat["family"]
        unit = FAMILY_UNIT[family]
        top = ranked[0]
        rank_cards = "".join(self.gift_card(g, family, i) for i, g in enumerate(ranked, 1))
        pop_cards = "".join(self.gift_card(g, family) for g in popular)
        unit_note = f"<li>{e(cat['unit_note'])}</li>" if cat.get("unit_note") else ""
        others = "".join(f'<li><a href="/{s}/">{e(c["title"])}</a></li>'
                         for s, (c, _, _) in self.results.items() if s != slug)
        body = f"""<nav class="crumbs"><a href="/">トップ</a> › {e(cat['title'])}</nav>
<h1>ふるさと納税 {e(cat['title'])}のコスパランキング【{self.year}年】</h1>
<p class="updated">データ更新:{e(self.updated)} ・ 比較した返礼品:{len(ranked)}件</p>
<p class="lead">{e(cat['intro'])}</p>
<div class="summary">
いま1万円あたりの量がいちばん多いのは、<strong>{e(top.shop)}の「{e(top.short_name[:30])}」</strong>で、
1万円あたり<strong>{e(per10k_text(top, family))}</strong>(寄付額{yen(top.price_min)}で{e(top.amount_text)})です。
</div>
{self.deadline_text()}
<h2>1万円あたりの量ランキング({e(unit)})</h2>
<div class="gifts">{rank_cards}</div>
<h2>容量・回数を選べる人気の返礼品(レビューが多い順)</h2>
<p class="small">寄付額によって量が変わるため、ランキングには入れていません。量ごとの寄付額は、返礼品のページで確認してください。</p>
<div class="gifts">{pop_cards}</div>
<section class="howto">
<h2>計算方法と注意点</h2>
<ul>
<li>1万円あたりの量 = 商品名に書かれた量 ÷ 寄付額 × 10,000。</li>
{unit_note}
<li>「約5kg」のように「約」が付く返礼品も、書かれた数字で計算しています。</li>
<li>寄付額・内容は{e(self.updated)}時点のものです。申し込む前に返礼品のページで確認してください。</li>
</ul>
</section>
<section><h2>ほかのジャンル</h2><ul class="others">{others}</ul></section>"""
        title = f"ふるさと納税 {cat['title']} コスパランキング【{self.year}年】1万円あたりの量で比較"
        desc = (f"楽天ふるさと納税の{cat['title']}を、寄付額1万円あたりの量で比較。"
                f"現在の1位は1万円あたり{per10k_text(top, family)}。毎日自動更新。")
        return self.layout(f"/{slug}/", title, desc, body)

    def about(self):
        body = f"""<h1>運営者情報・計算方法</h1>
<h2>運営者</h2>
<p>{e(self.c['operator_name'])}</p>
<p>お問い合わせ:{e(self.c['contact'])}</p>
<h2>広告について</h2>
<p>当サイトは、楽天グループ株式会社の「楽天アフィリエイト」を利用しています。当サイトのリンクから楽天ふるさと納税で寄付をすると、運営者に紹介料が支払われます。紹介料の有無や金額によって、ランキングの順位を変えることはありません。</p>
<h2>データと計算方法</h2>
<ul>
<li>返礼品のデータは、楽天ウェブサービスのAPIから毎日自動で取得しています。</li>
<li>1万円あたりの量 = 商品名に書かれた量 ÷ 寄付額 × 10,000 で計算します。</li>
<li>容量・回数を選べる返礼品、定期便、量の表記が複数ある返礼品は、計算の誤りを防ぐため、ランキングに入れていません。</li>
<li>極端な値(読み取りの誤りの可能性が高いもの)は、自動で除外しています。</li>
<li>量の多さは、品質・味・使いやすさを表すものではありません。</li>
</ul>
<h2>免責事項</h2>
<p>掲載内容の正確さには注意していますが、寄付額・在庫・内容は変わることがあります。お申し込みの前に、必ず返礼品のページで最新の内容を確認してください。控除の上限額は、収入や家族構成によって変わります。くわしくは<a href="https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/deduction.html" rel="noopener" target="_blank">総務省 ふるさと納税ポータルサイト</a>を確認してください。</p>"""
        return self.layout("/about/", f"運営者情報・計算方法 | {self.c['site_name']}", "当サイトの運営者情報、広告について、計算方法。", body)

    def privacy(self):
        body = f"""<h1>プライバシーポリシー</h1>
<h2>アフィリエイトについて</h2>
<p>当サイトは楽天アフィリエイトを利用しています。リンクをクリックすると、楽天グループ株式会社がCookieなどを使って、紹介の成果を記録することがあります。くわしくは楽天グループ株式会社のプライバシーポリシーを確認してください。</p>
<h2>アクセス解析について</h2>
<p>当サイトでは、現在アクセス解析ツールを使っていません。使い始めるときは、このページでお知らせします。</p>
<h2>個人情報について</h2>
<p>お問い合わせでいただいた個人情報は、お返事のためだけに使い、法令にもとづく場合を除いて第三者に提供しません。</p>
<p>制定日:{self.today.isoformat()}</p>"""
        return self.layout("/privacy/", f"プライバシーポリシー | {self.c['site_name']}", "当サイトのプライバシーポリシー。", body)

    def not_found(self):
        return self.layout("/404.html", "ページが見つかりません", "ページが見つかりません。",
                           '<h1>ページが見つかりません</h1><p><a href="/">トップページへ</a></p>', noindex=True)

    def build(self, out):
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        pages = {"index.html": self.index(), "about/index.html": self.about(),
                 "privacy/index.html": self.privacy(), "404.html": self.not_found()}
        for slug in self.results:
            pages[f"{slug}/index.html"] = self.category(slug)
        for rel, html in pages.items():
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(html, encoding="utf-8")
        shutil.copy(HERE / "style.css", out / "style.css")
        urls = ["/"] + [f"/{s}/" for s in self.results] + ["/about/"]
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
    ap.add_argument("--out", default=str(ROOT / "dist" / "furusato"), help="出力先のフォルダ")
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

    for key in ("operator_name", "contact"):
        if "ここに" in config[key] and not args.demo:
            print(f"  ! config.json の {key} がまだ書き換えられていません(運営者情報のページに表示されます)", file=sys.stderr)
    if base_url == config["base_url_default"] and not args.demo:
        print(f"  ! 環境変数 {config['base_url_env']} が未設定です。公開URLが仮のままです", file=sys.stderr)

    site = Site(config, snapshot, overrides, base_url, today, demo=args.demo)
    if not site.results:
        sys.exit("公開できるカテゴリがありません。")
    n = site.build(Path(args.out))
    print(f"{n}ページを作りました: {args.out}")


if __name__ == "__main__":
    main()
