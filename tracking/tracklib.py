"""記録・集計で共通して使う部品(プログラミングの知識は不要です)。

posts.csv  : 投稿1件=1行の記録表(スプレッドシートで開けます)
sales_daily.csv : 楽天アフィリエイト管理画面のCSVから取り込んだ日別の成果
config.json: 目標金額などの設定
"""
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path

TRACKING_DIR = Path(__file__).resolve().parent
POSTS_CSV = TRACKING_DIR / "posts.csv"
SALES_CSV = TRACKING_DIR / "sales_daily.csv"
CONFIG_JSON = TRACKING_DIR / "config.json"

POST_COLUMNS = [
    "post_id", "planned_date", "posted_date", "status", "type_id", "type_name",
    "ad", "item_code", "item_name", "price", "impressions", "likes", "replies",
    "clicks", "orders", "sales_yen", "notes",
]
SALES_COLUMNS = ["date", "item_code", "item_name", "clicks", "orders", "sales_yen", "source"]


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, columns, rows):
    # Excel / Google スプレッドシートで文字化けしないよう BOM 付き UTF-8 で保存
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def load_config(path=CONFIG_JSON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_int(value, default=0):
    if value is None:
        return default
    text = re.sub(r"[,\s円件回]", "", str(value))
    if text == "":
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


_DATE_PATTERNS = [
    r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})",
    r"(\d{4})年(\d{1,2})月(\d{1,2})日",
]


def parse_date(value):
    """'2026/10/05' '2026-10-05' '2026年10月5日 12:00' などを date に変換。失敗したら None。"""
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) and not isinstance(value, datetime) else value.date()
    text = str(value or "").strip()
    for pattern in _DATE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def post_effective_date(post):
    """成果の紐づけに使う日付。投稿済みなら投稿日、なければ None。"""
    if post.get("status") != "posted":
        return None
    return parse_date(post.get("posted_date")) or parse_date(post.get("planned_date"))


def _name_key(name):
    return re.sub(r"\s+", "", str(name or ""))[:12]


def attribute(posts, sales_rows):
    """成果(sales_rows)を、いちばん近い過去の投稿に割り当てる。

    戻り値: (posts 更新後, 割り当てできなかった売上の合計)
    ・商品コード、または商品名の先頭12文字が一致する投稿を探す
    ・成果の日付以前に投稿された投稿のうち、いちばん新しいものに全部を割り当てる
    ・同じ商品を複数回投稿していると、新しい方に集まる(目安としての簡易ルールです)
    """
    for p in posts:
        p["clicks"], p["orders"], p["sales_yen"] = 0, 0, 0
    unattributed = 0
    for row in sales_rows:
        row_date = parse_date(row.get("date"))
        code = (row.get("item_code") or "").strip()
        name_key = _name_key(row.get("item_name"))
        best = None
        for p in posts:
            p_date = post_effective_date(p)
            if p_date is None or (row_date and p_date > row_date):
                continue
            codes = {c.strip() for c in str(p.get("item_code", "")).split("|") if c.strip()}
            names = [_name_key(n) for n in str(p.get("item_name", "")).split("|") if n.strip()]
            hit = (code and code in codes) or (name_key and any(
                n and (n == name_key or n in name_key or name_key in n) for n in names))
            if hit and (best is None or p_date >= post_effective_date(best)):
                best = p
        if best is None:
            unattributed += to_int(row.get("sales_yen"))
            continue
        best["clicks"] = to_int(best["clicks"]) + to_int(row.get("clicks"))
        best["orders"] = to_int(best["orders"]) + to_int(row.get("orders"))
        best["sales_yen"] = to_int(best["sales_yen"]) + to_int(row.get("sales_yen"))
    return posts, unattributed
