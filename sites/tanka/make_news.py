#!/usr/bin/env python3
"""価格の記録(data/history.csv)から、「値下がりした日用品」の記事を自動で書きます。

使い方:
  python3 sites/tanka/make_news.py           # 条件を満たせば news/日付-price-drop.md を作る
  python3 sites/tanka/make_news.py --dry-run # 作らずに、内容だけ表示する

記事を作る条件(同じような記事を量産しないため):
  ・直近7日以内に、送料込みの値段が5%以上下がった商品が3件以上ある
  ・前回の値下がりの記事から6日以上たっている
記事のリンクは「item:商品コード」の印で書き、サイトを作るときに最新のリンクへ置き換えます(IDをファイルに残さない)。
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "common"))

from news import load_articles  # noqa: E402
from unitprice import rank_category, yen_unit  # noqa: E402

MIN_DROP = 0.05      # 5%以上の値下がり
MIN_ITEMS = 3        # 3件以上あるときだけ記事にする
WINDOW_DAYS = 7      # 直近7日と比べる
INTERVAL_DAYS = 6    # 前回の記事から6日以上あける
MAX_PER_CATEGORY = 3


def load_history(path):
    prices = defaultdict(dict)
    for r in csv.DictReader(open(path, encoding="utf-8")):
        try:
            prices[r["item_code"]][date.fromisoformat(r["date"])] = int(float(r["price"]))
        except (ValueError, KeyError):
            continue
    return prices


def find_drops(config, snapshot, prices, today):
    since = today - timedelta(days=WINDOW_DAYS)
    drops, seen = [], set()
    for cat in config["categories"]:
        ranked = rank_category(snapshot.get("categories", {}).get(cat["slug"], []), cat, top=300)
        for p in ranked:
            if p.code in seen or p.code not in prices:
                continue
            past = {d: v for d, v in prices[p.code].items() if since <= d < today}
            if not past:
                continue
            start = min(past)
            old = past[start]
            if old <= 0 or p.price >= old:
                continue
            rate = (old - p.price) / old
            if rate >= MIN_DROP:
                seen.add(p.code)
                div = cat["per"]["div"]
                drops.append({"cat": cat, "p": p, "old": old, "rate": rate, "start": start,
                              "old_unit": old / (p.amount / div)})
    return drops


def make_article(drops, today):
    drops.sort(key=lambda d: -d["rate"])
    by_cat = defaultdict(list)
    for d in drops:
        if len(by_cat[d["cat"]["slug"]]) < MAX_PER_CATEGORY:
            by_cat[d["cat"]["slug"]].append(d)
    picked = [d for ds in by_cat.values() for d in ds]
    top = picked[0]
    start = min(d["start"] for d in picked)
    md = lambda x: f"{x.month}月{x.day}日"
    title = f"{md(start)}から{md(today)}に値下がりした日用品 {len(picked)}件"
    summary = (f"楽天市場の送料込みの日用品のうち、{md(start)}より5%以上安くなった商品をまとめました。"
               f"いちばん下がったのは{top['cat']['title']}で{top['rate'] * 100:.0f}%。")
    lines = ["---", f"title: {title}", f"date: {today.isoformat()}", f"summary: {summary}", "kind: auto", "type: price-drop", "---",
             f"このサイトで毎朝記録している価格のうち、{md(start)}と比べて**送料込みの値段が5%以上下がった商品**を、品目ごとにまとめました。"
             f"値段は{md(today)}朝の時点のものです。", ""]
    for slug, ds in by_cat.items():
        cat = ds[0]["cat"]
        per = cat["per"]["label"]
        lines += [f"## {cat['title']}", "", f"| 商品 | 値段(送料込み) | {per}あたり |", "|---|---|---|"]
        for d in ds:
            p = d["p"]
            name = p.short_name.replace("|", "／")
            lines.append(f"| [{name}](item:{p.code}) | {d['old']:,}円 → **{p.price:,}円**(-{d['rate'] * 100:.0f}%) "
                         f"| {yen_unit(d['old_unit'])}円 → **{yen_unit(p.unit_price)}円** |")
        lines += ["", f"[{cat['title']}の単価ランキングを見る](/{slug}/)", ""]
    lines += ["## 調べ方", "",
              f"- 楽天市場の送料込みの商品を毎朝集めて、値段を記録しています。{md(start)}の値段と{md(today)}の値段を比べています。",
              "- 値段・在庫は変わることがあります。購入する前に、商品ページで最新の値段を確かめてください。",
              "- 量の読み取りや計算の方法は、[運営者・計算方法](/about/)のページをご覧ください。", ""]
    return f"{today.isoformat()}-price-drop", "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    snap_path = HERE / "data" / "snapshot.json"
    hist_path = HERE / "data" / "history.csv"
    if not snap_path.exists() or not hist_path.exists():
        sys.exit("snapshot.json か history.csv がありません。先に fetch.py を実行してください。")
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    prices = load_history(hist_path)
    today = max(d for v in prices.values() for d in v)

    recent = [a for a in load_articles(HERE / "news") if a.meta.get("type") == "price-drop"]
    if recent and (today - recent[0].date).days < INTERVAL_DAYS:
        print(f"前回の値下がりの記事({recent[0].date})から{INTERVAL_DAYS}日たっていないので、作りません。")
        return
    drops = find_drops(config, snapshot, prices, today)
    if len(drops) < MIN_ITEMS:
        print(f"5%以上値下がりした商品が{len(drops)}件なので、記事は作りません。")
        return
    slug, text = make_article(drops, today)
    if args.dry_run:
        print(text)
        return
    out = HERE / "news" / f"{slug}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(f"記事を作りました: {out.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
