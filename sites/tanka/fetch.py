#!/usr/bin/env python3
"""楽天APIからカテゴリごとの商品を取得し、data/snapshot.json に保存します。

使い方:
  python3 sites/tanka/fetch.py                 # 全カテゴリ
  python3 sites/tanka/fetch.py --only kome     # 1カテゴリだけ(試すとき)

・IDやキーは .env(または環境変数)から読みます。snapshot.json はアフィリエイトリンクを含むため GitHub には上げません。
・価格の記録(IDを含まない)は data/history.csv に追記します(「買い時」を調べるための蓄積)。
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))

import rakuten_client as rc  # noqa: E402
from unitprice import matches_category  # noqa: E402

JST = timezone(timedelta(hours=9))
KEEP = ("itemCode", "itemName", "itemPrice", "itemPriceMin3", "itemPriceMax3", "affiliateUrl", "itemUrl",
        "mediumImageUrls", "shopName", "shopCode", "reviewCount", "reviewAverage", "postageFlag")


def fetch_category(settings, category, pages):
    items = {}
    for kw in category["keywords"]:
        for page in range(1, pages + 1):
            try:
                raws = rc.search_raw(settings, kw, page=page, hits=30, sort="-reviewCount",
                                     user_agent="tanka-erabu-site/1.0")
            except rc.RakutenError as e:
                print(f"  ! {kw} p{page}: {e}", file=sys.stderr)
                break
            for r in raws:
                if matches_category(r, category):
                    items.setdefault(r.get("itemCode"), {k: r.get(k) for k in KEEP})
            if len(raws) < 30:
                break
    return list(items.values())


def append_history(path, fetched_at, snapshot):
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "category", "item_code", "price", "review_count"])
        for slug, raws in snapshot.items():
            for r in raws:
                w.writerow([fetched_at[:10], slug, r["itemCode"], r.get("itemPrice"), r.get("reviewCount")])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="このカテゴリ(slug)だけ取得する")
    ap.add_argument("--no-history", action="store_true", help="history.csv に追記しない")
    args = ap.parse_args()

    rc.load_env(ROOT / ".env")
    settings = rc.get_settings()
    if settings["missing"]:
        sys.exit("環境変数が足りません: " + ", ".join(settings["missing"]) + "(.env を確認してください)")
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    snap_path = HERE / "data" / "snapshot.json"
    old = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {"categories": {}}

    fetched_at = datetime.now(JST).isoformat(timespec="minutes")
    result = dict(old.get("categories", {}))
    fetched = {}
    for cat in config["categories"]:
        if args.only and cat["slug"] != args.only:
            continue
        raws = fetch_category(settings, cat, config.get("pages_per_keyword", 2))
        print(f"{cat['title']}: {len(raws)}件")
        if raws:  # 取得に失敗したカテゴリは前回のデータを残す
            result[cat["slug"]] = raws
            fetched[cat["slug"]] = raws
    if not fetched:
        sys.exit("1件も取得できませんでした。エラーメッセージを確認してください。")

    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps({"fetched_at": fetched_at, "categories": result}, ensure_ascii=False),
                         encoding="utf-8")
    if not args.no_history:
        append_history(HERE / "data" / "history.csv", fetched_at, fetched)
    print(f"保存しました: {snap_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
