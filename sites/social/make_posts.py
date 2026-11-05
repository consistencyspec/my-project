#!/usr/bin/env python3
"""2つのサイトの最新の数字(data.json)から、Threads と X の投稿の下書きを作ります(投稿はしません)。

使い方:
  python3 sites/social/make_posts.py                 # 公開中のサイトの数字から作る
  python3 sites/social/make_posts.py --local         # 手元で作ったサイト(dist/)の数字から作る

出力: drafts/social/日付.md(内容を確かめ、《 》を自分の言葉に直してから、自分の手で投稿してください)
"""
import argparse
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES = {
    "furusato": ("https://furusato-yosan.com/data.json", ROOT / "dist" / "furusato" / "data.json"),
    "tanka": ("https://tanka-erabu.com/data.json", ROOT / "dist" / "tanka" / "data.json"),
}
THREADS_LIMIT = 500
X_LIMIT = 280          # X は、日本語1文字を2、URLを23として数える
X_URL_WEIGHT = 23


def load(name, local):
    url, path = SOURCES[name]
    if local:
        return json.loads(path.read_text(encoding="utf-8"))
    req = urllib.request.Request(url + f"?d={date.today().isoformat()}", headers={"User-Agent": "social-drafts/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode("utf-8"))


def x_length(text):
    """X の文字数の数え方(だいたい): 半角は1、日本語などは2、URLは23。"""
    total = 0
    for word in text.replace("\n", " \n ").split(" "):
        if word.startswith("http://") or word.startswith("https://"):
            total += X_URL_WEIGHT
        else:
            total += sum(1 if ord(c) < 0x1100 else 2 for c in word)
    return total + text.count(" ")


def fmt_amount(value, unit):
    if unit in ("ロール", "箱") or value >= 100:
        return f"{value:,.0f}{unit}"
    return f"{value:.1f}{unit}"


def fmt_yen(value):
    if value >= 100:
        return f"{value:,.0f}円"
    if value >= 10:
        return f"{value:.1f}円"
    return f"{value:.2f}円"


def pick(items, seed, offset=0):
    """日ごとに違うものを選ぶ(同じ日なら何度作っても同じ)。"""
    return items[(seed + offset) % len(items)] if items else None


# ---------- ふるさと納税 ----------
def furusato_genre_post(d, g, today):
    top, unit = g["top"], g["unit"]
    ratio = top["per10k"] / g["typical"] if g["typical"] else 1
    link = f"{d['url']}/{g['slug']}/"
    threads = (
        f"1万円の寄付で届く{g['short']}、今日いちばん多かったのは{fmt_amount(top['per10k'], unit)}でした(PR)\n\n"
        f"楽天ふるさと納税の{g['title']}{g['count']}件を集計。ふつうは1万円で{fmt_amount(g['typical'], unit)}前後なので、"
        f"{ratio:.1f}倍届く計算です。\n\n"
        f"{top['shop']}・寄付額{top['price']:,}円で{top['amount_text']}。\n\n"
        f"《ひとこと：選ぶときに気にしていること、去年頼んだものなど》\n\n"
        f"{today.year}年分の締め切りまで、あと{d['days_left']}日。\n"
        f"▼ほかの返礼品も並べています\n{link}\n※広告を含みます"
    )
    x = (f"1万円で届く{g['short']}、今日いちばん多いのは{fmt_amount(top['per10k'], unit)}"
         f"(ふつうは{fmt_amount(g['typical'], unit)})\n{top['shop']}・{top['price']:,}円で{top['amount_text']}\n"
         f"締め切りまであと{d['days_left']}日\n{link} (PR)")
    return {"title": f"ふるさと納税：{g['title']}の1位", "threads": threads, "x": x}


def furusato_plan_post(d, plan):
    items = "\n".join(f"・{i['short']} {i['amount_text']}" for i in plan["items"])
    man = plan["budget"] // 10000
    link = f"{d['url']}/{plan['slug']}/"
    threads = (
        f"ふるさと納税を{man}万円するなら、こんな組み合わせもできます(PR)\n\n{items}\n"
        f"→ 合計{plan['total']:,}円(「{plan['name']}」の組み合わせ)\n\n"
        f"楽天ふるさと納税の返礼品を、量が多いものから選んで予算いっぱいまで組み合わせました。\n\n"
        f"《ひとこと：わが家ならこれを入れる、など》\n\n"
        f"締め切りまであと{d['days_left']}日。\n▼ほかの組み合わせ\n{link}\n※広告を含みます"
    )
    short_items = "・".join(f"{i['short']}{i['amount_text']}" for i in plan["items"])
    x = f"ふるさと納税{man}万円の組み合わせ例\n{short_items}\n合計{plan['total']:,}円\n{link} (PR)"
    return {"title": f"ふるさと納税：{man}万円の組み合わせ", "threads": threads, "x": x}


# ---------- 日用品 ----------
def tanka_post(d, c):
    top, per = c["top"], c["per"]
    spread = c["max"] / top["unit_price"] if top["unit_price"] else 1
    link = f"{d['url']}/{c['slug']}/"
    threads = (
        f"{c['title']}、{per}あたりで比べると今日いちばん安かったのは{fmt_yen(top['unit_price'])}でした(PR)\n\n"
        f"楽天市場の送料込みの{c['title']}{c['count']}件を集計。ふつうは{fmt_yen(c['typical'])}前後、"
        f"高いものだと{fmt_yen(c['max'])}で、同じ{c['title']}でも{spread:.1f}倍の差があります。\n\n"
        f"《ひとこと：いつも買っているもの、まとめ買いの工夫など》\n\n"
        f"▼{per}あたりのランキング\n{link}\n※広告を含みます"
    )
    x = (f"{c['title']}、{per}あたり今日いちばん安いのは{fmt_yen(top['unit_price'])}"
         f"(ふつうは{fmt_yen(c['typical'])})\n楽天市場の送料込み{c['count']}件を比較\n{link} (PR)")
    return {"title": f"日用品：{c['title']}の単価", "threads": threads, "x": x}


def make_posts(furusato, tanka, today):
    seed = today.toordinal()
    posts = []
    if furusato:
        g = pick(furusato["genres"], seed)
        if g:
            posts.append(furusato_genre_post(furusato, g, today))
        plans = [p for p in furusato["plans"] if p["budget"] in (30000, 50000)]
        p = pick(plans, seed)
        if p:
            posts.append(furusato_plan_post(furusato, p))
    if tanka:
        for offset in (0, 7):  # 1日2品目
            c = pick(tanka["categories"], seed, offset)
            if c and all(c["title"] not in x["title"] for x in posts):
                posts.append(tanka_post(tanka, c))
    for p in posts:
        p["warnings"] = []
        if len(p["threads"]) > THREADS_LIMIT:
            p["warnings"].append(f"Threads用が{len(p['threads'])}文字です。500文字以内に縮めてください")
        if x_length(p["x"]) > X_LIMIT:
            p["warnings"].append(f"X用が長すぎます(目安{x_length(p['x'])}/{X_LIMIT})。少し削ってください")
    return posts


def render(posts, today, sources):
    out = [f"# SNS投稿の下書き({today.isoformat()})", "",
           "> 投稿は自動ではしません。数字を確かめ、《 》を自分の言葉に直してから、自分の手で投稿してください。",
           "> Threadsは1日1件まで(今のフォロワーの方向けの投稿が中心のため)、Xは1日1〜3件が目安です。", "",
           "データ: " + "、".join(f"{k} {v}" for k, v in sources.items()), "",
           "チェック: [ ] 1行目に(PR)がある  [ ] 《 》が残っていない  [ ] リンク先を開いて数字が同じか確かめた", ""]
    for i, p in enumerate(posts, 1):
        out += [f"## {i}. {p['title']}", ""]
        out += [f"⚠️ {w}" for w in p["warnings"]]
        out += [f"**Threads**({len(p['threads'])}文字)", "", "```", p["threads"], "```", "",
                f"**X**(目安 {x_length(p['x'])}/{X_LIMIT})", "", "```", p["x"], "```", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--local", action="store_true", help="dist/ の data.json から作る")
    ap.add_argument("--out", default=str(ROOT / "drafts" / "social"), help="出力先のフォルダ")
    ap.add_argument("--today", help="日付を指定する(テスト用)")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()

    data, sources = {}, {}
    for name in SOURCES:
        try:
            data[name] = load(name, args.local)
            sources[name] = data[name].get("updated", "")
        except Exception as e:  # 片方のサイトが読めなくても、もう片方の下書きは作る
            print(f"  ! {name} の数字を読めませんでした: {e}", file=sys.stderr)
            data[name] = None
    if not any(data.values()):
        sys.exit("どちらのサイトの数字も読めませんでした。")
    posts = make_posts(data["furusato"], data["tanka"], today)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{today.isoformat()}.md"
    path.write_text(render(posts, today, sources), encoding="utf-8")
    print(f"下書きを{len(posts)}件作りました: {path}")


if __name__ == "__main__":
    main()
