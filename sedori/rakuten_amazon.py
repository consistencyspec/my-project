#!/usr/bin/env python3
"""
楽天 → Amazon(FBA) 価格差チェック

  1. 楽天市場の公式API(商品検索API)で商品を集める
  2. 商品名・説明文から JAN コードを取り出す(JANがない商品は比較できないので除外)
  3. 楽天の実質仕入れ値(価格 + 送料 − ポイント)を計算する
  4. Amazon側を調べる
     - 自動モード:Amazon公式の SP-API で、カート価格・手数料・ランキング・出品制限を取得
     - 手動モード:SP-API未接続なら「Amazonでいくら以上で売れれば利益が出るか(損益分岐の価格)」を出す
  5. output/ フォルダに CSV(全件)と HTML(候補)を出力する

標準ライブラリだけで動きます(pip install は不要)。
サイトの画面を読み取る「スクレイピング」はしません。公式APIだけを使います。
"""
import csv
import html
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import config

HERE = Path(__file__).resolve().parent
RAKUTEN_ENDPOINT = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
SPAPI_ENDPOINT = "https://sellingpartnerapi-fe.amazon.com"   # 日本はFar East
LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
JP_MARKETPLACE = "A1VC38T7YXB528"
AMAZON_JP_SELLER_ID = "AN1VRQENFRJN5"  # Amazon.co.jp 本体の出品者ID


# ---------------------------------------------------------------------
# 設定(.env)
# ---------------------------------------------------------------------

def load_env(path):
    """.env を読み込む。すでに設定済みの環境変数は上書きしない。"""
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env(name):
    v = os.environ.get(name, "").strip()
    return "" if (not v or v.startswith("ここに")) else v


SECRET_ENV = ("RAKUTEN_APPLICATION_ID", "RAKUTEN_ACCESS_KEY", "SPAPI_CLIENT_ID",
              "SPAPI_CLIENT_SECRET", "SPAPI_REFRESH_TOKEN")


def redact(text):
    for name in SECRET_ENV:
        v = env(name)
        if v:
            text = text.replace(v, "***")
    return text


# ---------------------------------------------------------------------
# 文字列ユーティリティ
# ---------------------------------------------------------------------

def norm(s):
    return unicodedata.normalize("NFKC", s or "").upper().replace(" ", "")


def contains_any(text, words):
    t = norm(text)
    for w in words:
        if w and norm(w) in t:
            return w
    return None


JAN_RE = re.compile(r"(?<!\d)(4[59]\d{11})(?!\d)")


def jan_ok(code):
    """JAN(13桁)のチェックデジットを確認する。"""
    if not (len(code) == 13 and code.isdigit()):
        return False
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(code[:12]))
    return (10 - s % 10) % 10 == int(code[12])


def find_jan(*texts):
    for t in texts:
        for m in JAN_RE.finditer(unicodedata.normalize("NFKC", t or "")):
            if jan_ok(m.group(1)):
                return m.group(1)
    return ""


# ---------------------------------------------------------------------
# データと計算
# ---------------------------------------------------------------------

@dataclass
class Item:
    name: str
    price: int
    url: str
    shop: str
    point_rate: int = 1       # 楽天の商品ページのポイント倍率(1 = 1倍 = 1%)
    shipping_included: bool = True
    jan: str = ""
    keyword: str = ""
    skip_reason: str = ""
    # Amazon側
    asin: str = ""
    amazon_title: str = ""
    sales_rank: int | None = None
    amazon_price: int | None = None
    offer_count: int | None = None
    amazon_sells: bool = False
    fees: int | None = None
    restricted: bool | None = None

    @property
    def points(self):
        """もらえる楽天ポイント(税抜価格に対してつく前提の概算)"""
        rate = self.point_rate + config.EXTRA_POINT_PERCENT
        return (self.price * 10 // 11) * rate // 100

    @property
    def cost(self):
        """実質仕入れ値 = 価格 + 送料 − ポイント"""
        ship = 0 if self.shipping_included else config.RAKUTEN_SHIPPING_ESTIMATE
        return self.price + ship - self.points

    @property
    def breakeven_price(self):
        """Amazonでこの価格以上で売れれば、MIN_PROFIT 以上の利益が出る(手動モード用の目安)"""
        need = self.cost + config.FBA_FEE_ESTIMATE + config.INBOUND_SHIPPING_PER_ITEM + config.MIN_PROFIT
        return math.ceil(need / (1 - config.REFERRAL_FEE_RATE) / 10) * 10

    @property
    def est_fees(self):
        if self.fees is not None:
            return self.fees
        if self.amazon_price is None:
            return None
        return int(self.amazon_price * config.REFERRAL_FEE_RATE + config.FBA_FEE_ESTIMATE)

    @property
    def profit(self):
        if self.amazon_price is None:
            return None
        return self.amazon_price - self.est_fees - config.INBOUND_SHIPPING_PER_ITEM - self.cost

    @property
    def roi(self):
        p = self.profit
        return None if p is None or self.cost <= 0 else round(p / self.cost, 2)

    @property
    def is_candidate(self):
        return (not self.skip_reason and self.profit is not None
                and self.profit >= config.MIN_PROFIT and (self.roi or 0) >= config.MIN_ROI)


def screen(it: Item) -> str:
    """調べる前の除外。理由を返す(空文字なら対象)。"""
    if w := contains_any(it.name, config.NG_WORDS):
        return f"NGワード({w})"
    if b := contains_any(it.name, config.EXCLUDE_BRANDS):
        return f"避けるブランド({b})"
    if not it.jan:
        return "JANなし"
    return ""


# ---------------------------------------------------------------------
# HTTP(共通)
# ---------------------------------------------------------------------

def http_json(url, method="GET", headers=None, body=None, retries=3):
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    last = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: " + redact(e.read().decode("utf-8", errors="replace")[:300])
            if e.code == 429 or e.code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(last) from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = redact(str(e))
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(last)


# ---------------------------------------------------------------------
# 楽天(公式 商品検索API)
# ---------------------------------------------------------------------

def parse_rakuten(data, keyword=""):
    out = []
    for entry in data.get("Items") or data.get("items") or []:
        e = entry.get("Item", entry) if isinstance(entry, dict) else {}
        name = str(e.get("itemName", ""))
        if not name:
            continue
        jan = str(e.get("janCode") or e.get("jan") or "")
        if not jan_ok(jan):
            jan = find_jan(name, str(e.get("itemCaption", "")))
        out.append(Item(
            name=name,
            price=int(float(e.get("itemPrice", 0) or 0)),
            url=str(e.get("itemUrl", "")),
            shop=str(e.get("shopName", "")),
            point_rate=int(float(e.get("pointRate", 1) or 1)),
            shipping_included=int(e.get("postageFlag", 0) or 0) == 0,
            jan=jan,
            keyword=keyword,
        ))
    return out


def load_jan_list(path):
    """jan_list.txt(1行に1つJAN)を読み込む。正しいJANだけ返す。"""
    path = Path(path)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        code = unicodedata.normalize("NFKC", line).strip().split("#")[0].strip()
        if jan_ok(code) and code not in out:
            out.append(code)
    return out


def build_queries():
    """(種類, 値) のリスト。種類は keyword / shop / jan。"""
    q = [("keyword", k) for k in config.KEYWORDS]
    q += [("shop", s) for s in getattr(config, "SHOP_CODES", [])]
    q += [("jan", j) for j in load_jan_list(HERE / "jan_list.txt")]
    return q


def fetch_rakuten():
    app_id, key = env("RAKUTEN_APPLICATION_ID"), env("RAKUTEN_ACCESS_KEY")
    if not app_id or not key:
        sys.exit("楽天のアプリケーションID・アクセスキーが env.txt に設定されていません。README の手順2を見てください。")
    endpoint = env("RAKUTEN_API_ENDPOINT") or RAKUTEN_ENDPOINT
    headers = {"Authorization": "Bearer " + key, "User-Agent": "sedori-rakuten-amazon/1.0"}
    if ref := env("RAKUTEN_REFERER"):
        headers.update({"Referer": ref, "Origin": ref.rstrip("/")})
    items, seen = [], set()
    for kind, value in build_queries():
        pages = 1 if kind == "jan" else config.PAGES_PER_KEYWORD
        for page in range(1, pages + 1):
            params = {"applicationId": app_id, "accessKey": key, "hits": 30, "page": page,
                      "sort": "+itemPrice" if kind == "jan" else config.RAKUTEN_SORT, "availability": 1,
                      "minPrice": config.MIN_RAKUTEN_PRICE, "maxPrice": config.MAX_RAKUTEN_PRICE,
                      "format": "json", "formatVersion": 2}
            params["shopCode" if kind == "shop" else "keyword"] = value
            if aff := env("RAKUTEN_AFFILIATE_ID"):
                params["affiliateId"] = aff
            label = {"keyword": "キーワード", "shop": "ショップ", "jan": "JAN"}[kind]
            print(f"[楽天] {label}「{value}」 {page}ページ目")
            try:
                data = http_json(endpoint + "?" + urllib.parse.urlencode(params), headers=headers)
            except RuntimeError as e:
                print(f"  ! 失敗: {e}")
                if "403" in str(e):
                    print("  → 楽天ウェブサービスの「許可されたIP」に、このMacの回線のIPを追加してください(README参照)")
                break
            got = 0
            for it in parse_rakuten(data, value):
                if kind == "jan" and not it.jan:
                    it.jan = value  # JANで検索して見つかった商品(セット品などの取り違えに注意)
                if it.url not in seen:
                    seen.add(it.url)
                    items.append(it)
                    got += 1
            print(f"  → {got}件")
            time.sleep(1.2)  # 楽天のアクセス制限(1秒1回)を守る
            if got == 0:
                break
    return items


# ---------------------------------------------------------------------
# Amazon(公式 SP-API)
# ---------------------------------------------------------------------

class SPAPI:
    def __init__(self):
        self.token, self.expire = "", 0.0
        self.seller_id = env("SPAPI_SELLER_ID")

    @staticmethod
    def available():
        return all(env(n) for n in ("SPAPI_CLIENT_ID", "SPAPI_CLIENT_SECRET", "SPAPI_REFRESH_TOKEN"))

    def _auth(self):
        if self.token and time.time() < self.expire - 60:
            return self.token
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token", "refresh_token": env("SPAPI_REFRESH_TOKEN"),
            "client_id": env("SPAPI_CLIENT_ID"), "client_secret": env("SPAPI_CLIENT_SECRET"),
        }).encode()
        r = http_json(LWA_TOKEN_URL, "POST",
                      {"Content-Type": "application/x-www-form-urlencoded"}, body)
        self.token, self.expire = r["access_token"], time.time() + int(r.get("expires_in", 3600))
        return self.token

    def call(self, path, params=None, method="GET", body=None, wait=0.0):
        url = SPAPI_ENDPOINT + path + ("?" + urllib.parse.urlencode(params) if params else "")
        headers = {"x-amz-access-token": self._auth(), "Content-Type": "application/json",
                   "User-Agent": "sedori-rakuten-amazon/1.0 (Language=Python)"}
        try:
            return http_json(url, method, headers, body)
        finally:
            time.sleep(wait)  # SP-API の回数制限を守る

    # --- JAN → ASIN・ランキング ---
    def catalog_by_jan(self, jans):
        result = {}
        for i in range(0, len(jans), 20):
            chunk = jans[i:i + 20]
            data = self.call("/catalog/2022-04-01/items", {
                "identifiers": ",".join(chunk), "identifiersType": "JAN",
                "marketplaceIds": JP_MARKETPLACE, "includedData": "identifiers,summaries,salesRanks",
                "pageSize": 20}, wait=0.6)
            result.update(parse_catalog(data, set(chunk)))
        return result

    # --- カート価格・出品者 ---
    def offers(self, asin):
        return self.call(f"/products/pricing/v0/items/{asin}/offers",
                         {"MarketplaceId": JP_MARKETPLACE, "ItemCondition": "New"}, wait=2.1)

    # --- 手数料(販売手数料+FBA手数料) ---
    def fees(self, asin, price):
        body = {"FeesEstimateRequest": {
            "MarketplaceId": JP_MARKETPLACE, "IsAmazonFulfilled": True, "Identifier": asin,
            "PriceToEstimateFees": {"ListingPrice": {"CurrencyCode": "JPY", "Amount": price}}}}
        data = self.call(f"/products/fees/v0/items/{asin}/feesEstimate", method="POST", body=body, wait=1.1)
        est = (data.get("payload") or {}).get("FeesEstimateResult", {}).get("FeesEstimate") or {}
        amt = (est.get("TotalFeesEstimate") or {}).get("Amount")
        return int(round(float(amt))) if amt is not None else None

    # --- 出品制限 ---
    def restricted(self, asin):
        if not self.seller_id:
            return None
        data = self.call("/listings/2021-08-01/restrictions", {
            "asin": asin, "sellerId": self.seller_id, "marketplaceIds": JP_MARKETPLACE,
            "conditionType": "new_new"}, wait=0.3)
        return bool(data.get("restrictions"))


def parse_catalog(data, wanted):
    """searchCatalogItems の返事から {JAN: (ASIN, 商品名, ランキング)} を作る。"""
    out = {}
    for it in data.get("items", []):
        codes = set()
        for grp in it.get("identifiers", []):
            for ident in grp.get("identifiers", []):
                v = str(ident.get("identifier", ""))
                codes.add(v[1:] if len(v) == 14 and v.startswith("0") else v)
        title = next((s.get("itemName", "") for s in it.get("summaries", [])), "")
        ranks = []
        for grp in it.get("salesRanks", []):
            ranks += [r.get("rank") for r in grp.get("displayGroupRanks", []) if r.get("rank")]
        rank = min(ranks) if ranks else None
        for code in codes & wanted:
            out.setdefault(code, (it.get("asin", ""), title, rank))
    return out


def parse_offers(data):
    """getItemOffers の返事から (カート価格, 出品者数, Amazon本体が出品しているか) を返す。"""
    p = data.get("payload") or {}
    s = p.get("Summary") or {}
    price = None
    for bb in s.get("BuyBoxPrices") or []:
        if str(bb.get("condition", "")).lower() == "new":
            price = (bb.get("LandedPrice") or bb.get("ListingPrice") or {}).get("Amount")
            break
    if price is None:
        lows = [(lp.get("LandedPrice") or {}).get("Amount") for lp in s.get("LowestPrices") or []
                if str(lp.get("condition", "")).lower() == "new"]
        lows = [x for x in lows if x is not None]
        price = min(lows) if lows else None
    offers = p.get("Offers") or []
    amazon = any(o.get("SellerId") == AMAZON_JP_SELLER_ID for o in offers)
    count = s.get("TotalOfferCount", len(offers))
    return (int(round(float(price))) if price is not None else None), count, amazon


def enrich_with_amazon(targets):
    api = SPAPI()
    print(f"\n[Amazon] {len(targets)}件のJANをカタログで照合します")
    catalog = api.catalog_by_jan(sorted({t.jan for t in targets}))
    for n, it in enumerate(targets, 1):
        hit = catalog.get(it.jan)
        if not hit:
            it.skip_reason = "Amazonに商品なし"
            continue
        it.asin, it.amazon_title, it.sales_rank = hit
        if it.sales_rank is None or it.sales_rank > config.MAX_SALES_RANK:
            it.skip_reason = f"ランキング圏外({it.sales_rank or '-'})"
            continue
        try:
            it.amazon_price, it.offer_count, it.amazon_sells = parse_offers(api.offers(it.asin))
        except RuntimeError as e:
            it.skip_reason = f"価格取得エラー({str(e)[:40]})"
            continue
        if it.amazon_price is None:
            it.skip_reason = "新品の出品なし"
            continue
        if config.SKIP_IF_AMAZON_SELLS and it.amazon_sells:
            it.skip_reason = "Amazon本体が出品"
            continue
        if (it.profit or 0) < config.MIN_PROFIT:  # 目安の時点で赤字なら、手数料APIは呼ばない
            continue
        try:
            it.fees = api.fees(it.asin, it.amazon_price)
            it.restricted = api.restricted(it.asin)
        except RuntimeError as e:
            print(f"  ! {it.asin}: {e}")
        if it.restricted:
            it.skip_reason = "出品制限あり"
        mark = "★候補" if it.is_candidate else ""
        print(f"[{n}/{len(targets)}] 楽天¥{it.cost:,} → Amazon¥{it.amazon_price:,} 利益{it.profit} {it.name[:28]} {mark}")


# ---------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------

def amazon_search_url(jan):
    return "https://www.amazon.co.jp/s?k=" + urllib.parse.quote(jan)


def write_outputs(items, outdir: Path, auto: bool):
    outdir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = outdir / f"rakuten_amazon_{stamp}.csv"

    def key(x):
        if auto:
            return (x.is_candidate, x.profit if x.profit is not None else -10**9)
        return (not x.skip_reason, -(x.breakeven_price - x.price))

    rows = sorted(items, key=key, reverse=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:  # Excelで文字化けしない
        w = csv.writer(f)
        w.writerow(["判定", "利益", "ROI", "楽天実質仕入れ値", "楽天価格", "ポイント", "損益分岐のAmazon価格",
                    "Amazonカート価格", "手数料", "ランキング", "出品者数", "JAN", "ASIN", "商品名",
                    "除外理由", "楽天URL", "Amazon URL"])
        for it in rows:
            amz = f"https://www.amazon.co.jp/dp/{it.asin}" if it.asin else (amazon_search_url(it.jan) if it.jan else "")
            w.writerow(["候補" if it.is_candidate else "", it.profit if it.profit is not None else "",
                        it.roi if it.roi is not None else "", it.cost, it.price, it.points, it.breakeven_price,
                        it.amazon_price or "", it.est_fees if it.est_fees is not None else "",
                        it.sales_rank or "", it.offer_count if it.offer_count is not None else "",
                        it.jan, it.asin, it.name, it.skip_reason, it.url, amz])

    if auto:
        picks = [i for i in rows if i.is_candidate]
        title = f"仕入れ候補(利益 ¥{config.MIN_PROFIT:,} 以上・ROI {int(config.MIN_ROI * 100)}% 以上)"
    else:
        picks = [i for i in rows if not i.skip_reason][:200]
        title = "Amazonで確認する商品リスト(手動モード)"
    cards = []
    for it in picks:
        if auto:
            nums = (f"楽天 実質<b>¥{it.cost:,}</b> → Amazon <b>¥{it.amazon_price:,}</b>"
                    f"<span class='profit'>利益 ¥{it.profit:,}(ROI {int((it.roi or 0) * 100)}%)</span>")
            meta = f"ランキング {it.sales_rank:,} ・ 出品者 {it.offer_count}人 ・ 手数料 ¥{it.est_fees:,}"
            amz = f"https://www.amazon.co.jp/dp/{it.asin}"
        else:
            nums = (f"楽天 実質<b>¥{it.cost:,}</b>(価格¥{it.price:,} − ポイント{it.points:,})"
                    f"<span class='profit'>Amazonで <b>¥{it.breakeven_price:,}</b> 以上なら利益</span>")
            meta = f"JAN {it.jan} ・ 検索語「{html.escape(it.keyword)}」"
            amz = amazon_search_url(it.jan)
        cards.append(f"""
<div class="card">
  <div class="name">{html.escape(it.name[:90])}</div>
  <div class="nums">{nums}</div>
  <div class="meta">{meta}</div>
  <div class="links"><a href="{html.escape(it.url)}" target="_blank">楽天の商品ページ</a>
  <a href="{html.escape(amz)}" target="_blank">Amazonで見る</a></div>
</div>""")
    note = ("購入前に、Amazonの商品ページで「同じ商品か(容量・色・セット数)」「出品制限がないか」を必ず確認してください。"
            if auto else
            "SP-API未接続のため、Amazonの価格は自動で取っていません。各商品のJANを「Amazon Seller」アプリで検索し、"
            "カート価格が「損益分岐の価格」より高ければ候補です(アプリで出品制限と手数料も確認できます)。")
    html_path = outdir / f"rakuten_amazon_{stamp}.html"
    html_path.write_text(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>楽天→Amazon {stamp}</title>
<style>
body{{font-family:-apple-system,"Hiragino Sans","Yu Gothic",sans-serif;background:#f5f5f2;margin:0;padding:16px;color:#222}}
h1{{font-size:18px}} .sum{{color:#555;font-size:13px;margin-bottom:12px;line-height:1.6}}
.card{{background:#fff;border-radius:10px;padding:12px;margin-bottom:10px;box-shadow:0 1px 3px #0001}}
.name{{font-weight:600;margin-bottom:6px}} .nums b{{font-size:15px}}
.profit{{margin-left:8px;color:#1e7e34;font-weight:600}} .meta{{font-size:12px;color:#888;margin:4px 0}}
.links a{{display:inline-block;margin:4px 10px 0 0;font-size:13px}}
</style></head><body>
<h1>{title}</h1>
<div class="sum">{stamp} 実行 ・ 表示 {len(picks)}件 / 調査 {len(items)}件<br>{note}</div>
{''.join(cards) or '<p>今回は条件を満たす商品はありませんでした。</p>'}
</body></html>""", encoding="utf-8")
    return csv_path, html_path, len(picks)


# ---------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------

def main():
    load_env(HERE / ".env")
    load_env(HERE / "env.txt")  # Macで隠しファイルを作りにくいので、見えるファイル名でもOK
    items = fetch_rakuten()
    print(f"\n楽天から {len(items)} 件取得")
    best = {}
    for it in items:
        it.skip_reason = screen(it)
        if not it.skip_reason and (it.jan not in best or it.cost < best[it.jan].cost):
            best[it.jan] = it
    for it in items:  # 同じJANは、いちばん安く買えるものだけを調べる
        if not it.skip_reason and best[it.jan] is not it:
            it.skip_reason = "同じJANでより安い楽天商品あり"
    targets = list(best.values())
    print(f"JANがあり、除外条件に当たらない商品: {len(targets)} 件")

    auto = SPAPI.available()
    if auto and targets:
        enrich_with_amazon(targets)
    elif not auto:
        print("\nSP-API が未設定のため「手動モード」で出力します(Amazonの価格は Amazon Seller アプリで確認)。")

    csv_path, html_path, n = write_outputs(items, HERE / "output", auto)
    print(f"\n完了:表示 {n} 件\n  全件一覧: {csv_path}\n  レポート: {html_path}")


if __name__ == "__main__":
    main()
