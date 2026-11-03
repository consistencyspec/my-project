#!/usr/bin/env python3
"""data/snapshot.json から、静的サイト(HTML)を dist/furusato/ に作ります。

使い方:
  python3 sites/furusato/build.py                 # 公開用
  python3 sites/furusato/build.py --demo          # ダミーデータで見た目を確認(APIもIDも不要)

公開先のURLは環境変数 FURUSATO_BASE_URL(例: https://furusato-yosan.com)で指定します。
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

from plans import make_plan  # noqa: E402
from rank import rank_category  # noqa: E402

FAMILY_UNIT = {"weight": "kg", "volume": "L", "roll": "ロール", "box": "箱"}
UNIT_DIV = {"weight": 1000, "volume": 1000, "roll": 1, "box": 1}
# style.css の中身が変わると値が変わり、ブラウザが古い見た目を使い続けるのを防ぐ
CSS_VERSION = hashlib.sha1((HERE / "style.css").read_bytes()).hexdigest()[:8]
FONTS = ("https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900"
         "&family=Roboto+Condensed:wght@700;800&display=swap")

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


def e(text):
    return escape(str(text), quote=True)


def yen(n):
    return f"{n:,}円"


def man(amount):
    """10000 → 「1万円」"""
    return f"{amount // 10000}万円" if amount % 10000 == 0 else yen(amount)


def num(value, family):
    """1万円あたりの量の数字部分(単位なし)。"""
    if family in ("roll", "box") or value >= 100:
        return f"{value:,.0f}"
    return f"{value:.1f}"


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
        self.updated = datetime.fromisoformat(fetched).strftime("%-m月%-d日 %H:%M") if fetched else ""
        self.updated_day = datetime.fromisoformat(fetched).strftime("%-m月%-d日") if fetched else "今日"
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
        self.ranked_by_genre = {s: r for s, (_, r, _) in self.results.items()}
        self.budgets = config.get("budgets", [])

    def short(self, slug):
        return self.results[slug][0]["short"]

    # ---------- 共通部品 ----------
    def layout(self, path, title, description, body, noindex=False, current=""):
        canonical = self.base + path
        robots = '<meta name="robots" content="noindex">' if (noindex or self.demo) else ""
        budgets = "".join(f'<a class="{"on" if b["slug"] == current else ""}" href="/{b["slug"]}/">{man(b["amount"])}</a>'
                          for b in self.budgets)
        genres = "".join(f'<a class="{"on" if s == current else ""}" href="/{s}/">{e(c["short"])}</a>'
                         for s, (c, _, _) in self.results.items())
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
<meta name="theme-color" content="#ffd23f">
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
<header class="masthead"><div class="wrap">
<a class="logo" href="/"><svg class="mark" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="#e2382b"/><circle cx="24" cy="24" r="18.5" fill="none" stroke="#fff" stroke-width="1.5"/><text x="24" y="31.5" text-anchor="middle" font-size="22" font-weight="900" fill="#fff" font-family="Zen Maru Gothic, sans-serif">予</text></svg><span class="logo-t"><span class="logo-s">ふるさと納税</span><span class="logo-l">予算で<b>えらぶ</b></span></span></a>
<span class="pr-tag">PR<small>広告を含みます</small></span>
<span class="stamp">毎朝更新<br><b>{e(self.updated)}</b></span>
</div></header>
<nav class="rail"><div class="wrap">
<div class="rail-row"><span class="rail-k">予算</span>{budgets}</div>
<div class="rail-row"><span class="rail-k">品目</span>{genres}</div>
</div></nav>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">
<p class="foot-logo">予算で<b>えらぶ</b> ふるさと納税</p>
<p class="foot-pr">PR ｜ このサイトは楽天アフィリエイトの広告リンクを使っています。リンク先で寄付すると、運営者に紹介料が入ります。</p>
<p><a href="/meyasu/">予算の決め方</a> ／ <a href="/about/">運営者・計算方法</a> ／ <a href="/privacy/">プライバシーポリシー</a></p>
<p>寄付額・在庫・内容は毎日変わります。申し込む前に、楽天ふるさと納税の返礼品ページで最新の内容を確かめてください。</p>
<p>© {self.year} {e(self.c['operator_name'])}</p>
</div></footer>
<script>{SORT_JS}</script>
</body>
</html>
"""

    def deadline(self):
        if self.days_left < 0:
            return ""
        start = date(self.year, 1, 1)
        passed = (self.today - start).days / ((date(self.year, 12, 31) - start).days + 1)
        urgent = " urgent" if self.days_left <= 14 else ""
        return f"""<section class="dl{urgent}">
<p class="dl-head">{self.year}年分の締め切りまで</p>
<p class="dl-num"><span>あと</span><b>{self.days_left}</b><span>日</span></p>
<p class="dl-sub"><b>12月31日</b>までの寄付が、{self.year}年分になります。年末は人気の返礼品が品切れになることもあります。</p>
<div class="dl-bar" role="img" aria-label="{self.year}年の残り{100 - round(passed * 100)}%"><i style="width:{passed * 100:.0f}%"></i></div>
<p class="dl-bar-l"><span>1月</span><span>{self.year}年の残り {100 - round(passed * 100)}%</span><span>12月31日</span></p>
</section>"""

    def item(self, g, family, rank=None, typical=None, compact=False):
        unit = FAMILY_UNIT[family]
        link = sponsored(g.url)
        img = (f'<img src="{e(g.image)}" alt="" width="120" height="120" loading="lazy">'
               if g.image else '<span class="noimg"></span>')
        rev = f'<span class="star">★{g.review_average:.1f}</span> {g.review_count:,}件' if g.review_count else "レビューなし"
        if g.per10k is None:
            price = yen(g.price_min) if g.price_min == g.price_max else f"{yen(g.price_min)}〜{yen(g.price_max)}"
            return f"""<li class="it plain">
<a class="ph" {link}>{img}</a>
<div class="tx"><p class="town">{e(g.shop)}</p><p class="nm"><a {link}>{e(g.short_name)}</a></p>
<p class="meta">{rev}</p><p class="meta">寄付額 <b>{price}</b>(量によって変わります)</p></div>
</li>"""
        if rank and rank <= 3:
            badge = f'<span class="rec r{rank}"><small>おすすめ</small>{rank}<small>位</small></span>'
        else:
            badge = f'<span class="no">{rank}</span>' if rank else ""
        hot = f'<span class="hot">ふつうの{g.per10k / typical:.1f}倍</span>' if typical and g.per10k >= typical * 1.2 else ""
        per_unit = round(g.price_min / (g.amount / UNIT_DIV[family]))
        note = f'<p class="meta">{e(g.note)}</p>' if g.note else ""
        cls = "it compact" if compact else "it"
        return f"""<li class="{cls}" data-per="{g.per10k:.4f}" data-price="{g.price_min}" data-reviews="{g.review_count}">
{badge}<a class="ph" {link}>{img}</a>
<div class="tx">
<p class="town">{e(g.shop)}</p>
<p class="nm"><a {link}>{e(g.short_name)}</a></p>
<p class="meta">{rev}</p>{note}
</div>
<div class="fig">
<p class="big"><small>1万円で</small><b>{num(g.per10k, family)}</b><small>{e(unit)}</small></p>{hot}
<p class="sub">寄付 <b>{yen(g.price_min)}</b> で {e(g.amount_text)}<br>1{e(unit)}あたり{yen(per_unit)}</p>
<a class="go" {link}>楽天で見る</a>
</div>
</li>"""

    def plan_block(self, budget, plan_def):
        picks, total = make_plan(self.ranked_by_genre, plan_def["genres"], budget)
        if not picks:
            return ""
        haul = "・".join(f"{e(self.short(s))} {e(g.amount_text)}" for s, g in picks)
        rows = "".join(
            f'<li><span class="pg">{e(self.short(s))}</span>'
            f'<a {sponsored(g.url)}>{e(g.short_name[:34])}</a>'
            f'<span class="pv">{e(g.amount_text)}</span><span class="pp">{yen(g.price_min)}</span></li>'
            for s, g in picks)
        return f"""<section class="plan">
<p class="plan-k">{e(plan_def['name'])}</p>
<p class="plan-haul">{haul}</p>
<ol class="plan-list">{rows}</ol>
<p class="plan-sum">合計 <b>{yen(total)}</b>(残り{yen(budget - total)})</p>
</section>"""

    # ---------- 各ページ ----------
    def index(self):
        tickets = "".join(f"""<a class="ticket" href="/{b['slug']}/"><span class="t-amt">{b['amount'] // 10000}<small>万円</small></span>
<span class="t-cap">で選ぶ</span></a>""" for b in self.budgets)
        rows = []
        for slug, (cat, ranked, _) in self.results.items():
            top = ranked[0]
            rows.append(f"""<li><a href="/{slug}/"><span class="tb-g">{e(cat['short'])}</span>
<span class="tb-v"><b>{num(top.per10k, cat['family'])}</b>{e(FAMILY_UNIT[cat['family']])}</span>
<span class="tb-t">{e(top.shop)}</span></a></li>""")
        teaser = ""
        for pd in self.c.get("plans", []):
            picks, total = make_plan(self.ranked_by_genre, pd["genres"], 50000)
            if picks:
                haul = "<br>".join(f"{e(self.short(s))} <b>{e(g.amount_text)}</b>" for s, g in picks)
                teaser = f"""<section class="teaser">
<p class="teaser-k">たとえば、5万円なら</p>
<p class="teaser-v">{haul}</p>
<p class="teaser-s">合計{yen(total)}・「{e(pd['name'])}」の組み合わせ</p>
<a class="more" href="/5man/">5万円の組み合わせをもっと見る</a>
</section>"""
                break
        body = f"""<section class="hero">
<p class="hero-k">楽天ふるさと納税／毎朝集計</p>
<h1>予算を<br class="sp">えらぶだけ。</h1>
<p class="hero-s">寄付する金額を決めたら、<br class="sp">その金額で「いちばんたくさん届く」返礼品を出します。</p>
<div class="tickets">{tickets}</div>
<p class="hero-n">予算が決まっていない人は <a href="/meyasu/">予算の決め方</a></p>
</section>
{self.deadline()}
{teaser}
<h2 class="hd"><span>{e(self.updated_day)}の1位</span><small>1万円あたりに届く量</small></h2>
<ul class="board">{''.join(rows)}</ul>
<section class="memo">
<h2 class="hd"><span>このサイトのこと</span></h2>
<p>返礼品の量を寄付額で割って、「1万円でどれだけ届くか」で並べています。商品名から量がはっきり読み取れたものだけを数え、レビューが{self.c.get('min_review_count', 10)}件に満たないものは外しています。</p>
<p>量の多さは、味や品質の評価ではありません。気になる返礼品は、レビューも読んでから選んでください。</p>
<p class="sign">運営 {e(self.c['operator_name'])}</p>
</section>"""
        title = f"予算でえらぶふるさと納税【{self.year}年】1万円・3万円・5万円でいちばん届く返礼品"
        desc = "1万円・2万円・3万円・5万円・10万円の予算別に、楽天ふるさと納税でいちばん量が多く届く返礼品と組み合わせを毎朝更新。"
        return self.layout("/", title, desc, body)

    def budget_page(self, b):
        amount = b["amount"]
        plans = "".join(self.plan_block(amount, pd) for pd in self.c.get("plans", [])) if amount >= 20000 else ""
        plan_sec = (f'<h2 class="hd"><span>{man(amount)}を使い切る組み合わせ</span><small>残りの予算で、量が多いものから選んでいます</small></h2>'
                    f'<div class="plans">{plans}</div>') if plans else ""
        genre_secs = []
        for slug, (cat, ranked, _) in self.results.items():
            pool = [g for g in ranked if g.price_min <= amount][:3]
            if not pool:
                continue
            typical = median(g.per10k for g in ranked)
            items = "".join(self.item(g, cat["family"], i, typical, compact=True) for i, g in enumerate(pool, 1))
            genre_secs.append(f"""<section class="gsec">
<h3 class="gh">{e(cat['title'])}<a href="/{slug}/">すべて見る</a></h3>
<ol class="items">{items}</ol>
</section>""")
        others = "".join(f'<a href="/{x["slug"]}/">{man(x["amount"])}</a>' for x in self.budgets if x is not b)
        body = f"""<nav class="crumbs"><a href="/">トップ</a> ／ 予算{man(amount)}</nav>
<h1 class="ph1"><span class="ph1-amt">{amount // 10000}<small>万円</small></span>で選ぶなら</h1>
<p class="lead">寄付額{man(amount)}以内の返礼品を、品目ごとに「1万円あたりに届く量」が多い順で並べました。{e(self.updated)}時点のデータです。</p>
{self.deadline()}
{plan_sec}
<h2 class="hd"><span>品目ごとの上位3つ</span><small>寄付額{man(amount)}以内</small></h2>
{''.join(genre_secs)}
<p class="pager">ほかの予算：{others}</p>"""
        title = f"ふるさと納税 {man(amount)}でいちばん届く返礼品【{self.year}年】予算別おすすめ"
        desc = f"寄付額{man(amount)}以内で、量がいちばん多く届く楽天ふるさと納税の返礼品を品目別に。組み合わせ例つき・毎朝更新。"
        return self.layout(f"/{b['slug']}/", title, desc, body, current=b["slug"])

    def category(self, slug):
        cat, ranked, popular = self.results[slug]
        family = cat["family"]
        unit = FAMILY_UNIT[family]
        top = ranked[0]
        typical = median(g.per10k for g in ranked)
        items = "".join(self.item(g, family, i, typical) for i, g in enumerate(ranked, 1))
        pop = "".join(self.item(g, family) for g in popular)
        by_budget = []
        for b in self.budgets:
            pool = [g for g in ranked if g.price_min <= b["amount"]]
            if pool:
                g = max(pool, key=lambda x: x.per10k)
                by_budget.append(f'<li><span class="bb-k">{man(b["amount"])}まで</span>'
                                 f'<a {sponsored(g.url)}>{e(g.shop)}<br><small>{e(g.short_name[:24])}</small></a>'
                                 f'<span class="bb-v"><b>{num(g.per10k, family)}</b>{e(unit)}</span></li>')
        unit_note = f"<li>{e(cat['unit_note'])}</li>" if cat.get("unit_note") else ""
        body = f"""<nav class="crumbs"><a href="/">トップ</a> ／ {e(cat['title'])}</nav>
<h1 class="gh1">ふるさと納税の{e(cat['title'])}<br><small>1万円でどれだけ届く？【{self.year}年】</small></h1>
<p class="verdict">1万円で届く{e(cat['short'])}は、ふつう<b>{num(typical, family)}{e(unit)}</b>前後。<br>
いちばん多いのは<b class="red">{num(top.per10k, family)}{e(unit)}</b>({e(top.shop)})です。</p>
<p class="lead">{e(cat['intro'])}</p>
{self.deadline()}
<h2 class="hd"><span>予算ごとの1位</span></h2>
<ul class="bybudget">{''.join(by_budget)}</ul>
<h2 class="hd" id="ranking"><span>ランキング</span><small>{len(ranked)}件・{e(self.updated)}時点</small></h2>
<div class="controls" data-controls hidden>
<label>並び順<select data-sort><option value="per">量が多い順</option><option value="price">寄付額が安い順</option><option value="reviews">レビューが多い順</option></select></label>
<label>予算<select data-cap><option value="0">上限なし</option><option value="10000">1万円まで</option><option value="20000">2万円まで</option><option value="30000">3万円まで</option><option value="50000">5万円まで</option></select></label>
</div>
<ol class="items" data-list>{items}</ol>
<p class="empty" data-empty hidden>この予算で寄付できる返礼品はありません。</p>
<h2 class="hd"><span>量を選べる人気の返礼品</span><small>レビューが多い順</small></h2>
<p class="lead small">量によって寄付額が変わるため、ランキングには入れていません。</p>
<ul class="items">{pop}</ul>
<section class="memo">
<h2 class="hd"><span>数え方</span></h2>
<ul>
<li>1万円あたりの量＝商品名の量÷寄付額×10,000。「ふつう」は、ランキングに入った返礼品の真ん中の値です。</li>
{unit_note}
<li>「約5kg」のような表記は、書かれた数字のまま数えています。</li>
</ul>
</section>"""
        title = f"ふるさと納税 {cat['title']}のコスパランキング【{self.year}年】1万円で{num(top.per10k, family)}{unit}届くのは？"
        desc = (f"楽天ふるさと納税の{cat['title']}を、1万円で届く量で比較。ふつうは{num(typical, family)}{unit}、"
                f"いちばん多いのは{num(top.per10k, family)}{unit}。予算別の1位つき・毎朝更新。")
        return self.layout(f"/{slug}/", title, desc, body, current=slug)

    def meyasu(self):
        links = "".join(f'<a class="ticket mini" href="/{b["slug"]}/"><span class="t-amt">{b["amount"] // 10000}<small>万円</small></span></a>'
                        for b in self.budgets)
        body = f"""<h1 class="gh1">予算の決め方</h1>
<p class="lead">ふるさと納税で、自己負担2,000円で済む寄付額には上限があります。上限は、年収や家族構成によって人それぞれです。</p>
<section class="memo">
<h2 class="hd"><span>1. 上限の目安を調べる</span></h2>
<p>総務省のふるさと納税ポータルサイトに、年収と家族構成ごとの目安の表があります。まずはここで、自分に近い行を探してください。</p>
<p><a href="https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/deduction.html" rel="noopener" target="_blank">総務省｜ふるさと納税ポータルサイト「控除額の計算」</a></p>
<h2 class="hd"><span>2. 少し下をねらう</span></h2>
<p>住宅ローン控除や医療費控除を受ける人は、上限が下がることがあります。目安ぴったりではなく、少し少なめにしておくと安心です。</p>
<h2 class="hd"><span>3. 予算をえらぶ</span></h2>
<p>決まったら、その金額のページへ。品目ごとの1位と、予算を使い切る組み合わせを出しています。</p>
<div class="tickets">{links}</div>
</section>
<p class="lead small">このサイトでは控除額の計算はしていません。正確な金額は、総務省のページや税務署・お住まいの市区町村で確認してください。</p>"""
        return self.layout("/meyasu/", f"ふるさと納税の予算の決め方 | {self.c['site_name']}",
                           "ふるさと納税の上限(予算)の目安の調べ方と、決め方のコツ。", body, current="meyasu")

    def about(self):
        body = f"""<h1 class="gh1">運営者・計算方法</h1>
<section class="memo">
<h2 class="hd"><span>運営者</span></h2>
<p>{e(self.c['operator_name'])}<br>お問い合わせ：{e(self.c['contact'])}</p>
<h2 class="hd"><span>広告について</span></h2>
<p>このサイトは、楽天グループ株式会社の「楽天アフィリエイト」を使っています。サイトのリンクから楽天ふるさと納税で寄付をすると、運営者に紹介料が支払われます。紹介料の有無や金額で、順位を変えることはありません。</p>
<h2 class="hd"><span>データと計算方法</span></h2>
<ul>
<li>返礼品のデータは、楽天ウェブサービスのAPIから毎朝取得しています。</li>
<li>1万円あたりの量＝商品名に書かれた量÷寄付額×10,000。</li>
<li>量や回数を選べる返礼品、定期便、量の表記が複数ある返礼品は、計算を間違えないようにランキングから外しています。</li>
<li>極端な値(読み取りの誤りの可能性が高いもの)は、自動で外しています。</li>
<li>組み合わせは、品目の順番に「残りの予算で寄付できる中で、量がいちばん多いもの」を選んでいます。</li>
</ul>
<h2 class="hd"><span>免責事項</span></h2>
<p>内容の正確さには気をつけていますが、寄付額・在庫・内容は変わることがあります。申し込む前に、必ず返礼品のページで確かめてください。控除の上限は人によって違います。<a href="/meyasu/">予算の決め方</a>もあわせてどうぞ。</p>
</section>"""
        return self.layout("/about/", f"運営者・計算方法 | {self.c['site_name']}", "運営者情報、広告について、計算方法。", body)

    def privacy(self):
        body = f"""<h1 class="gh1">プライバシーポリシー</h1>
<section class="memo">
<h2 class="hd"><span>アフィリエイトについて</span></h2>
<p>このサイトは楽天アフィリエイトを使っています。リンクをクリックすると、楽天グループ株式会社がCookieなどで紹介の成果を記録することがあります。くわしくは楽天グループ株式会社のプライバシーポリシーをご覧ください。</p>
<h2 class="hd"><span>アクセス解析について</span></h2>
<p>このサイトでは、閲覧数などを知るために、Cloudflare, Inc.の「Cloudflare Web Analytics」を使っています。Cookieは使わず、閲覧者を特定できる情報も集めていません。集めるのは、見られたページ、参照元、ブラウザや端末の種類、おおまかな国・地域などの統計情報です。くわしくは<a href="https://www.cloudflare.com/ja-jp/privacypolicy/" rel="noopener" target="_blank">Cloudflareのプライバシーポリシー</a>をご覧ください。</p>
<h2 class="hd"><span>個人情報について</span></h2>
<p>お問い合わせでいただいた個人情報は、お返事のためだけに使い、法令にもとづく場合を除いて第三者に渡しません。</p>
<p>制定日：{self.today.isoformat()}</p>
</section>"""
        return self.layout("/privacy/", f"プライバシーポリシー | {self.c['site_name']}", "プライバシーポリシー。", body)

    def not_found(self):
        return self.layout("/404.html", "ページが見つかりません", "ページが見つかりません。",
                           '<h1 class="gh1">ページが見つかりません</h1><p><a href="/">トップページへ</a></p>', noindex=True)

    def build(self, out):
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        pages = {"index.html": self.index(), "meyasu/index.html": self.meyasu(), "about/index.html": self.about(),
                 "privacy/index.html": self.privacy(), "404.html": self.not_found()}
        for b in self.budgets:
            pages[f"{b['slug']}/index.html"] = self.budget_page(b)
        for slug in self.results:
            pages[f"{slug}/index.html"] = self.category(slug)
        for rel, html in pages.items():
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(html, encoding="utf-8")
        shutil.copy(HERE / "style.css", out / "style.css")
        for f in (HERE / "static").iterdir():  # ファビコンなど
            shutil.copy(f, out / f.name)
        urls = (["/"] + [f"/{b['slug']}/" for b in self.budgets] + [f"/{s}/" for s in self.results]
                + ["/meyasu/", "/about/"])
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

    site = Site(config, snapshot, overrides, base_url, today, demo=args.demo)
    if not site.results:
        sys.exit("公開できるカテゴリがありません。")
    n = site.build(Path(args.out))
    print(f"{n}ページを作りました: {args.out}")


if __name__ == "__main__":
    main()
