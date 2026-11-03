#!/usr/bin/env python3
"""
日本からの出品の「売れ筋」を広く調べる(eBay公式 Browse API)

eBay(アメリカ)の主要カテゴリを順に調べ、
  1. 日本から出品されている数が多いサブカテゴリ(=日本の出品者が力を入れている分野)
  2. そのサブカテゴリで、日本の出品者の「同じ出品から何個売れたか(推定販売数)」
を集計して、売れている順に並べます。

※ eBay の API では「売れた履歴」そのものは取れません。代わりに、複数個まとめて出品されている
  商品の「推定販売数(estimatedSoldQuantity)」を使います。
  → 何度も売れている=仕入れを繰り返せる商品が見つかりやすい一方、1点ものの売れ行きは
    数えられません。気になった分野は Terapeak で売れた件数を確認してください。

使い方:  python3 japan_trends.py
         (env.txt に EBAY_CLIENT_ID / EBAY_CLIENT_SECRET が必要。1回あたり約1,000回APIを使います。上限は1日5,000回)
"""
import csv
import html
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import config
import ebay_research as er

HERE = Path(__file__).resolve().parent
BASE = "https://api.ebay.com/buy/browse/v1"

# eBay(アメリカ)の主要カテゴリ。不要なものは config.py の TREND_CATEGORIES で絞れます
DEFAULT_CATEGORIES = {
    "1": "Collectibles", "220": "Toys & Hobbies", "1249": "Video Games & Consoles",
    "625": "Cameras & Photo", "281": "Jewelry & Watches", "11450": "Clothing, Shoes & Accessories",
    "11233": "Music", "619": "Musical Instruments & Gear", "293": "Consumer Electronics",
    "26395": "Health & Beauty", "11700": "Home & Garden", "888": "Sporting Goods",
    "267": "Books & Magazines", "20081": "Antiques", "550": "Art", "870": "Pottery & Glass",
    "237": "Dolls & Bears", "45100": "Entertainment Memorabilia", "14339": "Crafts",
    "64482": "Sports Mem, Cards & Fan Shop", "11232": "Movies & TV", "1281": "Pet Supplies",
    "12576": "Business & Industrial", "58058": "Computers/Tablets & Networking",
}
SUBCATS_PER_CATEGORY = getattr(config, "TREND_SUBCATS_PER_CATEGORY", 5)   # 1カテゴリで調べるサブカテゴリ数
ITEMS_PER_SUBCAT = getattr(config, "TREND_ITEMS_PER_SUBCAT", 6)           # 1サブカテゴリで詳しく見る出品数
WAIT = 0.25


def call(token, path, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = er.http_json(url, {"Authorization": "Bearer " + token,
                              "X-EBAY-C-MARKETPLACE-ID": config.MARKETPLACE, "Accept-Language": "en-US"})
    time.sleep(WAIT)
    return data


def jp_filter(extra=""):
    f = f"itemLocationCountry:JP,price:[{config.MIN_PRICE_USD}..],priceCurrency:USD"
    return f + ("," + extra if extra else "")


def subcategories(token, cat_id):
    """日本からの出品数が多い子カテゴリ [(id, 名前, 日本の出品数)]"""
    data = call(token, "/item_summary/search", {
        "category_ids": cat_id, "filter": jp_filter(), "limit": 1,
        "fieldgroups": "MATCHING_ITEMS,CATEGORY_REFINEMENTS"})
    dist = (data.get("refinement") or {}).get("categoryDistributions") or []
    subs = [(d.get("categoryId"), d.get("categoryName", ""), int(d.get("matchCount", 0)))
            for d in dist if d.get("categoryId") and d.get("categoryId") != cat_id]
    return data.get("total", 0), sorted(subs, key=lambda s: -s[2])


def total_count(token, cat_id):
    data = call(token, "/item_summary/search", {"category_ids": cat_id, "limit": 1,
                                                  "filter": f"price:[{config.MIN_PRICE_USD}..],priceCurrency:USD"})
    return data.get("total", 0)


def sample_items(token, cat_id):
    data = call(token, "/item_summary/search", {
        "category_ids": cat_id, "filter": jp_filter("buyingOptions:{FIXED_PRICE}"), "limit": 50})
    return data.get("itemSummaries", [])


def months_since(iso):
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return max((datetime.now(timezone.utc) - d).days / 30.4, 0.5)


def item_detail(token, item_id):
    d = call(token, "/item/" + urllib.parse.quote(item_id, safe=""))
    sold = 0
    for a in d.get("estimatedAvailabilities") or []:
        sold += int(a.get("estimatedSoldQuantity") or 0)
    m = months_since(d.get("itemCreationDate", ""))
    try:
        price = float(d["price"]["value"])
    except (KeyError, TypeError, ValueError):
        price = None
    return {
        "title": d.get("title", ""), "price": price, "sold": sold,
        "per_month": round(sold / m, 1) if m else None,
        "url": d.get("itemWebUrl", ""), "seller": (d.get("seller") or {}).get("username", ""),
    }


def scan():
    er.load_env(HERE / "env.txt")
    er.load_env(HERE / ".env")
    token = er.get_token()
    cats = getattr(config, "TREND_CATEGORIES", None) or DEFAULT_CATEGORIES
    rows, items = [], []
    for n, (cid, cname) in enumerate(cats.items(), 1):
        try:
            jp_total, subs = subcategories(token, cid)
        except RuntimeError as e:
            print(f"[{n}/{len(cats)}] ! {cname}: {e}")
            continue
        print(f"[{n}/{len(cats)}] {cname}: 日本からの出品 {jp_total:,} 件")
        for sid, sname, jp in subs[:SUBCATS_PER_CATEGORY]:
            try:
                allc = total_count(token, sid)
                sample = sample_items(token, sid)[:ITEMS_PER_SUBCAT]
                details = []
                for s in sample:
                    try:
                        details.append(item_detail(token, s["itemId"]))
                    except (RuntimeError, KeyError):
                        pass
            except RuntimeError as e:
                print(f"    ! {sname}: {e}")
                continue
            sold = sum(d["sold"] for d in details)
            pm = sum(d["per_month"] or 0 for d in details)
            prices = sorted(d["price"] for d in details if d["price"])
            rows.append({"category": cname, "subcategory": sname, "sub_id": sid, "jp": jp, "all": allc,
                         "jp_share": round(jp / allc, 3) if allc else 0, "sampled": len(details),
                         "sold": sold, "per_month": round(pm, 1),
                         "median_price": prices[len(prices) // 2] if prices else None})
            for d in details:
                items.append({**d, "category": cname, "subcategory": sname})
            print(f"    {sname}: 日本{jp:,}/全体{allc:,}  サンプル{len(details)}件の推定販売 {sold}個(月{pm:.1f}個)")
    return rows, items


def write_report(rows, items, outdir=None):
    outdir = outdir or HERE / "output"
    outdir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    rows = sorted(rows, key=lambda r: -r["per_month"])
    items = sorted([i for i in items if i["sold"] > 0], key=lambda i: -(i["per_month"] or 0))
    csv_path = outdir / f"japan_trends_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["カテゴリ", "サブカテゴリ", "日本からの出品数", "全体の出品数", "日本の割合",
                    "調べた出品数", "推定販売数(合計)", "月あたり販売数(合計)", "価格の中央値USD"])
        for r in rows:
            w.writerow([r["category"], r["subcategory"], r["jp"], r["all"], f"{r['jp_share']:.0%}", r["sampled"],
                        r["sold"], r["per_month"], r["median_price"] or ""])
    items_path = outdir / f"japan_bestsellers_{stamp}.csv"
    with items_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["月あたり販売数", "推定販売数", "価格USD", "カテゴリ", "サブカテゴリ", "商品名", "出品者", "URL"])
        for i in items:
            w.writerow([i["per_month"], i["sold"], i["price"] or "", i["category"], i["subcategory"],
                        i["title"], i["seller"], i["url"]])

    def terapeak(q):
        return ("https://www.ebay.com/sh/research?marketplace=EBAY-US&dayRange=90&tabName=SOLD&keywords="
                + urllib.parse.quote(q))
    sub_rows = "".join(
        f"<tr><td>{html.escape(r['category'])}</td><td class='t'>{html.escape(r['subcategory'])}</td>"
        f"<td class='p'>{r['per_month']}</td><td>{r['sold']:,}</td><td>{r['jp']:,}</td><td>{r['jp_share']:.0%}</td>"
        f"<td>{'$' + format(r['median_price'], '.0f') if r['median_price'] else '-'}</td>"
        f"<td><a href='https://www.ebay.com/sch/{r['sub_id']}/i.html?LH_PrefLoc=99&_salic=104' target='_blank'>eBay</a></td></tr>"
        for r in rows)
    item_rows = "".join(
        f"<tr><td class='p'>{i['per_month']}</td><td>{i['sold']:,}</td><td>{'$' + format(i['price'], '.2f') if i['price'] else '-'}</td>"
        f"<td>{html.escape(i['subcategory'])}</td><td class='t'><a href='{html.escape(i['url'])}' target='_blank'>"
        f"{html.escape(i['title'][:80])}</a></td><td><a href='{terapeak(i['title'][:60])}' target='_blank'>Terapeak</a></td></tr>"
        for i in items[:150])
    html_path = outdir / f"japan_trends_{stamp}.html"
    html_path.write_text(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>日本からの売れ筋 {stamp}</title>
<style>
body{{font-family:-apple-system,"Hiragino Sans",sans-serif;background:#f5f5f2;margin:0;padding:16px;color:#222}}
h1{{font-size:19px}} h2{{font-size:16px;margin-top:24px}} .sum{{color:#555;font-size:13px;line-height:1.7}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;background:#fff;font-size:13px;width:100%}}
th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap}} th{{background:#fafafa}}
td:first-child{{text-align:right}} .t{{text-align:left;white-space:normal;min-width:220px}} .p{{font-weight:600;color:#1e7e34}}
</style></head><body>
<h1>日本からの出品の売れ筋({stamp})</h1>
<div class="sum">eBay(アメリカ)で、日本から出品されている商品を調べました。<br>
<b>月あたり販売数</b>=各サブカテゴリで上位{ITEMS_PER_SUBCAT}件の出品について、「推定販売数 ÷ 出品してからの月数」を足したものです。
複数個まとめて出品されている商品の販売数なので、<b>何度も売れている(仕入れを繰り返せる)分野ほど大きく</b>なります。
1点ものの売れ行きは含まれないため、気になる分野は Terapeak で売れた件数を確認してください。</div>
<h2>サブカテゴリ(月あたり販売数の多い順)</h2>
<div class="scroll"><table><tr><th>カテゴリ</th><th>サブカテゴリ</th><th>月あたり販売数</th><th>推定販売数</th>
<th>日本からの出品数</th><th>日本の割合</th><th>価格の中央値</th><th></th></tr>{sub_rows}</table></div>
<h2>よく売れている日本の出品(上位150件)</h2>
<div class="scroll"><table><tr><th>月あたり</th><th>推定販売数</th><th>価格</th><th>サブカテゴリ</th><th>商品名</th><th></th></tr>{item_rows}</table></div>
</body></html>""", encoding="utf-8")
    return csv_path, items_path, html_path


def main():
    rows, items = scan()
    paths = write_report(rows, items)
    print("\n完了")
    for p in paths:
        print("  " + str(p))


if __name__ == "__main__":
    main()
