#!/usr/bin/env python3
"""1週間分のThreads投稿の下書きを作ります(投稿は自動では行いません)。

使い方の例:
  python3 scripts/generate_drafts.py --start 2026-10-02 --days 7        # 本番(楽天APIを使う)
  python3 scripts/generate_drafts.py --start 2026-10-02 --days 7 --demo # 練習(ダミー商品。APIを使わない)

出力: output/drafts_開始日.md (人の目で確認・修正してから、自分で投稿してください)
"""
import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tracking"))

import post_templates as pt  # noqa: E402
import rakuten_client as rc  # noqa: E402
import tracklib as tl  # noqa: E402

WEEKDAY = "月火水木金土日"


def load_calendar(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r["type_id"]]


def load_demo_items():
    import json
    return rc.parse_items(json.loads((ROOT / "scripts" / "sample_items.json").read_text(encoding="utf-8")))


def pick_items(row, settings, demo, used_codes, demo_items):
    type_id = int(row["type_id"])
    count = pt.ITEM_COUNT[type_id]
    if count == 0:
        return []
    if demo:
        pool = [i for i in demo_items if i.item_code not in used_codes] or demo_items  # デモは足りなければ再利用
        return pool[:count]
    items = rc.search_items(
        settings, row["keyword"], row["min_price"] or None, row["max_price"] or None,
        hits=30, sort=pt.SORT.get(type_id, "standard"))
    return rc.select_items(items, count, exclude_codes=used_codes)


def make_draft(row, day, items):
    type_id = int(row["type_id"])
    warnings = []
    needed = pt.ITEM_COUNT[type_id]
    if len(items) < needed:
        warnings.append(f"条件に合う商品が足りません({len(items)}/{needed}件)。calendar.csv のキーワードや価格帯を見直してください。この日の下書きは作っていません")
        return {"main": "(商品が見つからなかったため下書きなし)", "reply": "", "warnings": warnings}
    main, reply = pt.build(type_id, items, day, row["keyword"])
    if row["ad"] == "1" and not main.startswith("【PR】"):
        warnings.append("広告投稿なのに先頭に【PR】がありません")
    for label, text in (("本文", main), ("リプライ", reply)):
        if pt.estimated_length(text) > pt.LIMIT:
            warnings.append(f"{label}が500文字を超える見込みです({pt.estimated_length(text)}文字)。短くしてください")
    if pt.placeholders(main + reply):
        warnings.append(f"《 》の書き換え箇所が {len(pt.placeholders(main + reply))} か所あります。必ず自分の言葉に置き換えてください")
    return {"main": main, "reply": reply, "warnings": warnings}


def render(drafts, start, demo):
    out = [f"# 投稿下書き({start} から)", ""]
    if demo:
        out += ["> ⚠️ **デモモードです。商品とリンクはダミーです。このまま投稿しないでください。**", ""]
    out += ["> 確認してから、**自分の手で** Threads に投稿してください(自動投稿はしません)。",
            "> 《 》の部分は必ず自分の言葉に書き換えてください。", "",
            "全体のチェック: [ ] 広告投稿の先頭に【PR】がある  [ ] 《 》が残っていない  "
            "[ ] 価格・在庫を商品ページで確認した  [ ] 使っていない物を「使った」と書いていない", ""]
    for d in drafts:
        row, day = d["row"], d["day"]
        ad = "広告あり(【PR】必須)" if row["ad"] == "1" else "広告なし"
        out += ["---", "", f"## {day.isoformat()}({WEEKDAY[day.weekday()]}) {row['type_name']} / {ad}",
                f"- 投稿ID: `{d['post_id']}`"]
        if row["keyword"]:
            out.append(f"- 検索キーワード: {row['keyword']}({row['min_price']}〜{row['max_price']}円)")
        for it in d["items"]:
            out.append(f"- 商品: {it.name}({it.shop}) {it.price:,}円 ★{it.review_average:.1f}({it.review_count}件)")
        for w in d["warnings"]:
            out.append(f"- ⚠️ {w}")
        out += ["", "### 本文(コピーして貼る)", "```text", d["main"], "```",
                f"文字数の見込み: {pt.estimated_length(d['main'])}/500", ""]
        if d["reply"]:
            out += ["### リプライ(リンク用。本文に返信する形で投稿)", "```text", d["reply"], "```",
                    f"文字数の見込み: {pt.estimated_length(d['reply'])}/500", ""]
        out += ["投稿したら: `tracking/posts.csv` の該当行を `status=posted`、`posted_date` に投稿日を入れる", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Threads投稿の下書きを作ります")
    ap.add_argument("--start", default=date.today().isoformat(), help="開始日 (例: 2026-10-02)")
    ap.add_argument("--days", type=int, default=7, help="何日分作るか(初期値 7)")
    ap.add_argument("--demo", action="store_true", help="ダミー商品で動作確認する(APIを使わない)")
    ap.add_argument("--calendar", default=str(ROOT / "scripts" / "calendar.csv"))
    ap.add_argument("--posts", default=str(tl.POSTS_CSV), help="投稿記録CSV")
    ap.add_argument("--out-dir", default=str(ROOT / "output"))
    ap.add_argument("--no-track", action="store_true", help="posts.csv に記録しない")
    args = ap.parse_args()

    start = date.fromisoformat(args.start)
    end = start + timedelta(days=args.days - 1)
    rc.load_env(ROOT / ".env")
    settings = rc.get_settings()
    if not args.demo and settings["missing"]:
        sys.exit("環境変数が足りません: " + ", ".join(settings["missing"]) +
                 "\n.env.example をコピーして .env を作り、値を入れてください。練習だけなら --demo を付けてください。")

    posts = tl.read_csv(args.posts)
    # 今回作り直す期間の下書きは「使用済み」に数えない(同じ期間の再実行で商品が入れ替わらないように)
    def in_range(p):
        d = tl.parse_date(p.get("planned_date"))
        return d is not None and start <= d <= end and p.get("status") == "draft"
    used = {c for p in posts if not in_range(p) for c in str(p.get("item_code", "")).split("|") if c}
    by_id = {p["post_id"]: p for p in posts}
    demo_items = load_demo_items() if args.demo else []

    rows = [r for r in load_calendar(args.calendar) if start <= date.fromisoformat(r["date"]) <= end]
    if not rows:
        sys.exit(f"{start}〜{end} に投稿予定がありません(calendar.csv を確認してください)")

    drafts = []
    for n, row in enumerate(rows, 1):
        day = date.fromisoformat(row["date"])
        try:
            items = pick_items(row, settings, args.demo, used, demo_items)
        except rc.RakutenError as e:
            sys.exit(str(e))
        used.update(i.item_code for i in items)  # 同じ商品を重複して投稿しない
        d = make_draft(row, day, items)
        d.update(row=row, day=day, items=items, post_id=f"P{day:%Y%m%d}")
        drafts.append(d)
        for w in d["warnings"]:
            print(f"[注意] {row['date']} {row['type_name']}: {w}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"drafts_{start.isoformat()}{'_demo' if args.demo else ''}.md"
    out_path.write_text(render(drafts, start.isoformat(), args.demo), encoding="utf-8")

    if not args.no_track and not args.demo:
        for d in drafts:
            row = d["row"]
            old = by_id.get(d["post_id"])
            if old is not None and old.get("status") != "draft":
                continue  # 投稿済み・見送り済みの記録は書き換えない
            if old is not None:
                posts.remove(old)
            posts.append({
                "post_id": d["post_id"], "planned_date": row["date"], "posted_date": "", "status": "draft",
                "type_id": row["type_id"], "type_name": row["type_name"], "ad": row["ad"],
                "item_code": "|".join(i.item_code for i in d["items"]),
                "item_name": " | ".join(pt.shorten(i.name, 40) for i in d["items"]),
                "price": "|".join(str(i.price) for i in d["items"]),
            })
        posts.sort(key=lambda p: p.get("planned_date", ""))
        tl.write_csv(args.posts, tl.POST_COLUMNS, posts)
        print(f"投稿記録を更新しました: {args.posts}")
    print(f"下書きを書き出しました: {out_path}({len(drafts)}件)")


if __name__ == "__main__":
    main()
