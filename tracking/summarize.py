#!/usr/bin/env python3
"""週次・月次の成果をまとめ、最終目標(12月の売上金額)までの進み具合を表示します。

使い方:
  python3 tracking/summarize.py                  # 今日を基準にしたレポート
  python3 tracking/summarize.py --today 2026-10-10   # 基準日を指定(毎週土曜の報告はこれ)
  python3 tracking/summarize.py --no-save        # レポートファイルを保存しない

「先週」= 基準日の前日から7日間。レポートは tracking/reports/ にも保存されます。
"""
import argparse
import calendar
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tracklib as tl  # noqa: E402

MIN_POSTS_FOR_VERDICT = 3  # 判定に必要な最低投稿数


def month_key(d):
    return f"{d.year}-{d.month:02d}"


def total(rows, field, start=None, end=None):
    s = 0
    for r in rows:
        d = tl.parse_date(r.get("date"))
        if d and (start is None or d >= start) and (end is None or d <= end):
            s += tl.to_int(r.get(field))
    return s


def yen(n):
    return f"{int(n):,}円"


def bar(ratio, width=20):
    filled = max(0, min(width, int(round(ratio * width))))
    return "█" * filled + "░" * (width - filled)


def months_between(d, target_month):
    ty, tm = map(int, target_month.split("-"))
    return (ty - d.year) * 12 + (tm - d.month)


def type_table(posts):
    """型ごとの成績と、増やす/継続/やめる の判定。"""
    stats = defaultdict(lambda: {"posts": 0, "clicks": 0, "orders": 0, "sales": 0, "ad": 0})
    for p in posts:
        if p.get("status") != "posted":
            continue
        s = stats[p["type_name"]]
        s["posts"] += 1
        s["ad"] = p.get("ad") == "1"
        s["clicks"] += tl.to_int(p.get("clicks"))
        s["orders"] += tl.to_int(p.get("orders"))
        s["sales"] += tl.to_int(p.get("sales_yen"))
    ad_types = {n: s for n, s in stats.items() if s["ad"]}
    ranked = sorted(ad_types, key=lambda n: (ad_types[n]["sales"], ad_types[n]["clicks"]) , reverse=True)
    eligible = [n for n in ranked if ad_types[n]["posts"] >= MIN_POSTS_FOR_VERDICT]
    top = set(eligible[: max(1, len(eligible) // 3)]) if eligible else set()
    lines = []
    for n, s in stats.items():
        if not s["ad"]:
            verdict = "(広告なし。フォロワーづくり用。表示回数・いいねで判断)"
        elif s["posts"] < MIN_POSTS_FOR_VERDICT:
            verdict = f"様子見(あと{MIN_POSTS_FOR_VERDICT - s['posts']}本たまったら判定)"
        elif s["clicks"] == 0 and s["sales"] == 0:
            verdict = "やめる/作り直す(クリックも売上もゼロ)"
        elif n in top and (s["sales"] > 0 or s["clicks"] > 0):
            verdict = "増やす(上位)"
        else:
            verdict = "継続(改善して再挑戦)"
        lines.append((n, s, verdict))
    lines.sort(key=lambda x: (x[1]["sales"], x[1]["clicks"]), reverse=True)
    return lines


def kpi_section(posts, followers, cfg, today):
    """フォロワー数と、1投稿あたりの表示回数(売上の元になる数字)を、今月の目安と比べる。"""
    goal = cfg.get("kpi_milestones", {}).get(month_key(today), {})
    out = ["", "## フォロワーと表示回数(売上の元になる数字)"]
    dated = sorted((d, r) for r in followers if (d := tl.parse_date(r.get("date"))) and d <= today)
    if dated:
        d, r = dated[-1]
        n = tl.to_int(r.get("followers"))
        line = f"- フォロワー数: **{n:,}人**({d.month}/{d.day} 時点)"
        if goal.get("followers"):
            line += f" / 今月の目安 {goal['followers']:,}人 {bar(n / goal['followers'], 10)} {n / goal['followers']:.0%}"
        out.append(line)
        if len(dated) >= 2:
            pd_, pr = dated[-2]
            out.append(f"- 前回({pd_.month}/{pd_.day})から {n - tl.to_int(pr.get('followers')):+,}人")
    else:
        out.append("- フォロワー数の記録がありません。`tracking/followers.csv` に土曜ごとに1行追加してください。")
    start = today - timedelta(days=28)
    imps = [tl.to_int(p.get("impressions")) for p in posts
            if p.get("status") == "posted" and p.get("ad") == "1" and str(p.get("impressions", "")).strip()
            and (d := tl.post_effective_date(p)) and start <= d < today]
    if imps:
        avg = sum(imps) / len(imps)
        line = f"- 広告投稿1本あたりの表示回数(直近4週・{len(imps)}本の平均): **{avg:,.0f}回**"
        if goal.get("avg_impressions"):
            line += f" / 今月の目安 {goal['avg_impressions']:,}回 {bar(avg / goal['avg_impressions'], 10)} {avg / goal['avg_impressions']:.0%}"
        out.append(line)
    else:
        out.append("- 表示回数の記録がありません。Threadsのインサイトで見て、posts.csv の impressions に入れてください。")
    return out


def build_report(posts, sales, cfg, today, followers=()):
    target = cfg["target_yen"]
    target_month = cfg["target_month"]
    ms = cfg.get("milestones", {})
    wk_end = today - timedelta(days=1)
    wk_start = today - timedelta(days=7)
    mkey = month_key(today)
    m_start = today.replace(day=1)
    m_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    wk_sales = total(sales, "sales_yen", wk_start, wk_end)
    wk_clicks = total(sales, "clicks", wk_start, wk_end)
    wk_orders = total(sales, "orders", wk_start, wk_end)
    m_sales = total(sales, "sales_yen", m_start, today)
    m_clicks = total(sales, "clicks", m_start, today)
    m_orders = total(sales, "orders", m_start, today)
    run28 = total(sales, "sales_yen", today - timedelta(days=28), wk_end)
    run_month = run28 * 30 / 28

    out = [f"# 週次レポート({today.isoformat()} 基準)", ""]
    out += [f"## 先週({wk_start.month}/{wk_start.day}〜{wk_end.month}/{wk_end.day})",
            f"- 売上金額: **{yen(wk_sales)}**(クリック {wk_clicks} / 注文 {wk_orders} 件)"]
    posted_wk = [p for p in posts if (d := tl.post_effective_date(p)) and wk_start <= d <= wk_end]
    out.append(f"- 先週の投稿: {len(posted_wk)} 本")
    out += ["", f"## 今月({mkey}) の進み具合"]
    m_goal = ms.get(mkey)
    out.append(f"- 今月の売上金額: **{yen(m_sales)}**(クリック {m_clicks} / 注文 {m_orders} 件)")
    if m_goal:
        out.append(f"- 今月の通過点 {yen(m_goal)} に対して: {bar(m_sales / m_goal)} {m_sales / m_goal:.0%}")
    days_left = (m_end - today).days + 1
    out += ["", f"## 最終目標(売上金額 {yen(target)} / {target_month})",
            f"- 直近4週のペースを1か月に換算: **{yen(run_month)}**(目標の {run_month / target:.1%})",
            f"- 目標月 {target_month} まであと約 {max(months_between(today, target_month), 0)} か月"]
    if target_month == mkey:
        out.append(f"- 今月の残り {days_left} 日で、目標まであと {yen(max(target - m_sales, 0))}"
                   f"(1日あたり {yen(max(target - m_sales, 0) / max(days_left, 1))} 必要)")
    ml = months_between(today, target_month)
    if run_month > 0 and ml > 0:
        need = (target / run_month) ** (1 / ml) - 1
        out.append(f"- 目標月に届くには、毎月 **{need:.0%}** ずつ売上が伸び続ける必要があります"
                   f"{'(現実的には非常に厳しい水準です)' if need > 1.0 else ''}")
    elif run_month == 0:
        out.append("- まだ売上データがありません(CSVの取り込みが未実施か、売上がゼロ)")
    out += kpi_section(posts, followers, cfg, today)
    out += ["", "## 型ごとの成績(投稿済みのもの)"]
    table = type_table(posts)
    if not table:
        out.append("- まだ投稿済みの記録がありません。投稿したら posts.csv の status を posted に。")
    else:
        out += ["| 型 | 投稿数 | クリック | 注文 | 売上金額 | 判定 |", "|---|---:|---:|---:|---:|---|"]
        for n, s, v in table:
            out.append(f"| {n} | {s['posts']} | {s['clicks']} | {s['orders']} | {yen(s['sales'])} | {v} |")
    out += ["", "## 来週のやること(自動提案)"]
    out += suggestions(table, posts, sales, today, wk_start, wk_end)
    return "\n".join(out) + "\n"


def suggestions(table, posts, sales, today, wk_start, wk_end):
    s = []
    drafts = [p for p in posts if p.get("status") == "draft" and (tl.parse_date(p.get("planned_date")) or today) < today]
    if drafts:
        s.append(f"- 投稿予定日を過ぎた下書きが {len(drafts)} 件あります。投稿したなら status を posted に、やめたなら skipped に。")
    if not sales:
        s.append("- 楽天アフィリエイト管理画面のCSVをダウンロードして取り込みましょう(README『週のルーティン』参照)。")
    add = [n for n, _, v in table if v.startswith("増やす")]
    stop = [n for n, _, v in table if v.startswith("やめる")]
    if add:
        s.append(f"- 来週は『{'・'.join(add)}』の投稿を増やす(calendar.csv の型を差し替え)。")
    if stop:
        s.append(f"- 『{'・'.join(stop)}』は一度やめるか、切り口(商品・書き出し)を変えて作り直す。")
    if total(sales, "clicks", wk_start, wk_end) == 0 and sales:
        s.append("- クリックがゼロ。リンクの置き場所(リプ欄)・書き出し1行目・投稿時間帯を変えて試す。")
    s.append("- 下書きを作る: `python3 scripts/generate_drafts.py --start 次の開始日 --days 7`")
    return s


def main():
    ap = argparse.ArgumentParser(description="成果の集計と進捗レポート")
    ap.add_argument("--today", help="基準日 (例: 2026-10-10)。省略すると今日")
    ap.add_argument("--posts", default=str(tl.POSTS_CSV))
    ap.add_argument("--sales", default=str(tl.SALES_CSV))
    ap.add_argument("--config", default=str(tl.CONFIG_JSON))
    ap.add_argument("--followers", default=str(tl.FOLLOWERS_CSV))
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    posts = tl.read_csv(args.posts)
    sales = tl.read_csv(args.sales)
    posts, _ = tl.attribute(posts, sales)
    followers = tl.read_csv(args.followers)
    report = build_report(posts, sales, tl.load_config(args.config), today, followers)
    print(report)
    if not args.no_save:
        out = Path(args.posts).resolve().parent / "reports"
        out.mkdir(exist_ok=True)
        (out / f"report_{today.isoformat()}.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
