"""返礼品の商品名から「量」を読み取る部品。

方針: 読み取りが確実なものだけを比較に使う(あやしいものは None を返して比較から外す)。
・容量や回数を選べる返礼品(「300g〜30kg」「5kg 10kg 20kg」など)は、寄付額と量の対応が分からないので外す
・「900g×5本」「12ロール×8パック」のような掛け算は合計にする
・「合計3.7kg」と書いてあれば、それを優先する
・定期便(「6回」「12ヶ月」など)は、1回分か全回分かが分からないので外す
"""
import re
import unicodedata

# 単位の種類ごとに、基準単位への換算倍率
UNIT_FAMILIES = {
    "weight": {"kg": 1000, "キロ": 1000, "g": 1, "グラム": 1},
    "volume": {"l": 1000, "ℓ": 1000, "リットル": 1000, "ml": 1},
    "roll": {"ロール": 1},
    "box": {"箱": 1},
}
# 表示用(基準単位の量 → 表示の単位)
DISPLAY = {
    "weight": ("kg", 1000),
    "volume": ("L", 1000),
    "roll": ("ロール", 1),
    "box": ("箱", 1),
}

_NUM = r"(\d+(?:\.\d+)?)"
_COUNTER = r"(?:袋|パック|本|個|箱|セット|缶|ケース|p|枚|入|玉|尾|パック入)?"
_MULT = r"(?:\s*[×x*]\s*(\d+)\s*" + _COUNTER + r")"
_SUBSCRIPTION = re.compile(r"定期便|頒布会")
_SUBSCRIPTION_COUNT = re.compile(r"\d+\s*(?:回|ヶ月|か月|カ月|ケ月)")
_CHOICE = re.compile(r"(?:容量|内容量|量|サイズ|重量|本数|個数)(?:が|を)?選べる|選べる(?:容量|内容量|量|サイズ|重量|本数|個数)")
_ROLL_FACTOR = re.compile(r"(\d+(?:\.\d+)?)\s*倍(?:巻|長)")


def normalize(text):
    """全角→半角などをそろえ、小文字にする(「ｋｇ」→「kg」、「Ｌ」→「l」)。"""
    return unicodedata.normalize("NFKC", text or "").lower()


def _pattern(family):
    units = sorted(UNIT_FAMILIES[family], key=len, reverse=True)
    unit_re = "|".join(re.escape(u) for u in units)
    # 単位の後ろが英字なら別の単位(例: "kgs" は可、"lb" の l は除外)
    tail = r"(?![a-z])" if family in ("weight", "volume") else ""
    return re.compile(r"(合計|計|総量|総重量)?\s*" + _NUM + r"\s*(" + unit_re + r")" + tail + r"((?:" + _MULT + r")*)")


_PATTERNS = {f: _pattern(f) for f in UNIT_FAMILIES}
_MULT_RE = re.compile(_MULT)


def parse_quantity(name, family):
    """商品名から量(基準単位: g / ml / ロール / 箱)を読み取る。確実でなければ None。"""
    text = normalize(name)
    if _SUBSCRIPTION.search(text) and _SUBSCRIPTION_COUNT.search(text):
        return None
    if _CHOICE.search(text):
        return None
    # 「300g〜30kg」のような範囲の表記は、容量を選べる返礼品
    if re.search(_NUM + r"\s*(?:kg|g|l|ml|ロール|箱)?\s*[〜~～]\s*\d", text):
        return None

    if family == "roll":
        equivalents = {float(x) for x in re.findall(_NUM + r"\s*ロール相当", text)}
        if equivalents:  # 「144ロール相当」と換算済みの数が書いてあれば、それを使う
            return equivalents.pop() if len(equivalents) == 1 else None

    matches = []
    for m in _PATTERNS[family].finditer(text):
        total_mark, num, unit, mults = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        base = num * UNIT_FAMILIES[family][unit]
        factor = 1
        for mm in _MULT_RE.finditer(mults or ""):
            factor *= int(mm.group(1))
        if base <= 0:
            continue
        matches.append({"total_mark": bool(total_mark), "base": base, "factor": factor})
    if not matches:
        return None

    marked = [m for m in matches if m["total_mark"]]
    if marked:
        totals = {m["base"] * m["factor"] for m in marked}
        return totals.pop() if len(totals) == 1 else None

    bases = {m["base"] for m in matches}
    if len(bases) != 1:
        return None  # 「5kg 10kg 20kg」のように量が複数 → 選べる返礼品
    factors = {m["factor"] for m in matches if m["factor"] != 1}
    if len(factors) > 1:
        return None  # 「2L×6本」「2L×12本」が両方ある → 選べる返礼品
    total = bases.pop() * (factors.pop() if factors else 1)

    if family == "roll":
        roll_factors = {float(x) for x in _ROLL_FACTOR.findall(text)}
        if len(roll_factors) > 1:
            return None
        if roll_factors:
            total *= roll_factors.pop()  # 2倍巻きなら、標準ロール2個分として数える
    return total


def to_display(amount, family):
    """基準単位の量を「12.5kg」「96ロール」のような表示にする。"""
    unit, div = DISPLAY[family]
    value = amount / div
    if value >= 100 or float(value).is_integer():
        text = f"{value:,.0f}"
    elif value >= 10:
        text = f"{value:.1f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text + unit
