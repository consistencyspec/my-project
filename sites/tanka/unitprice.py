"""取得した商品を、カテゴリごとに「1枚・1Lあたりの値段(送料込み)」で並べる部品(APIには接続しません)。"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
from quantity import normalize, parse_quantity, to_display  # noqa: E402

FURUSATO_SHOP = re.compile(r"^f\d{6}")  # ふるさと納税の自治体ショップ(寄付なので比べない)


@dataclass
class Product:
    code: str
    name: str
    short_name: str
    shop: str
    price: int
    url: str
    image: str
    review_count: int
    review_average: float
    amount: float = 0          # 基準単位(g / ml / 枚 / ロール / 箱)の量
    amount_text: str = ""
    unit_price: float = 0      # 1単位(1L・1枚など)あたりの値段(円)
    note: str = ""


def short_name(name, limit=46):
    text = re.sub(r"【[^】]*】|［[^］]*］|\[[^\]]*\]|＜[^＞]*＞|<[^>]*>|《[^》]*》|＼[^／]*／|★[\d.]+|◎|♪|！|!", " ", name)
    text = re.sub(r"\s+", " ", text).strip(" 　|｜/")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def matches_category(raw, category):
    """カテゴリに合う商品か(送料込み・ふるさと納税以外・キーワード条件)。"""
    if raw.get("postageFlag") not in (0, "0"):
        return False  # 送料別の商品は、本当の単価が分からないので比べない
    if FURUSATO_SHOP.match(str(raw.get("shopCode", ""))):
        return False
    name = normalize(raw.get("itemName", ""))
    if not any(normalize(w) in name for w in category["must_include"]):
        return False
    if category.get("also_include") and not any(normalize(w) in name for w in category["also_include"]):
        return False
    if any(normalize(w) in name for w in category.get("exclude", [])):
        return False
    if category.get("require_regex") and not re.search(category["require_regex"], name):
        return False
    if category.get("exclude_regex") and re.search(category["exclude_regex"], name):
        return False
    return True


def to_product(raw):
    images = raw.get("mediumImageUrls") or []
    image = images[0] if images else ""
    if isinstance(image, dict):
        image = image.get("imageUrl", "")
    image = re.sub(r"_ex=\d+x\d+", "_ex=240x240", image)
    return Product(
        code=str(raw.get("itemCode", "")),
        name=str(raw.get("itemName", "")),
        short_name=short_name(str(raw.get("itemName", ""))),
        shop=str(raw.get("shopName", "")),
        price=int(float(raw.get("itemPrice", 0) or 0)),
        url=str(raw.get("affiliateUrl") or raw.get("itemUrl") or ""),
        image=image,
        review_count=int(float(raw.get("reviewCount", 0) or 0)),
        review_average=float(raw.get("reviewAverage", 0) or 0),
    )


def rank_category(raws, category, overrides=None, min_review_count=5, top=30):
    """カテゴリの商品を、単価が安い順に並べる。量が読み取れない・価格が選択肢で変わる商品は外す。"""
    overrides = overrides or {}
    family = category["family"]
    div = category["per"]["div"]
    lo, hi = category["unit_price_range"]
    min_review_count = category.get("min_review_count", min_review_count)
    seen, ranked = set(), []
    for raw in raws:
        code = str(raw.get("itemCode", ""))
        if code in seen or not matches_category(raw, category):
            continue
        seen.add(code)
        ov = overrides.get(code, {})
        if ov.get("exclude"):
            continue
        p = to_product(raw)
        pmin = int(float(raw.get("itemPriceMin3") or p.price))
        pmax = int(float(raw.get("itemPriceMax3") or p.price))
        if p.review_count < min_review_count or p.price <= 0 or pmin != pmax:
            continue  # 種類や数を選ぶ商品は、表示価格がどの量の値段か分からないので外す
        amount = ov.get("amount") or parse_quantity(p.name, family)
        if not amount:
            continue
        unit_price = p.price / (amount / div)
        if not lo <= unit_price <= hi:
            continue  # 極端な値は読み取りの誤りの可能性が高い
        p.amount, p.amount_text, p.unit_price = amount, to_display(amount, family), unit_price
        p.note = ov.get("note", "")
        ranked.append(p)
    ranked.sort(key=lambda x: (x.unit_price, -x.review_count))
    return ranked[:top]


def yen_unit(value):
    """単価の表示(10円以上は小数1桁、10円未満は小数2桁)。"""
    if value >= 100:
        return f"{value:,.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"
