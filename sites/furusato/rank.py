"""取得した返礼品を、カテゴリごとに「1万円あたりの量」で並べる部品(APIには接続しません)。"""
import re
from dataclasses import dataclass, field

from quantity import normalize, parse_quantity, to_display

FURUSATO_SHOP = re.compile(r"^f\d{6}")  # 楽天ふるさと納税の自治体ショップは「f+自治体コード」で始まる


@dataclass
class Gift:
    code: str
    name: str
    short_name: str
    shop: str
    price_min: int
    price_max: int
    url: str
    image: str
    review_count: int
    review_average: float
    amount: float = None          # 基準単位(g / ml / ロール / 箱)の量。読めなければ None
    amount_text: str = ""
    per10k: float = None          # 寄付額1万円あたりの量(表示単位: kg / L / ロール / 箱)
    note: str = ""
    flags: list = field(default_factory=list)


def short_name(name, limit=48):
    """商品名から【ふるさと納税】や記号の飾りを取り、読みやすい長さにする。"""
    text = re.sub(r"【[^】]*】|［[^］]*］|\[[^\]]*\]|＜[^＞]*＞|<[^>]*>|《[^》]*》|＼|／|★[\d.]+|◎|♪", " ", name)
    text = re.sub(r"\s+", " ", text).strip(" 　|｜/")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def to_gift(raw):
    images = raw.get("mediumImageUrls") or []
    image = images[0] if images else ""
    if isinstance(image, dict):
        image = image.get("imageUrl", "")
    image = re.sub(r"_ex=\d+x\d+", "_ex=240x240", image)
    price = int(float(raw.get("itemPrice", 0) or 0))
    return Gift(
        code=str(raw.get("itemCode", "")),
        name=str(raw.get("itemName", "")),
        short_name=short_name(str(raw.get("itemName", ""))),
        shop=str(raw.get("shopName", "")),
        price_min=int(float(raw.get("itemPriceMin3") or raw.get("itemPriceMin1") or price)),
        price_max=int(float(raw.get("itemPriceMax3") or raw.get("itemPriceMax1") or price)),
        url=str(raw.get("affiliateUrl") or raw.get("itemUrl") or ""),
        image=image,
        review_count=int(float(raw.get("reviewCount", 0) or 0)),
        review_average=float(raw.get("reviewAverage", 0) or 0),
    )


def matches_category(raw, category):
    if not FURUSATO_SHOP.match(str(raw.get("shopCode", ""))):
        return False
    name = normalize(raw.get("itemName", ""))
    if not any(normalize(w) in name for w in category["must_include"]):
        return False
    return not any(normalize(w) in name for w in category.get("exclude", []))


def rank_category(raws, category, overrides=None, min_review_count=10, top=20, popular=10):
    """カテゴリの返礼品を「比較できるもの(ranked)」と「容量を選べる人気品(popular)」に分ける。"""
    overrides = overrides or {}
    family = category["family"]
    lo, hi = category["per10k_range"]
    seen, ranked, others = set(), [], []
    for raw in raws:
        code = str(raw.get("itemCode", ""))
        if code in seen or not matches_category(raw, category):
            continue
        seen.add(code)
        ov = overrides.get(code, {})
        if ov.get("exclude"):
            continue
        g = to_gift(raw)
        if g.review_count < min_review_count or g.price_min <= 0:
            continue
        amount = ov.get("amount") or (parse_quantity(g.name, family) if g.price_min == g.price_max else None)
        if amount:
            unit_div = {"weight": 1000, "volume": 1000}.get(family, 1)
            per10k = amount / unit_div / g.price_min * 10000
            if lo <= per10k <= hi:
                g.amount, g.amount_text, g.per10k = amount, to_display(amount, family), per10k
                g.note = ov.get("note", "")
                if ov.get("amount"):
                    g.flags.append("checked")  # 人が商品ページで確認した量
                ranked.append(g)
                continue
            # 範囲外は読み取りミスの可能性が高いので比較に使わない
        others.append(g)
    ranked.sort(key=lambda g: (-g.per10k, -g.review_count))
    others.sort(key=lambda g: -g.review_count)
    return ranked[:top], others[:popular]


def per10k_text(g, family):
    unit = {"weight": "kg", "volume": "L", "roll": "ロール", "box": "箱"}[family]
    v = g.per10k
    if family in ("roll", "box"):
        return f"{v:,.0f}" + unit
    return (f"{v:.1f}" if v < 100 else f"{v:,.0f}") + unit
