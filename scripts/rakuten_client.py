"""楽天市場 商品検索API を呼び出す部品。

・アプリケーションID / アクセスキー / アフィリエイトID は環境変数(または .env)から読みます。
・コードの中にIDやキーは書きません。エラーメッセージにも表示しません。
・標準ライブラリだけで動きます(追加インストール不要)。
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# 2026年2月以降の新API。仕様が変わったら .env の RAKUTEN_API_ENDPOINT で上書きできます。
DEFAULT_ENDPOINT = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
REQUEST_INTERVAL_SEC = 1.1  # 楽天のアクセス制限(1秒1回程度)を守るための待ち時間
_last_request_at = 0.0


class RakutenError(Exception):
    """API呼び出しに失敗したときのエラー(メッセージにキーは含めません)。"""


@dataclass
class Item:
    item_code: str
    name: str
    price: int
    url: str
    affiliate_url: str
    shop: str
    review_average: float
    review_count: int


def load_env(path):
    """.env ファイルを読み込む。すでに設定済みの環境変数は上書きしない。"""
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def get_settings():
    """環境変数から設定を集める。足りないものは missing に入れて返す。"""
    s = {
        "application_id": os.environ.get("RAKUTEN_APPLICATION_ID", "").strip(),
        "access_key": os.environ.get("RAKUTEN_ACCESS_KEY", "").strip(),
        "affiliate_id": os.environ.get("RAKUTEN_AFFILIATE_ID", "").strip(),
        "endpoint": os.environ.get("RAKUTEN_API_ENDPOINT", "").strip() or DEFAULT_ENDPOINT,
        "referer": os.environ.get("RAKUTEN_REFERER", "").strip(),
    }
    placeholders = ("ここに", "xxxx", "your_")
    s["missing"] = [
        env for env, key in (
            ("RAKUTEN_APPLICATION_ID", "application_id"),
            ("RAKUTEN_ACCESS_KEY", "access_key"),
            ("RAKUTEN_AFFILIATE_ID", "affiliate_id"),
        ) if not s[key] or any(p in s[key].lower() for p in placeholders)
    ]
    return s


def _redact(text, settings):
    for key in ("application_id", "access_key", "affiliate_id"):
        if settings.get(key):
            text = text.replace(settings[key], "***")
    return text


def parse_items(data):
    """APIの返事(JSON)から Item のリストを作る。新旧どちらの形式でも読めるようにしてある。"""
    items = []
    for entry in data.get("Items") or data.get("items") or []:
        e = entry.get("Item", entry) if isinstance(entry, dict) else {}
        if not e.get("itemName"):
            continue
        items.append(Item(
            item_code=str(e.get("itemCode", "")),
            name=str(e.get("itemName", "")),
            price=int(float(e.get("itemPrice", 0) or 0)),
            url=str(e.get("itemUrl", "")),
            affiliate_url=str(e.get("affiliateUrl", "")),
            shop=str(e.get("shopName", "")),
            review_average=float(e.get("reviewAverage", 0) or 0),
            review_count=int(float(e.get("reviewCount", 0) or 0)),
        ))
    return items


def search_items(settings, keyword, min_price=None, max_price=None, hits=30, sort="standard"):
    """キーワードで商品を検索して Item のリストを返す。"""
    global _last_request_at
    if settings["missing"]:
        raise RakutenError("環境変数が未設定です: " + ", ".join(settings["missing"]))
    params = {
        "applicationId": settings["application_id"],
        "accessKey": settings["access_key"],
        "affiliateId": settings["affiliate_id"],
        "keyword": keyword,
        "hits": hits,
        "sort": sort,
        "availability": 1,
        "format": "json",
        "formatVersion": 2,
    }
    if min_price:
        params["minPrice"] = int(min_price)
    if max_price:
        params["maxPrice"] = int(max_price)
    url = settings["endpoint"] + "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": "Bearer " + settings["access_key"], "User-Agent": "threads-affiliate-drafts/1.0"}
    if settings["referer"]:
        headers["Referer"] = settings["referer"]
        headers["Origin"] = settings["referer"].rstrip("/")

    wait = REQUEST_INTERVAL_SEC - (time.time() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    last_error = ""
    for attempt in range(3):
        _last_request_at = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as res:
                return parse_items(json.loads(res.read().decode("utf-8")))
        except urllib.error.HTTPError as e:
            body = _redact(e.read().decode("utf-8", errors="replace")[:300], settings)
            last_error = f"HTTP {e.code}: {body}"
            if e.code == 429 or e.code >= 500:  # 混雑・一時的な不具合は少し待って再試行
                time.sleep(2 * (attempt + 1))
                continue
            if e.code in (401, 403):
                last_error += "(ID・アクセスキー・許可Webサイト(RAKUTEN_REFERER)の設定を確認してください)"
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_error = _redact(str(e), settings)
            time.sleep(2 * (attempt + 1))
    raise RakutenError(f"楽天APIの呼び出しに失敗しました: {last_error}")


def select_items(items, count, min_review_count=5, min_review_average=4.0,
                 ng_words=("中古", "訳あり", "福袋", "ジャンク", "レンタル", "アウトレット"),
                 exclude_codes=()):
    """条件に合う商品を count 件選ぶ(レビューが少ない・NGワード入り・使用済みの商品は除外)。"""
    chosen = []
    for it in items:
        if it.item_code in exclude_codes or any(w in it.name for w in ng_words):
            continue
        if it.review_count < min_review_count or it.review_average < min_review_average:
            continue
        chosen.append(it)
        if len(chosen) >= count:
            break
    return chosen
