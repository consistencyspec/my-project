#!/usr/bin/env python3
"""
eBay 売上・利益集計(eBay公式 Finances API + Fulfillment API)

eBay から「実際に引かれた手数料」と「入金額」を注文ごとに取得し、
自分で入力した仕入れ値・送料を引いて、本当の利益を集計します。

使い方
  初回だけ:  python3 sales_report.py --login      (eBayアカウントでアクセスを許可)
  集計:      python3 sales_report.py               (直近90日)
             python3 sales_report.py --from 2026-10-01 --to 2026-10-31
  お試し:    python3 sales_report.py --demo        (サンプルデータで動きを見る。eBayには接続しません)

流れ
  1. 実行すると costs.csv に新しい注文が追加されます(仕入れ値などは空欄)
  2. costs.csv を Excel / Numbers で開き、buy_jpy(仕入れ値)と ship_cost_jpy(発送費)を入力して保存
  3. もう一度実行すると、利益が計算されたレポートができます
"""
import argparse
import base64
import csv
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

HERE = Path(__file__).resolve().parent
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
FINANCES_URL = "https://apis.ebay.com/sell/finances/v1/transaction"
ORDERS_URL = "https://api.ebay.com/sell/fulfillment/v1/order"
SCOPES = " ".join([
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.finances",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
])
TOKEN_FILE = HERE / "token.txt"        # 許可の情報(リフレッシュトークン)。人に渡さないこと
COSTS_FILE = HERE / "costs.csv"
COST_COLUMNS = ["order_id", "line_item_id", "date", "title", "sku", "item_id", "country",
                "buy_jpy", "ship_cost_jpy", "other_jpy", "group", "memo"]


# ---------------------------------------------------------------------
# 共通
# ---------------------------------------------------------------------

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
            with urllib.request.urlopen(req, timeout=60) as res:
                return json.loads(res.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:400]}"
            if e.code == 429 or e.code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            break
        except urllib.error.URLError as e:
            last = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in last:
                last += "\n→ 証明書が入っていません。README の「よくあるエラー」を見てください。"
                break
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(last)


def num(v, default=0.0):
    try:
        return float(str(v).replace(",", "").replace("¥", "").strip())
    except (TypeError, ValueError):
        return default


def to_jpy(amount):
    """{"value": "12.34", "currency": "USD"} を円にする"""
    if not amount:
        return 0.0
    v = num(amount.get("value"))
    cur = (amount.get("currency") or "JPY").upper()
    if cur == "JPY":
        return v
    if cur == "USD":
        return v * config.USD_JPY
    rates = getattr(config, "OTHER_RATES", {})
    return v * rates.get(cur, config.USD_JPY)


# ---------------------------------------------------------------------
# 認証(ユーザーの許可)
# ---------------------------------------------------------------------

def basic_auth():
    cid, secret = env("EBAY_CLIENT_ID"), env("EBAY_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("env.txt に EBAY_CLIENT_ID と EBAY_CLIENT_SECRET を書いてください。")
    return "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()


def login():
    runame = env("EBAY_RUNAME")
    if not runame:
        sys.exit("env.txt に EBAY_RUNAME を書いてください(README の手順2-2)。")
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": env("EBAY_CLIENT_ID"), "response_type": "code",
        "redirect_uri": runame, "scope": SCOPES})
    print("1. 次のURLをブラウザで開き、eBayにログインして「同意する(Agree)」を押してください。\n")
    print(url + "\n")
    print("2. 同意したあとに表示されたページの「アドレスバーのURL」を、まるごとコピーして貼り付けてください。")
    got = input("\nURL: ").strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(got).query).get("code", [got])[0]
    body = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                                   "redirect_uri": runame}).encode()
    r = http_json(TOKEN_URL, {"Authorization": basic_auth(),
                              "Content-Type": "application/x-www-form-urlencoded"}, body)
    TOKEN_FILE.write_text(r["refresh_token"], encoding="utf-8")
    days = int(r.get("refresh_token_expires_in", 0)) // 86400
    print(f"\n許可が完了しました(約{days}日有効)。次は  python3 sales_report.py  を実行してください。")


def access_token():
    if not TOKEN_FILE.exists():
        sys.exit("まだ eBay の許可がありません。先に  python3 sales_report.py --login  を実行してください。")
    body = urllib.parse.urlencode({"grant_type": "refresh_token",
                                   "refresh_token": TOKEN_FILE.read_text(encoding="utf-8").strip(),
                                   "scope": SCOPES}).encode()
    try:
        r = http_json(TOKEN_URL, {"Authorization": basic_auth(),
                                  "Content-Type": "application/x-www-form-urlencoded"}, body)
    except RuntimeError as e:
        sys.exit(f"eBayの許可が切れたか、無効です。もう一度 --login を実行してください。\n({e})")
    return r["access_token"]


# ---------------------------------------------------------------------
# 取得
# ---------------------------------------------------------------------

def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def fetch_transactions(token, start, end):
    out, offset = [], 0
    while True:
        params = {"filter": f"transactionDate:[{iso(start)}..{iso(end)}]", "limit": 200, "offset": offset}
        data = http_json(FINANCES_URL + "?" + urllib.parse.urlencode(params),
                         {"Authorization": "Bearer " + token, "Accept": "application/json"})
        batch = data.get("transactions", [])
        out += batch
        print(f"  取引明細 {len(out)} 件")
        if len(batch) < 200:
            return out
        offset += 200


def fetch_orders(token, start, end):
    out, offset = [], 0
    while True:
        params = {"filter": f"creationdate:[{iso(start)}..{iso(end)}]", "limit": 200, "offset": offset}
        data = http_json(ORDERS_URL + "?" + urllib.parse.urlencode(params),
                         {"Authorization": "Bearer " + token, "Accept": "application/json"})
        batch = data.get("orders", [])
        out += batch
        print(f"  注文 {len(out)} 件")
        if len(batch) < 200:
            return out
        offset += 200


# ---------------------------------------------------------------------
# 集計
# ---------------------------------------------------------------------

def guess_group(title):
    t = (title or "").lower()
    for word, name in config.GROUPS:
        if word.lower() in t:
            return name
    return "その他"


def order_rows(orders):
    """注文 → 商品(行)ごとの情報"""
    rows = []
    for o in orders:
        try:
            country = o["fulfillmentStartInstructions"][0]["shippingStep"]["shipTo"]["contactAddress"]["countryCode"]
        except (KeyError, IndexError, TypeError):
            country = ""
        for li in o.get("lineItems", []):
            rows.append({
                "order_id": o.get("orderId", ""), "line_item_id": li.get("lineItemId", ""),
                "date": (o.get("creationDate") or "")[:10], "title": li.get("title", ""),
                "sku": li.get("sku", ""), "item_id": li.get("legacyItemId", ""), "country": country,
            })
    return rows


def money_by_order(transactions):
    """注文ごとの 売上(手数料前)・手数料・入金額 と、注文にひもづかない費用"""
    by_order = defaultdict(lambda: {"gross": 0.0, "fees": 0.0, "net": 0.0, "refund": 0.0, "label": 0.0})
    overhead = defaultdict(float)   # 広告費・ストア料金など(種類ごと)
    for t in transactions:
        typ = t.get("transactionType", "")
        sign = -1 if t.get("bookingEntry") == "DEBIT" else 1
        amount = to_jpy(t.get("amount")) * sign
        oid = t.get("orderId", "")
        if typ == "SALE" and oid:
            m = by_order[oid]
            m["gross"] += to_jpy(t.get("totalFeeBasisAmount"))
            m["fees"] += to_jpy(t.get("totalFeeAmount"))
            m["net"] += amount
        elif typ == "REFUND" and oid:
            by_order[oid]["refund"] += amount
            by_order[oid]["net"] += amount
        elif typ == "SHIPPING_LABEL" and oid:
            by_order[oid]["label"] += amount
            by_order[oid]["net"] += amount
        elif typ in ("PAYOUT", "TRANSFER", "WITHDRAWAL"):
            continue  # 入金(口座への振込)は利益の計算に関係ない
        elif oid and typ in ("NON_SALE_CHARGE", "DISPUTE", "ADJUSTMENT", "CREDIT"):
            by_order[oid]["net"] += amount
            by_order[oid]["fees"] -= amount if amount < 0 else 0
        else:
            label = {"NON_SALE_CHARGE": "広告費・その他の請求", "CREDIT": "返金・クレジット",
                     "ADJUSTMENT": "調整", "DISPUTE": "紛争"}.get(typ, typ or "不明")
            overhead[label] += amount
    return by_order, overhead


def read_costs():
    if not COSTS_FILE.exists():
        return {}
    with COSTS_FILE.open(encoding="utf-8-sig") as f:
        return {(r.get("order_id", ""), r.get("line_item_id", "")): r for r in csv.DictReader(f)}


def update_costs(rows):
    """新しい注文を costs.csv に追加する(入力済みの行はそのまま)"""
    costs = read_costs()
    added = 0
    for r in rows:
        key = (r["order_id"], r["line_item_id"])
        if key not in costs:
            costs[key] = {**{c: "" for c in COST_COLUMNS}, **r, "group": guess_group(r["title"])}
            added += 1
        else:
            for c in ("date", "title", "sku", "item_id", "country"):  # eBay側の情報は最新にする
                costs[key][c] = r[c] or costs[key].get(c, "")
    ordered = sorted(costs.values(), key=lambda x: x.get("date", ""), reverse=True)
    with COSTS_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COST_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(ordered)
    return costs, added


def build_report(rows, by_order, costs):
    """注文ごとの利益(複数商品の注文は、売上を商品数で按分)"""
    per_order_lines = defaultdict(int)
    for r in rows:
        per_order_lines[r["order_id"]] += 1
    lines = []
    for r in rows:
        m = by_order.get(r["order_id"])
        if not m:
            continue  # 期間内に入金明細がない注文(未払い・キャンセルなど)
        n = per_order_lines[r["order_id"]]
        c = costs.get((r["order_id"], r["line_item_id"]), {})
        buy, ship, other = num(c.get("buy_jpy"), None), num(c.get("ship_cost_jpy"), 0), num(c.get("other_jpy"), 0)
        pack = config.PACKING_COST_JPY
        net = m["net"] / n
        profit = None if buy is None else net - buy - ship - other - pack
        gross = m["gross"] / n
        lines.append({
            **r, "group": c.get("group") or guess_group(r["title"]),
            "gross": round(gross), "fees": round(m["fees"] / n), "refund": round(m["refund"] / n),
            "label": round(m["label"] / n), "net": round(net),
            "buy": buy, "ship": ship + pack + other,
            "profit": None if profit is None else round(profit),
            "margin": None if profit is None or not gross else round(profit / gross, 3),
        })
    return lines


def summarize(lines, key):
    agg = defaultdict(lambda: {"count": 0, "gross": 0, "fees": 0, "net": 0, "cost": 0, "profit": 0, "missing": 0})
    for l in lines:
        a = agg[key(l)]
        a["count"] += 1
        a["gross"] += l["gross"]
        a["fees"] += l["fees"]
        a["net"] += l["net"]
        if l["profit"] is None:
            a["missing"] += 1
        else:
            a["cost"] += (l["buy"] or 0) + l["ship"]
            a["profit"] += l["profit"]
    return agg


# ---------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------

def yen(v):
    return "-" if v is None else f"¥{v:,.0f}"


def table(title, agg, sort_by_profit=True):
    items = sorted(agg.items(), key=lambda kv: kv[1]["profit"] if sort_by_profit else kv[0], reverse=True)
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{a['count']}</td><td>{yen(a['gross'])}</td><td>{yen(a['fees'])}</td>"
        f"<td>{yen(a['net'])}</td><td>{yen(a['cost'])}</td><td class='p'>{yen(a['profit'])}</td>"
        f"<td>{(a['profit'] / a['gross'] if a['gross'] else 0):.0%}</td>"
        f"<td class='w'>{a['missing'] or ''}</td></tr>" for k, a in items)
    return (f"<h2>{title}</h2><div class='scroll'><table><tr><th></th><th>件数</th><th>売上</th><th>eBay手数料</th>"
            f"<th>入金額</th><th>仕入れ・発送</th><th>利益</th><th>利益率</th><th>未入力</th></tr>{rows}</table></div>")


def write_report(lines, overhead, start, end):
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = out / f"sales_report_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["日付", "グループ", "商品名", "SKU", "国", "売上", "eBay手数料", "返金", "ラベル代",
                    "入金額", "仕入れ値", "発送・梱包・その他", "利益", "利益率", "注文番号"])
        for l in lines:
            w.writerow([l["date"], l["group"], l["title"], l["sku"], l["country"], l["gross"], l["fees"],
                        l["refund"], l["label"], l["net"], "" if l["buy"] is None else int(l["buy"]),
                        int(l["ship"]), "" if l["profit"] is None else l["profit"],
                        "" if l["margin"] is None else f"{l['margin']:.0%}", l["order_id"]])

    total = summarize(lines, lambda l: "合計")["合計"] if lines else None
    over = sum(overhead.values())
    missing = sum(1 for l in lines if l["profit"] is None)
    final = (total["profit"] if total else 0) + over
    order_rows = "".join(
        f"<tr{' class=miss' if l['profit'] is None else ''}><td>{l['date']}</td><td>{html.escape(l['group'])}</td>"
        f"<td class='t'>{html.escape(l['title'][:70])}</td><td>{l['country']}</td><td>{yen(l['gross'])}</td>"
        f"<td>{yen(l['net'])}</td><td>{yen(l['buy'])}</td><td class='p'>{yen(l['profit'])}</td>"
        f"<td>{'' if l['margin'] is None else format(l['margin'], '.0%')}</td></tr>"
        for l in sorted(lines, key=lambda x: (x["profit"] is None, -(x["profit"] or 0))))
    over_rows = "".join(f"<li>{html.escape(k)}:{yen(v)}</li>" for k, v in overhead.items()) or "<li>なし</li>"
    html_path = out / f"sales_report_{stamp}.html"
    html_path.write_text(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>eBay利益集計 {stamp}</title>
<style>
body{{font-family:-apple-system,"Hiragino Sans",sans-serif;background:#f5f5f2;margin:0;padding:16px;color:#222}}
h1{{font-size:19px}} h2{{font-size:16px;margin-top:24px}} .sum{{color:#555;font-size:13px;line-height:1.7}}
.kpi{{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}}
.kpi div{{background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 1px 3px #0001;min-width:120px}}
.kpi b{{display:block;font-size:20px}} .kpi span{{font-size:12px;color:#777}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;background:#fff;font-size:13px;width:100%}}
th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap}}
th{{background:#fafafa}} td:first-child,th:first-child,.t{{text-align:left}} .t{{white-space:normal;min-width:220px}}
.p{{font-weight:600;color:#1e7e34}} .w{{color:#c0392b}} tr.miss td{{color:#999}}
</style></head><body>
<h1>eBay 利益集計({start:%Y-%m-%d} 〜 {end:%Y-%m-%d})</h1>
<div class="sum">手数料・入金額は eBay の明細の実際の数字です。外貨は 1ドル={config.USD_JPY}円で換算。
梱包費は1件 ¥{config.PACKING_COST_JPY:,} で計算しています。</div>
<div class="kpi">
 <div><span>販売件数</span><b>{total['count'] if total else 0}</b></div>
 <div><span>売上</span><b>{yen(total['gross'] if total else 0)}</b></div>
 <div><span>eBay手数料</span><b>{yen(total['fees'] if total else 0)}</b></div>
 <div><span>利益(注文ごとの合計)</span><b>{yen(total['profit'] if total else 0)}</b></div>
 <div><span>広告費など</span><b>{yen(over)}</b></div>
 <div><span>最終利益</span><b>{yen(final)}</b></div>
</div>
{f'<div class="sum w">仕入れ値が未入力の注文が {missing} 件あります。costs.csv に入力して、もう一度実行してください(未入力の分は利益に含まれていません)。</div>' if missing else ''}
{table('グループ別(利益の多い順)', summarize(lines, lambda l: l['group']))}
{table('月別', summarize(lines, lambda l: l['date'][:7]), sort_by_profit=False)}
{table('国別', summarize(lines, lambda l: l['country'] or '不明'))}
<h2>注文にひもづかない費用</h2><ul class="sum">{over_rows}</ul>
<h2>注文ごと(利益の多い順)</h2><div class="scroll"><table>
<tr><th>日付</th><th>グループ</th><th>商品名</th><th>国</th><th>売上</th><th>入金額</th><th>仕入れ値</th><th>利益</th><th>利益率</th></tr>
{order_rows}</table></div>
</body></html>""", encoding="utf-8")
    return csv_path, html_path, missing


# ---------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------

def demo_data():
    data = json.loads((HERE / "demo_sales.json").read_text(encoding="utf-8"))
    return data["orders"], data["transactions"]


def main():
    ap = argparse.ArgumentParser(description="eBay 売上・利益集計")
    ap.add_argument("--login", action="store_true", help="eBayアカウントでアクセスを許可する(初回のみ)")
    ap.add_argument("--demo", action="store_true", help="サンプルデータで試す")
    ap.add_argument("--from", dest="start", help="開始日 例 2026-10-01")
    ap.add_argument("--to", dest="end", help="終了日 例 2026-10-31")
    args = ap.parse_args()
    load_env(HERE / "env.txt")
    load_env(HERE / ".env")
    if args.login:
        return login()

    now = datetime.now(timezone.utc)
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc) if args.start \
        else now - timedelta(days=config.REPORT_DAYS)
    end = (datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)) if args.end else now

    global COSTS_FILE
    if args.demo:
        COSTS_FILE = HERE / "costs_demo.csv"
        orders, transactions = demo_data()
        print("サンプルデータで集計します(eBayには接続しません)")
    else:
        token = access_token()
        print(f"eBay から {start:%Y-%m-%d} 〜 {end:%Y-%m-%d} のデータを取得します")
        orders = fetch_orders(token, start - timedelta(days=30), end)  # 入金が遅れて期間に入る注文のため少し前から
        transactions = fetch_transactions(token, start, end)

    rows = order_rows(orders)
    costs, added = update_costs(rows)
    by_order, overhead = money_by_order(transactions)
    lines = build_report(rows, by_order, costs)
    csv_path, html_path, missing = write_report(lines, overhead, start, end)
    print(f"\n新しい注文 {added} 件を {COSTS_FILE.name} に追加しました。")
    if missing:
        print(f"仕入れ値が未入力の注文が {missing} 件あります → {COSTS_FILE.name} の buy_jpy(仕入れ値)と "
              "ship_cost_jpy(発送費)を入力して保存し、もう一度実行してください。")
    print(f"\n完了\n  レポート: {html_path}\n  明細CSV: {csv_path}")


if __name__ == "__main__":
    main()
