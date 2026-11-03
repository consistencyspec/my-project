#!/usr/bin/env python3
"""
eBay 相場・競合調査(eBay公式 Browse API を使用)

keywords.txt の各キーワードについて、eBay(アメリカ)の「出品中」の商品を調べ、
  ・出品数(全体 / 日本から出品されているもの)
  ・価格(送料込み)の最安・中央値
  ・その中央値で売れたときの「仕入れ上限価格(円)」
を一覧にします。

「売れた価格(Sold)」は Browse API では取れないため、レポートの Terapeak(eBay公式・無料)
リンクから確認してください。メルカリの売り切れ検索リンクも付けています(手動で開くだけです)。

標準ライブラリだけで動きます。
"""
import base64
import csv
import html
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import config
import profit

HERE = Path(__file__).resolve().parent
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


def load_env(path):
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(name):
    v = os.environ.get(name, "").strip()
    return "" if (not v or v.startswith("ここに")) else v


def http_json(url, headers, data=None):
    last = ""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}"
            if e.code == 429 or e.code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            break
        except urllib.error.URLError as e:
            last = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in last:
                break
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(last)


def get_token():
    cid, secret = env("EBAY_CLIENT_ID"), env("EBAY_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("env.txt に EBAY_CLIENT_ID(App ID)と EBAY_CLIENT_SECRET(Cert ID)を書いてください。README の手順2を参照。")
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials",
                                   "scope": "https://api.ebay.com/oauth/api_scope"}).encode()
    r = http_json(TOKEN_URL, {"Authorization": "Basic " + basic,
                              "Content-Type": "application/x-www-form-urlencoded"}, body)
    return r["access_token"]


def search(token, keyword, japan_only=False):
    filters = [f"price:[{config.MIN_PRICE_USD}..],priceCurrency:USD", "buyingOptions:{FIXED_PRICE|AUCTION}"]
    if japan_only:
        filters.append("itemLocationCountry:JP")
    params = {"q": keyword, "limit": 200, "filter": ",".join(filters)}
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    return http_json(url, {"Authorization": "Bearer " + token,
                           "X-EBAY-C-MARKETPLACE-ID": config.MARKETPLACE,
                           "Accept-Language": "en-US"})


def landed_prices(data):
    """送料込みの価格(ドル)のリスト"""
    out = []
    for it in data.get("itemSummaries", []):
        try:
            p = float(it["price"]["value"])
        except (KeyError, TypeError, ValueError):
            continue
        ship = 0.0
        for so in it.get("shippingOptions") or []:
            try:
                ship = float(so["shippingCost"]["value"])
                break
            except (KeyError, TypeError, ValueError):
                pass
        out.append(round(p + ship, 2))
    return out


def summarize(keyword, all_data, jp_data):
    prices = landed_prices(jp_data) or landed_prices(all_data)
    med = round(statistics.median(prices), 2) if prices else None
    low = min(prices) if prices else None
    total = all_data.get("total", 0)
    jp = jp_data.get("total", 0)
    return {
        "keyword": keyword,
        "total": total,
        "jp": jp,
        "jp_share": round(jp / total, 2) if total else 0,
        "low": low,
        "median": med,
        # 送料込み中央値を「商品代」、送料0として計算(送料無料出品が多いため)
        "max_buy": profit.max_buy_price(med) if med else None,
        "sample": [it.get("title", "") for it in jp_data.get("itemSummaries", [])[:3]],
    }


def links(keyword):
    q = urllib.parse.quote(keyword)
    return {
        "terapeak": f"https://www.ebay.com/sh/research?marketplace=EBAY-US&keywords={q}&dayRange=90&tabName=SOLD",
        "ebay_sold": f"https://www.ebay.com/sch/i.html?_nkw={q}&LH_Sold=1&LH_Complete=1",
        "ebay_jp": f"https://www.ebay.com/sch/i.html?_nkw={q}&LH_PrefLoc=99&_salic=104",
    }


def read_keywords(path):
    """keywords.txt:1行に「eBayで検索する英語キーワード | メルカリで探す日本語(任意)」"""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        en, _, ja = line.partition("|")
        out.append((en.strip(), ja.strip()))
    return out


def write_report(rows, outdir):
    outdir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = outdir / f"ebay_research_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["キーワード", "メルカリ検索語", "出品数(全体)", "日本からの出品数", "日本の割合",
                    "最安USD(送料込)", "中央値USD(送料込)", "仕入れ上限(円)", "Terapeak(売れた実績)"])
        for r in rows:
            w.writerow([r["keyword"], r["ja"], r["total"], r["jp"], f"{r['jp_share']:.0%}", r["low"] or "",
                        r["median"] or "", r["max_buy"] if r["max_buy"] is not None else "",
                        links(r["keyword"])["terapeak"]])
    cards = []
    for r in rows:
        lk = links(r["keyword"])
        mer = ("https://jp.mercari.com/search?keyword=" + urllib.parse.quote(r["ja"]) + "&status=on_sale&sort=price&order=asc") if r["ja"] else ""
        maxbuy = f"<b>¥{r['max_buy']:,}</b> 以下で仕入れれば目標達成" if r["max_buy"] else "利益が出にくい価格帯"
        cards.append(f"""
<div class="card">
  <div class="kw">{html.escape(r['keyword'])}{(' / ' + html.escape(r['ja'])) if r['ja'] else ''}</div>
  <div class="nums">中央値 <b>${r['median'] or '-'}</b>(最安 ${r['low'] or '-'}・送料込) → {maxbuy}</div>
  <div class="meta">出品数 {r['total']:,} 件 ・ うち日本から {r['jp']:,} 件({r['jp_share']:.0%})</div>
  <div class="meta">例:{html.escape(' / '.join(s[:50] for s in r['sample']))}</div>
  <div class="links"><a href="{lk['terapeak']}" target="_blank">Terapeak(売れた実績)</a>
  <a href="{lk['ebay_sold']}" target="_blank">eBay Sold</a>
  <a href="{lk['ebay_jp']}" target="_blank">日本からの出品</a>
  {f'<a href="{html.escape(mer)}" target="_blank">メルカリ(安い順)</a>' if mer else ''}</div>
</div>""")
    html_path = outdir / f"ebay_research_{stamp}.html"
    html_path.write_text(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>eBay相場 {stamp}</title>
<style>
body{{font-family:-apple-system,"Hiragino Sans",sans-serif;background:#f5f5f2;margin:0;padding:16px;color:#222}}
h1{{font-size:18px}} .sum{{color:#555;font-size:13px;line-height:1.6;margin-bottom:12px}}
.card{{background:#fff;border-radius:10px;padding:12px;margin-bottom:10px;box-shadow:0 1px 3px #0001}}
.kw{{font-weight:600;margin-bottom:6px}} .nums b{{font-size:15px;color:#1e7e34}}
.meta{{font-size:12px;color:#777;margin:3px 0}} .links a{{display:inline-block;margin:4px 10px 0 0;font-size:13px}}
</style></head><body>
<h1>eBay 相場・競合調査(出品中の価格)</h1>
<div class="sum">{stamp} ・ 1ドル={config.USD_JPY}円 ・ 目標:利益¥{config.MIN_PROFIT_JPY:,}以上かつ利益率{config.MIN_MARGIN:.0%}以上<br>
仕入れ上限が高い順。<b>出品中の価格は「売れる価格」とは限りません。</b>必ず Terapeak で売れた件数と価格を確認してから仕入れてください。</div>
{''.join(cards)}
</body></html>""", encoding="utf-8")
    return csv_path, html_path


def main():
    load_env(HERE / "env.txt")
    load_env(HERE / ".env")
    kws = read_keywords(HERE / "keywords.txt")
    token = get_token()
    rows = []
    for n, (en, ja) in enumerate(kws, 1):
        try:
            all_data = search(token, en)
            time.sleep(0.5)
            jp_data = search(token, en, japan_only=True)
            time.sleep(0.5)
        except RuntimeError as e:
            print(f"[{n}/{len(kws)}] ! {en}: {e}")
            continue
        r = summarize(en, all_data, jp_data)
        r["ja"] = ja
        rows.append(r)
        print(f"[{n}/{len(kws)}] 中央値 ${r['median'] or '-'} 仕入れ上限 ¥{r['max_buy'] or 0:,}  出品{r['total']}(日本{r['jp']})  {en}")
    rows.sort(key=lambda r: r["max_buy"] or 0, reverse=True)
    csv_path, html_path = write_report(rows, HERE / "output")
    print(f"\n完了\n  一覧: {csv_path}\n  レポート: {html_path}")


if __name__ == "__main__":
    main()
