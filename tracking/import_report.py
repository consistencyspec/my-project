#!/usr/bin/env python3
"""楽天アフィリエイト管理画面からダウンロードしたCSVを取り込みます(手入力を減らすための道具)。

使い方:
  python3 tracking/import_report.py tracking/imports/今週のCSV.csv
  python3 tracking/import_report.py ファイル.csv --show-columns   # 見出しの確認だけ
  python3 tracking/import_report.py ファイル.csv --date 2026-10-09 # CSVに日付列がないとき

取り込むと tracking/sales_daily.csv に日別の成果が溜まり、posts.csv の
clicks / orders / sales_yen が自動で埋まります。同じ期間を何度取り込んでも二重に数えません。
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tracklib as tl  # noqa: E402


def read_report(path):
    """文字コード(UTF-8 / Shift_JIS)を自動判定して読み込む。"""
    last = None
    for enc in ("utf-8-sig", "cp932"):
        try:
            with open(path, newline="", encoding=enc) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError as e:
            last = e
    raise SystemExit(f"文字コードを判定できませんでした: {last}")


def find_header_row(rows, colmap):
    """見出し行を探す(先頭に説明行がある場合に対応)。"""
    known = {h for key in ("date", "item_name", "clicks", "orders", "sales_yen") for h in colmap[key]}
    for i, row in enumerate(rows[:15]):
        if len({c.strip() for c in row} & known) >= 2:
            return i
    return 0


def pick(headers, candidates):
    for c in candidates:
        if c in headers:
            return headers.index(c)
    return None


def main():
    ap = argparse.ArgumentParser(description="楽天アフィリエイトのCSVを取り込みます")
    ap.add_argument("csv_file")
    ap.add_argument("--date", help="CSVに日付列がないときに使う日付 (例: 2026-10-09)")
    ap.add_argument("--show-columns", action="store_true", help="見出しを表示して終了")
    ap.add_argument("--column-map", default=str(Path(__file__).resolve().parent / "column_map.json"))
    ap.add_argument("--posts", default=str(tl.POSTS_CSV))
    ap.add_argument("--sales", default=str(tl.SALES_CSV))
    args = ap.parse_args()

    colmap = json.loads(Path(args.column_map).read_text(encoding="utf-8"))
    rows = read_report(args.csv_file)
    if not rows:
        sys.exit("CSVが空です")
    h = find_header_row(rows, colmap)
    headers = [c.strip() for c in rows[h]]
    if args.show_columns:
        print("見出し:", headers)
        for key in ("date", "item_code", "item_name", "clicks", "orders", "sales_yen"):
            idx = pick(headers, colmap[key])
            print(f"  {key:10s} -> {headers[idx] if idx is not None else '(見つかりません)'}")
        return

    idx = {k: pick(headers, colmap[k]) for k in ("date", "item_code", "item_name", "clicks", "orders", "sales_yen")}
    if idx["sales_yen"] is None:
        sys.exit("『売上金額』の列が見つかりません。--show-columns で見出しを確認し、column_map.json に追加してください。")
    if idx["date"] is None and not args.date:
        sys.exit("日付の列がありません。--date 2026-10-09 のように日付を指定してください。")
    default_date = tl.parse_date(args.date) if args.date else None

    def cell(row, key):
        i = idx[key]
        return row[i].strip() if i is not None and i < len(row) else ""

    new_rows = []
    for row in rows[h + 1:]:
        if not any(c.strip() for c in row):
            continue
        d = tl.parse_date(cell(row, "date")) or default_date
        if d is None or cell(row, "item_name") in ("合計", "総計"):
            continue  # 日付のない行・合計行は読み飛ばす
        new_rows.append({
            "date": d.isoformat(), "item_code": cell(row, "item_code"), "item_name": cell(row, "item_name"),
            "clicks": tl.to_int(cell(row, "clicks")), "orders": tl.to_int(cell(row, "orders")),
            "sales_yen": tl.to_int(cell(row, "sales_yen")), "source": Path(args.csv_file).name,
        })

    key = lambda r: (r["date"], r["item_code"], r["item_name"])  # noqa: E731
    merged = {key(r): r for r in tl.read_csv(args.sales)}
    for r in new_rows:
        merged[key(r)] = r  # 新しい取り込みで上書き(二重計上しない)
    all_rows = sorted(merged.values(), key=lambda r: (r["date"], r["item_name"]))
    tl.write_csv(args.sales, tl.SALES_COLUMNS, all_rows)

    posts = tl.read_csv(args.posts)
    posts, unattributed = tl.attribute(posts, all_rows)
    tl.write_csv(args.posts, tl.POST_COLUMNS, posts)

    total = sum(tl.to_int(r["sales_yen"]) for r in new_rows)
    print(f"{len(new_rows)} 行を取り込みました(売上金額の合計 {total:,} 円)。")
    if unattributed:
        print(f"※投稿に紐づけられなかった売上が {unattributed:,} 円あります(目標の集計には含まれます)。")
    print("posts.csv の clicks / orders / sales_yen を更新しました。")


if __name__ == "__main__":
    main()
