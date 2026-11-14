#!/usr/bin/env python3
"""Threads API で、自分の投稿の数字(閲覧数・いいね・返信など)を取得して記録します。

使い方:
  python3 tracking/threads_fetch.py            # 直近30件を取得して threads_insights.csv を更新し、要約を表示
  python3 tracking/threads_fetch.py --limit 50

トークンについて:
  クラウド環境では、トークンは環境の「ネットワークシークレット」に保存されていて、
  graph.threads.net への通信に自動で付きます(このスクリプトはトークンを読みません)。
  手元のパソコンで使う場合は、環境変数 THREADS_ACCESS_TOKEN にトークンを入れてください。
"""
import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "https://graph.threads.net/v1.0"
JST = timezone(timedelta(hours=9))
OUT = Path(__file__).resolve().parent / "threads_insights.csv"
COLUMNS = ["post_id", "posted_jst", "hour_jst", "text_head", "views", "likes", "replies", "reposts",
           "quotes", "shares", "like_rate_pct", "permalink", "fetched_jst"]
METRICS = "views,likes,replies,reposts,quotes,shares"


def get(path, **params):
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        if e.code in (400, 401, 403):
            sys.exit(f"Threads API がエラーを返しました(HTTP {e.code})。トークンの期限切れの可能性があります。"
                     f"Meta の『ユーザートークン生成ツール』で作り直し、環境の設定で入れ直してください。\n{body}")
        raise


def fetch(limit):
    posts = get("me/threads", fields="id,text,timestamp,permalink,media_product_type", limit=limit).get("data", [])
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    rows = []
    for p in posts:
        if p.get("media_product_type") not in (None, "THREADS"):
            continue
        ins = get(f"{p['id']}/insights", metric=METRICS).get("data", [])
        m = {x["name"]: x["values"][0]["value"] for x in ins if x.get("values")}
        t = datetime.strptime(p["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).astimezone(JST)
        views = m.get("views", 0)
        rows.append({
            "post_id": p["id"], "posted_jst": t.strftime("%Y-%m-%d %H:%M"), "hour_jst": t.hour,
            "text_head": (p.get("text") or "").replace("\n", " ")[:40],
            **{k: m.get(k, 0) for k in ("views", "likes", "replies", "reposts", "quotes", "shares")},
            "like_rate_pct": round(m.get("likes", 0) / views * 100, 2) if views else 0,
            "permalink": p.get("permalink", ""), "fetched_jst": now,
        })
    return rows


def save(rows):
    old = {}
    if OUT.exists():
        with open(OUT, newline="", encoding="utf-8-sig") as f:
            old = {r["post_id"]: r for r in csv.DictReader(f)}
    for r in rows:
        old[r["post_id"]] = r  # 最新の数字で上書き
    merged = sorted(old.values(), key=lambda r: r["posted_jst"], reverse=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(merged)


def summary(rows):
    if not rows:
        return "投稿が見つかりませんでした。"
    by_views = sorted(rows, key=lambda r: int(r["views"]), reverse=True)
    lines = ["## 閲覧数の多い投稿(上位5件)"]
    for r in by_views[:5]:
        lines.append(f"- {r['posted_jst']} {int(r['views']):,}回 いいね{r['likes']} 返信{r['replies']}"
                     f"(いいね率{r['like_rate_pct']}%){r['text_head']}")
    lines.append("## 閲覧数の少ない投稿(下位3件)")
    for r in by_views[-3:]:
        lines.append(f"- {r['posted_jst']} {int(r['views']):,}回 {r['text_head']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Threads の投稿の数字を取得します")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()
    rows = fetch(args.limit)
    if not args.no_save:
        save(rows)
    print(summary(rows))


if __name__ == "__main__":
    main()
