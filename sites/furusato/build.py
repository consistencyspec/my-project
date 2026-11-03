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
UNIT_DIV = {"weight": 1000, "volume": 1000, "roll": 1, "box": 1}
PRICE_BANDS = [(0, 10000, "1万円まで"), (10001, 20000, "2万円まで"), (20001, 30000, "3万円まで"),
               (30001, 10**9, "3万円より上")]

# 並び替え・絞り込み(JavaScriptが動かない環境では、量が多い順のまま表示される)
SORT_JS = """
document.querySelectorAll('[data-controls]').forEach(function (c) {
  c.hidden = false;
  var list = document.querySelector('[data-list]'), empty = document.querySelector('[data-empty]');
  var items = Array.prototype.slice.call(list.children);
  function apply() {
    var key = c.querySelector('[data-sort]').value, cap = +c.querySelector('[data-cap]').value, shown = 0;
    items.sort(function (a, b) {
      if (key === 'price') return a.dataset.price - b.dataset.price;
      if (key === 'reviews') return b.dataset.reviews - a.dataset.reviews;
      return b.dataset.per - a.dataset.per;
    }).forEach(function (el) {
      var ok = !cap || +el.dataset.price <= cap;
      el.hidden = !ok; if (ok) shown++;
      list.appendChild(el);
    });
    empty.hidden = shown > 0;
  }
  c.addEventListener('change', apply);
});
"""


def median(values):
    v = sorted(values)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def fmt_per(value, family):
    unit = FAMILY_UNIT[family]
    if family in ("roll", "box"):
        return f"{value:,.0f}{unit}"
    return (f"{value:.1f}" if value < 100 else f"{value:,.0f}") + unit


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
    def layout(self, path, title, description, body, noindex=False, current=""):
        canonical = self.base + path
        robots = '<meta name="robots" content="noindex">' if (noindex or self.demo) else ""
        chips = "".join(
            f'<a class="chip{" on" if slug == current else ""}" href="/{slug}/">'
            f'<span aria-hidden="true">{cat.get("icon", "")}</span>{e(cat["title"])}</a>'
            for slug, (cat, _, _) in self.results.items())
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
<meta name="theme-color" content="#14532d">
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
<a class="logo" href="/"><span class="logo-sub">楽天ふるさと納税</span><span class="logo-main">1万円で<em>どれだけ届く？</em></span></a>
<p class="logo-note">データ更新 {e(self.updated)}</p>
</div></header>
<div class="pr-bar"><div class="wrap">本ページはプロモーション(広告)を含みます。リンク先で寄付すると、運営者に紹介料が入ります。</div></div>
<nav class="chips"><div class="wrap">{chips}</div></nav>
<main class="wrap">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p><a href="/about/">運営者情報・計算方法</a> ・ <a href="/privacy/">プライバシーポリシー</a></p>
<p>寄付額・在庫・内容は変わることがあります。お申し込みの前に、必ず楽天ふるさと納税の返礼品ページで最新の内容を確認してください。</p>
<p>© {self.year} {e(self.c['site_name'])}</p>
</div></footer>
<script>{SORT_JS}</script>
</body>
</html>
"""

    def gift_card(self, g, family, median=None, rank=None):
        unit = FAMILY_UNIT[family]
        link = f'href="{e(g.url)}" rel="nofollow sponsored noopener" target="_blank"'
        img = (f'<img src="{e(g.image)}" alt="{e(g.short_name)}" width="140" height="140" loading="lazy">'
               if g.image else '<div class="noimg"></div>')
        stars = (f'<span class="stars">★ {g.review_average:.1f}</span><span class="muted">({g.review_count:,}件)</span>'
                 if g.review_count else '<span class="muted">レビューなし</span>')
        if g.per10k is None:
            price = yen(g.price_min) if g.price_min == g.price_max else f"{yen(g.price_min)}〜{yen(g.price_max)}"
            return f"""<article class="gift plain">
<a class="thumb" {link}>{img}</a>
<div class="body">
<p class="shop">{e(g.shop)}</p>
<h3><a {link}>{e(g.short_name)}</a></h3>
<p class="rev">{stars}</p>
<p class="price-range">寄付額 <strong>{price}</strong><span class="muted">(容量・回数で変わります)</span></p>
<a class="btn" {link}>楽天で寄付する(PR)</a>
</div>
</article>"""
        ratio = g.per10k / median if median else 1
        tier = "gold" if ratio >= 1.3 else ("good" if ratio >= 1.0 else "base")
        ratio_text = f"真ん中の{ratio:.1f}倍" if median else ""
        per_unit_amount = g.amount / UNIT_DIV[family]
        per_unit_price = g.price_min / per_unit_amount
        badge = f'<span class="rank r{min(rank, 4)}">{rank}<small>位</small></span>' if rank else ""
        note = f'<p class="note">{e(g.note)}</p>' if g.note else ""
        return f"""<article class="gift tier-{tier}" data-per="{g.per10k:.4f}" data-price="{g.price_min}" data-reviews="{g.review_count}">
{badge}
<div class="gift-main">
<a class="thumb" {link}>{img}</a>
<div class="body">
<p class="shop">{e(g.shop)}</p>
<h3><a {link}>{e(g.short_name)}</a></h3>
<p class="rev">{stars}</p>
</div>
</div>
<div class="gift-data">
<div class="metric">
<span class="label">1万円あたり</span>
<span class="value">{e(per10k_text(g, family))}</span>
<span class="ratio">{e(ratio_text)}</span>
</div>
<dl class="facts">
<div><dt>寄付額</dt><dd><strong>{yen(g.price_min)}</strong></dd></div>
<div><dt>内容量</dt><dd>{e(g.amount_text)}</dd></div>
<div><dt>1{e(unit)}あたり</dt><dd>{yen(round(per_unit_price))}</dd></div>
</dl>
</div>
{note}
<a class="btn" {link}>楽天で寄付する(PR)</a>
</article>"""

    def deadline_box(self):
        if self.days_left < 0:
            return ""
        return (f'<div class="deadline"><span class="dl-label">{self.year}年分の締め切り 12月31日まで</span>'
                f'<span class="dl-days">あと<strong>{self.days_left}</strong>日</span></div>')

    # ---------- 各ページ ----------
    def index(self):
        cards = []
        for slug, (cat, ranked, _) in self.results.items():
            top = ranked[0]
            med = median(g.per10k for g in ranked)
            cards.append(f"""<a class="cat-card" href="/{slug}/">
<span class="cat-icon" aria-hidden="true">{cat.get('icon', '')}</span>
<span class="cat-title">{e(cat['title'])}</span>
<span class="cat-top"><small>1位</small> {e(per10k_text(top, cat['family']))}<small>/1万円</small></span>
<span class="cat-med">真ん中 {e(fmt_per(med, cat['family']))} ・ {len(ranked)}件を比較</span>
</a>""")
        body = f"""<section class="hero">
<h1>ふるさと納税は<br class="sp">「1万円あたりの量」で選ぶ</h1>
<p>楽天ふるさと納税の人気返礼品を、<strong>寄付額1万円あたりに届く量</strong>で比べています。お米なら何kg、トイレットペーパーなら何ロール届くかが、ひと目で分かります。</p>
{self.deadline_box()}
</section>
<h2 class="sec">ジャンルを選ぶ</h2>
<section class="cat-grid">{''.join(cards)}</section>
<section class="howto">
<h2 class="sec">このサイトの見方</h2>
<ol class="steps">
<li><strong>1万円あたりの量</strong> = 返礼品の量 ÷ 寄付額 × 10,000。寄付額がちがう返礼品どうしでも、同じものさしで比べられます。</li>
<li><strong>「真ん中の◯倍」</strong>は、そのジャンルで比べた返礼品の真ん中(中央値)と比べて、何倍届くかです。</li>
<li>商品名から量をはっきり読み取れた返礼品だけを比べています。容量や回数を選べる返礼品は、別の一覧にしています。</li>
<li>レビューが{self.c.get('min_review_count', 10)}件未満の返礼品は載せていません。量の多さと、味や品質の良さは別なので、レビューもあわせて確認してください。</li>
</ol>
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
        med = median(g.per10k for g in ranked)
        rank_cards = "".join(self.gift_card(g, family, med, i) for i, g in enumerate(ranked, 1))
        pop_cards = "".join(self.gift_card(g, family) for g in popular)
        bands = []
        for lo, hi, label in PRICE_BANDS:
            pool = [g for g in ranked if lo <= g.price_min <= hi]
            if pool:
                b = max(pool, key=lambda g: g.per10k)
                bands.append(f"""<a class="band" href="{e(b.url)}" rel="nofollow sponsored noopener" target="_blank">
<span class="band-label">{label}</span>
<span class="band-value">{e(per10k_text(b, family))}<small>/1万円</small></span>
<span class="band-name">{e(b.shop)}・{e(b.short_name[:22])}</span>
<span class="band-price">寄付額 {yen(b.price_min)}(PR)</span>
</a>""")
        unit_note = f"<li>{e(cat['unit_note'])}</li>" if cat.get("unit_note") else ""
        others = "".join(f'<li><a href="/{s}/">{c.get("icon", "")} {e(c["title"])}</a></li>'
                         for s, (c, _, _) in self.results.items() if s != slug)
        body = f"""<nav class="crumbs"><a href="/">トップ</a> › {e(cat['title'])}</nav>
<h1><span aria-hidden="true">{cat.get('icon', '')}</span> ふるさと納税 {e(cat['title'])}のコスパランキング【{self.year}年】</h1>
<p class="lead">{e(cat['intro'])}</p>
<section class="stats">
<div class="stat main"><span class="k">いちばん多い</span><span class="v">{e(per10k_text(top, family))}</span><span class="s">1万円あたり</span></div>
<div class="stat"><span class="k">真ん中</span><span class="v">{e(fmt_per(med, family))}</span><span class="s">1万円あたり</span></div>
<div class="stat"><span class="k">比べた返礼品</span><span class="v">{len(ranked)}<small>件</small></span><span class="s">{e(self.updated)}時点</span></div>
</section>
<p class="summary">いま1万円あたりの量がいちばん多いのは、<strong>{e(top.shop)}の「{e(top.short_name[:30])}」</strong>です。寄付額{yen(top.price_min)}で{e(top.amount_text)}届き、真ん中の返礼品の<strong>{top.per10k / med:.1f}倍</strong>の量です。</p>
{self.deadline_box()}
<h2 class="sec">寄付額ごとの「いちばん量が多い」返礼品</h2>
<p class="small">控除の上限が少ない人や、ほかの返礼品と組み合わせたい人は、寄付額の枠で選ぶと便利です。</p>
<section class="bands">{''.join(bands)}</section>
<h2 class="sec" id="ranking">1万円あたりの量ランキング({e(unit)})</h2>
<div class="controls" data-controls hidden>
<label>並び替え<select data-sort>
<option value="per">量が多い順</option><option value="price">寄付額が安い順</option><option value="reviews">レビューが多い順</option>
</select></label>
<label>寄付額の上限<select data-cap>
<option value="0">上限なし</option><option value="10000">1万円まで</option><option value="20000">2万円まで</option><option value="30000">3万円まで</option>
</select></label>
</div>
<p class="legend"><span class="lg gold">真ん中の1.3倍以上</span><span class="lg good">真ん中以上</span><span class="lg base">真ん中より少ない</span></p>
<div class="gifts" data-list>{rank_cards}</div>
<p class="empty" data-empty hidden>この条件に合う返礼品はありません。寄付額の上限を広げてください。</p>
<h2 class="sec">容量・回数を選べる人気の返礼品</h2>
<p class="small">寄付額によって量が変わるため、ランキングには入れていません(レビューが多い順)。量ごとの寄付額は、返礼品のページで確認してください。</p>
<div class="gifts">{pop_cards}</div>
<section class="howto">
<h2 class="sec">計算方法と注意点</h2>
<ul>
<li>1万円あたりの量 = 商品名に書かれた量 ÷ 寄付額 × 10,000。「真ん中」は比べた返礼品の中央値です。</li>
{unit_note}
<li>「約5kg」のように「約」が付く返礼品も、書かれた数字で計算しています。</li>
<li>寄付額・内容は{e(self.updated)}時点のものです。申し込む前に返礼品のページで確認してください。</li>
</ul>
</section>
<section><h2 class="sec">ほかのジャンル</h2><ul class="others">{others}</ul></section>"""
        title = f"ふるさと納税 {cat['title']} コスパランキング【{self.year}年】1万円あたりの量で比較"
        desc = (f"楽天ふるさと納税の{cat['title']}を、寄付額1万円あたりの量で比較。"
                f"現在の1位は1万円あたり{per10k_text(top, family)}。毎日自動更新。")
        return self.layout(f"/{slug}/", title, desc, body, current=slug)

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
