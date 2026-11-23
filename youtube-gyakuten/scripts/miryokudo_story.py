"""都道府県魅力度ランキング 4位〜10位の18年(新常識クロニクル)。

  .venv/bin/python scripts/miryokudo_story.py           -> output/miryokudo_story/miryokudo_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/miryokudo_story.py --script  -> content/miryokudo_story.md(台本)だけ作り直す
  .venv/bin/python scripts/miryokudo_story.py --voice   -> 声と台本だけ(映像は作らない)
  .venv/bin/python scripts/miryokudo_story.py --stills  -> 各場面の最後の絵を output/miryokudo_story/stills/ に書き出す(確認用)

この回は議席を使わない。1〜3位はほぼ動かないので最初に除外し、4位〜10位の7つの席を「番付ボード」で見せる。
右の円グラフは、7つの席を どの地方の県が取ったか の比率(年ごと)。
順位が入れ替わった県・新しく入った県は「その年、何があった？」の場面で、イラストつきで紹介する。
データ：ブランド総合研究所「地域ブランド調査」(research/todofuken-miryokudo-top10-2009-2026.md)
"""
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import INK, PANEL, SUB, TRIM, W, H, WHITE, font, panel, stage, text  # noqa: E402
from motion import blank, out_back, out_cubic, seg, with_alpha  # noqa: E402
import coffee_war as cw  # noqa: E402
import coffee_story as cs  # noqa: E402
from coffee_story import WithAudio, chip, element_layers, pop_in, telop, words  # noqa: E402
import miryokudo_art as art  # noqa: E402
from thumbnail import EPISODES, series_card  # noqa: E402
import narrate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "miryokudo_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "miryokudo_story.md")
EPISODE = "miryokudo"
EPISODES.setdefault(EPISODE, ("魅力度ランキング18年", "4位〜10位、その年 何があった？", "上がった県", "落ちた県"))

narrate.MM_DICT += ["魅力度/みりょくど", "圏外/けんがい", "初登場/はつとうじょう", "殿堂入り/でんどういり",
                    "軍艦島/ぐんかんじま", "兼六園/けんろくえん", "首里城/しゅりじょう", "夢洲/ゆめしま",
                    "平城遷都/へいじょうせんと", "潜伏キリシタン/せんぷくキリシタン", "天草/あまくさ",
                    "徳川家康/とくがわいえやす", "家康/いえやす", "龍馬伝/りょうまでん", "龍馬/りょうま",
                    "平清盛/たいらのきよもり", "大河ドラマ/たいがドラマ", "神戸/こうべ", "博多/はかた",
                    "G20/ジートゥエンティ", "18年間/じゅうはちねんかん", "1300年祭/せんさんびゃくねんさい",
                    "2時間半/にじかんはん", "全盛期/ぜんせいき", "地方/ちほう", "7つ/ななつ",
                    "北陸/ほくりく", "金沢/かなざわ", "晩年/ばんねん", "4位/よんい"]

# 文字を直接読み方に置きかえる語(数字がかなに直される前に使う)
narrate.TEXT_READ += [("G20", "ジートゥエンティ"), ("18年間", "十八年間"), ("18年分", "十八年分"), ("2時間半", "にじかんはん"),
                      ("1300年祭", "せんさんびゃくねんさい"), ("約3万人", "やくさんまんにん"), ("平清盛", "たいらのきよもり"),
                      ("トップ10", "トップテン"), ("トップ3", "トップスリー"), ("2県", "にけん"), ("2つ", "ふたつ"), ("1つ", "ひとつ"),
                      ("天草地方", "あまくさちほう")]
# 「〇位」はすべて かな+い で読ませる(漢字の「位」は「くらい」などと読まれる)。長い数字から先に置きかえる
narrate.TEXT_READ += [("139点", "ひゃくさんじゅうきゅうてん"), ("130点", "ひゃくさんじゅってん"), ("100点", "ひゃくてん"),
                      ("75点", "ななじゅうごてん"), ("71点", "ななじゅういってん"), ("8点", "はってん"), ("7点", "ななてん"),
                      ("3点", "さんてん"), ("1点", "いってん"), ("何位", "なんい")]
narrate.TEXT_READ += [(f"{n}位", narrate.kana(n) + "い") for n in range(13, 0, -1)]

# ---------- データ ----------
REGIONS = [("関東", (62, 120, 220)), ("関西", (240, 128, 40)), ("九州・沖縄", (60, 165, 105)), ("中部・北陸", (150, 95, 200))]
REGION_OF = {"東京": "関東", "神奈川": "関東", "大阪": "関西", "奈良": "関西", "兵庫": "関西",
             "福岡": "九州・沖縄", "長崎": "九州・沖縄", "沖縄": "九州・沖縄", "長野": "中部・北陸", "石川": "中部・北陸",
             "静岡": "中部・北陸"}
COLOR = dict(REGIONS)


def rc(pref):
    return COLOR[REGION_OF[pref]]


# 4位〜10位(2021年は10位が同点で8県)。bg-ranking.xyz の表から。公式発表で要確認
BOARD = {
    2009: "東京 奈良 神奈川 大阪 兵庫 福岡 長崎",
    2010: "東京 奈良 神奈川 大阪 兵庫 長崎 長野",
    2011: "東京 奈良 神奈川 大阪 長野 兵庫 福岡",
    2012: "東京 奈良 神奈川 長野 大阪 長崎 福岡",
    2013: "東京 神奈川 奈良 福岡 大阪 長野 兵庫",
    2014: "東京 神奈川 奈良 福岡 大阪 長野 長崎",
    2015: "沖縄 長崎 神奈川 奈良 福岡 大阪 長野",
    2016: "沖縄 神奈川 奈良 大阪 長野 石川 福岡",
    2017: "沖縄 神奈川 奈良 大阪 福岡 長野 石川",
    2018: "沖縄 神奈川 奈良 大阪 福岡 長野 長崎",
    2019: "沖縄 神奈川 大阪 奈良 福岡 石川 長野",
    2020: "東京 神奈川 大阪 奈良 長野 福岡 石川",
    2021: "東京 大阪 神奈川 福岡 長崎 奈良 石川 長野",
    2022: "東京 大阪 神奈川 福岡 奈良 長崎 石川",
    2023: "東京 大阪 福岡 神奈川 奈良 石川 長崎",
    2024: "東京 神奈川 福岡 大阪 長野 静岡 石川",
    2025: "神奈川 東京 福岡 長野 大阪 奈良 兵庫",
    2026: "東京 神奈川 大阪 福岡 長崎 長野 静岡",
}
BOARD = {y: s.split() for y, s in BOARD.items()}
YEARS = sorted(BOARD)
TOP3 = {y: ("北海道", "京都", "東京" if 2015 <= y <= 2019 else "沖縄") for y in YEARS}


def ranks(year):
    """{県: 順位}。2021年の10位同点に対応。"""
    out = {}
    for i, p in enumerate(BOARD[year]):
        out[p] = min(4 + i, 10)
    return out


def badge(year, pref):
    """その年の県の印：('初登場'|'復帰'|'↑2'|'↓1'|'', 色)。"""
    if year == YEARS[0]:
        return "", INK
    prev = ranks(year - 1)
    if pref in prev:
        d = prev[pref] - ranks(year)[pref]
        if d > 0:
            return f"↑{d}", (60, 165, 105)
        if d < 0:
            return f"↓{-d}", (62, 120, 220)
        return "", INK
    if pref == "沖縄" and year == 2015:
        return "3位から", SUB
    if pref == "東京" and year == 2020:
        return "3位から", SUB
    seen = any(pref in BOARD[y] for y in YEARS if y < year)
    return ("復帰", TRIM) if seen else ("初登場", (220, 50, 50))


def dropped(year):
    if year == YEARS[0]:
        return []
    now = set(BOARD[year])
    out = []
    for p in BOARD[year - 1]:
        if p not in now:
            if p == "東京" and year == 2015:
                continue      # 3位へ上がった
            if p == "沖縄" and year == 2020:
                continue      # 3位へ戻った
            out.append(p)
    return out


def shares(year):
    n = len(BOARD[year])
    return [sum(1 for p in BOARD[year] if REGION_OF[p] == r) / n for r, _ in REGIONS]


def counts(year):
    return [sum(1 for p in BOARD[year] if REGION_OF[p] == r) for r, _ in REGIONS]


# ---------- 番付ボード+円グラフ ----------
PX0, PY0, PX1, PY1 = 80, 120, 1000, 1010
PIE_C, PIE_R = (1450, 500), 250


def row_y(i, n):
    h = 96 if n <= 7 else 86
    return 262 + i * h + h / 2, h


def draw_row(d, cx_shift, y, h, rank, pref, bdg, alpha=1.0, scale=1.0):
    c = rc(pref)
    tint = tuple(int(255 - (255 - v) * 0.16) for v in c)
    x0, x1 = PX0 + 40, PX1 - 40
    hh = (h - 14) / 2 * scale
    d.rounded_rectangle([x0 + cx_shift, y - hh, x1 + cx_shift, y + hh], radius=hh, fill=tint)
    d.rounded_rectangle([x0 + cx_shift, y - hh, x0 + 22 + cx_shift, y + hh], radius=8, fill=c)
    r = 32 * scale
    rx = x0 + 80 + cx_shift
    d.ellipse([rx - r, y - r, rx + r, y + r], fill=INK)
    text(d, (rx, y), str(rank), int(34 * scale), WHITE, anchor="mm")
    text(d, (rx + 60, y), pref, int(56 * scale), INK, anchor="lm")
    text(d, (rx + 60 + d.textlength(pref, font=font(int(56 * scale))) + 22, y + 6), REGION_OF[pref], int(28 * scale), SUB,
         heavy=False, anchor="lm")
    if bdg[0]:
        s, col = bdg
        bx = x1 - 30 + cx_shift
        if s in ("初登場", "復帰", "3位から"):
            tw = d.textlength(s, font=font(34)) + 40
            d.rounded_rectangle([bx - tw, y - 28, bx, y + 28], radius=28, fill=col)
            text(d, (bx - tw / 2, y), s, 34, WHITE, anchor="mm")
        else:
            text(d, (bx, y), s, 48, col, anchor="rm")


def draw_pie(d, fr, cnt=None):
    cx, cy = PIE_C
    r = PIE_R
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=(14, 19, 32))
    a = -90.0
    for (name, col), f in zip(REGIONS, fr):
        if f <= 0.001:
            continue
        b = a + f * 360
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a, b, fill=col, outline=PANEL, width=6)
        if cnt is not None and f > 0.06:
            m = math.radians((a + b) / 2)
            text(d, (cx + math.cos(m) * r * 0.62, cy + math.sin(m) * r * 0.62), f"{round(f * 100)}%", 40, WHITE,
                 anchor="mm")
        a = b
    d.ellipse([cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3], fill=(27, 36, 58))
    text(d, (cx, cy), "地方", 34, WHITE, anchor="mm")


def legend(d, cnt, hi=None):
    for i, ((name, col), n) in enumerate(zip(REGIONS, cnt)):
        x = 1250 + (i % 2) * 400
        y = 820 + (i // 2) * 76
        sc = 1.12 if hi == name else 1.0
        d.rounded_rectangle([x - 175 * sc, y - 30 * sc, x + 175 * sc, y + 30 * sc], radius=30 * sc, fill=col)
        text(d, (x - 150 * sc, y), name, int(36 * sc), WHITE, anchor="lm")
        if n is not None:
            text(d, (x + 150 * sc, y), f"{n}県", int(40 * sc), WHITE, anchor="rm")


def board_static(year):
    im, d = stage()
    panel(d, (PX0, PY0, PX1, PY1))
    chip(d, PX0 + 150, 192, f"{year}年", INK, 52)
    text(d, (PX0 + 290, 192), "4位〜10位", 46, SUB, anchor="lm")
    t3 = TOP3[year]
    text(d, (1450, 150), f"1〜3位(除外)：{t3[0]}・{t3[1]}・{t3[2]}", 34, TRIM, anchor="mm")
    return im


def year_maker(year):
    """前の年の並びから、その年の並びへ動く。"""
    base = board_static(year)
    prev = BOARD.get(year - 1)
    cur = BOARD[year]
    n = len(cur)
    drops = dropped(year)

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im)
        k = out_cubic(seg(t, 0.3, 1.3))
        # 圏外に落ちる県
        if prev:
            for i, p in enumerate(prev):
                if p in cur:
                    continue
                a = 1 - seg(t, 0.2, 0.9)
                if a <= 0:
                    continue
                y0, h = row_y(i, len(prev))
                draw_row(d, 0, y0 + seg(t, 0.2, 0.9) * 120, h, min(4 + i, 10), p, ("", INK), scale=max(0.5, a))
        for i, p in enumerate(cur):
            y1, h = row_y(i, n)
            rank = min(4 + i, 10)
            if prev and p in prev:
                y0, _ = row_y(prev.index(p), len(prev))
                y = y0 + (y1 - y0) * k
                draw_row(d, 0, y, h, rank, p, badge(year, p) if t > 1.3 else ("", INK))
            else:
                kk = seg(t, 0.6 + 0.1 * i, 1.1 + 0.1 * i) if prev else seg(t, 0.2 + 0.18 * i, 0.6 + 0.18 * i)
                if kk <= 0:
                    continue
                sc = 0.6 + 0.4 * out_back(kk)
                draw_row(d, 0, y1, h, rank, p, badge(year, p) if t > 1.3 else ("", INK), scale=sc)
        # 円グラフ
        f0 = shares(year - 1) if prev else [0.25] * 4
        f1 = shares(year)
        q = out_cubic(seg(t, 0.3, 1.3)) if prev else out_cubic(seg(t, 0.2, 1.4))
        fr = [a + (b - a) * q for a, b in zip(f0, f1)]
        draw_pie(d, fr, cnt=counts(year) if q >= 1 else None)
        legend(d, counts(year) if q >= 1 else [None] * 4)
        if drops and t > 1.3:
            a = seg(t, 1.3, 1.7)
            text(d, (1450, 985), "圏外へ ↓ " + "・".join(drops), 40, tuple(int(200 * a + 27 * (1 - a)) for _ in range(3)),
                 anchor="mm")
        return im.convert("RGB")
    return frame, 2.2


# ---------- 「その年、何があった？」 ----------
def spot_frames(year, pref, heading, tl, elements):
    base = stage()[0].convert("RGBA")
    lay = blank()
    d = ImageDraw.Draw(lay)
    panel(d, (90, 130, 1830, 1000))
    chip(d, 240, 205, f"{year}年", INK, 42)
    c = rc(pref) if pref in REGION_OF else (220, 50, 50)
    tw = d.textlength(pref, font=font(42)) + 50
    d.rounded_rectangle([360, 205 - 36, 360 + tw, 205 + 36], radius=36, fill=c)
    text(d, (360 + tw / 2, 205), pref, 42, WHITE, anchor="mm")
    text(d, (420 + tw, 205), heading, 46, INK, anchor="lm")
    text(d, (1780, 205), "その年、何があった？", 34, SUB, heavy=False, anchor="rm")
    layers = element_layers(elements)
    tlay = blank()
    telop(ImageDraw.Draw(tlay), tl)

    def frame(t):
        im = base.copy()
        k = out_cubic(seg(t, 0.0, 0.4))
        im.alpha_composite(lay, (0, int((1 - k) * 60)))
        if k >= 1:
            pop_in(im, layers, t, start=0.3, step=0.35)
            a = seg(t, 0.4, 0.8)
            if a > 0:
                im.alpha_composite(with_alpha(tlay, a), (0, int((1 - a) * 20)))
        return im.convert("RGB")
    return frame, 0.3 + len(layers) * 0.35 + 0.6


def A(f, *args, **kw):
    """イラストを要素にする。"""
    return lambda d: f(d, *args, **kw)


def W_(cx, cy, s, size=56, color=INK):
    return lambda d: words(d, cx, cy, s, size, color)


RED = (220, 50, 50)
UP = (60, 165, 105)

# ---------- 場面 ----------
# ("year", 年, ナレーション) / ("spot", 年, 県, 見出し, テロップ, [要素], ナレーション)
SCENES = [
    ("hook", "都道府県の魅力度ランキング。1位は北海道、2位は京都。実はこの2つ、18年間、一度も入れ替わっていないんです。でも、その下の4位から10位は、毎年のように入れ替わってきました。"),
    ("title", "ランキングの順位が動いた年、その県では何が起きていたのか。新常識クロニクル、今日のテーマは「魅力度ランキング、4位から10位の18年」です。"),
    ("top3", "使うのは、ブランド総合研究所の「地域ブランド調査」。毎年、全国の約3万人に、それぞれの県がどれくらい魅力的かを聞いています。都道府県のランキングは、2009年から始まりました。ただ、1位の北海道、2位の京都は、ずっと同じ。3位も、ほとんどの年が沖縄です。そこで今回は、1位から3位を除外して、4位から10位の、7つの席に注目します。"),
    ("legend", "見方はかんたん。左が4位から10位の番付。右の円グラフは、その7つの席を、どの地方の県が取ったかの比率です。関東は青、関西はオレンジ、九州・沖縄は緑、中部・北陸は紫です。"),
    ("year", 2009, "それでは、行ってみましょう！ 2009年、最初の顔ぶれです。4位東京、5位奈良、6位神奈川、7位大阪。そして兵庫、福岡、長崎。7つの席のうち3つが関西。西日本が強いスタートです。"),

    ("year", 2010, "2010年。長崎が一つ上がって9位。そして10位に、長野が初登場。代わりに福岡が、圏外に落ちます。"),
    ("spot", 2010, "長崎", "大河ドラマ「龍馬伝」", "2010年の大河ドラマは「龍馬伝」。坂本龍馬が活躍した長崎が、舞台になった",
     [A(art.ryoma, 520, 560, 300), A(art.taiga, 1000, 540, 360, "龍馬伝"), W_(1460, 480, "長崎", 90, rc("長崎")),
      W_(1460, 610, "10位→9位", 64, UP)],
     "この年、NHKの大河ドラマは「龍馬伝」。坂本龍馬が活躍した長崎が、何度も舞台になりました。"),
    ("spot", 2010, "奈良", "平城遷都1300年祭", "2010年 奈良で平城遷都1300年祭。奈良はこの頃、5位の常連だった",
     [A(art.palace, 560, 560, 460), A(art.deer, 1040, 560, 360), W_(1460, 480, "5位キープ", 84, rc("奈良")),
      W_(1460, 610, "2009〜2012年", 56)],
     "同じ2010年、奈良では、平城遷都1300年祭が開かれ、奈良は5位を守りました。実はこの頃が、奈良の全盛期なんです。"),

    ("year", 2011, "2011年。福岡が10位に戻ってきます。長野は8位に上がり、長崎は圏外へ。"),
    ("spot", 2011, "福岡", "九州新幹線 全線開業", "2011年3月 九州新幹線が全線開業。博多から鹿児島まで新幹線でつながった",
     [A(art.kyushu, 760, 520, 820), W_(760, 740, "博多 ⇄ 鹿児島中央", 60), W_(1500, 470, "圏外→10位", 72, UP),
      W_(1500, 600, "震災の翌日に開業", 48, (62, 120, 220))],
     "この年の3月、九州新幹線が全線開業。博多から鹿児島まで、新幹線でつながりました。ただ、開業は東日本大震災の翌日。お祝いのイベントの多くは、中止になりました。"),

    ("year", 2012, "2012年。長野が7位に上がり、なんと大阪を抜きます。一方、兵庫が圏外へ。"),
    ("spot", 2012, "兵庫", "大河ドラマ「平清盛」", "2012年の大河ドラマは神戸ゆかりの「平清盛」。それでも兵庫は圏外へ",
     [A(art.taiga, 560, 540, 400, "平清盛"), A(art.ship, 1040, 560, 360), W_(1480, 480, "9位→圏外", 76, (62, 120, 220)),
      W_(1480, 610, "追い風にならず", 56)],
     "この年の大河ドラマは、神戸ゆかりの「平清盛」。兵庫は盛り上げようとしましたが、ランキングでは、追い風になりませんでした。"),

    ("year", 2013, "2013年。神奈川が奈良を抜いて5位へ。奈良はここから、ランキングの順位を少しずつ下げていきます。福岡も7位に上がり、兵庫が10位に戻ってきました。"),
    ("year", 2014, "2014年は、10位が兵庫から長崎へ。この2県は、10位の席を何度も取り合います。"),

    ("year", 2015, "そして2015年、事件が起きます。東京が、殿堂入りの沖縄を抜いて、3位に上がったんです。沖縄が4位に入り、そして長崎が、10位から一気に5位へジャンプ！"),
    ("spot", 2015, "東京", "沖縄を抜いて3位", "2013年9月 東京オリンピックの開催が決まり、東京が改めて注目されていた",
     [A(art.tower, 520, 560, 280), A(art.torch, 900, 560, 340), W_(1420, 480, "4位→3位", 90, rc("東京")),
      W_(1420, 610, "2015〜2019年の5年間", 56)],
     "2年前の2013年、東京オリンピックの開催が決まりました。「おもてなし」が流行語になり、東京が改めて注目されていた時期です。東京の3位は、ここから5年続きます。"),
    ("spot", 2015, "長崎", "10位→5位", "2015年7月 軍艦島などの「明治日本の産業革命遺産」が世界遺産に",
     [A(art.gunkanjima, 640, 560, 600), W_(1380, 450, "世界遺産", 80, (220, 50, 50)), W_(1380, 580, "10位→5位", 90, UP),
      W_(1380, 700, "長崎の最高順位", 52)],
     "この年の7月、軍艦島などの「明治日本の産業革命遺産」が、世界遺産に登録されました。長崎の5位は、今も、長崎の最高順位です。"),

    ("year", 2016, "2016年。9位に、石川が初登場します。一方、長崎は圏外へ。世界遺産の勢いは、1年で落ち着きました。"),
    ("spot", 2016, "石川", "北陸新幹線 金沢開業", "2015年3月 北陸新幹線が金沢まで開業。東京から金沢まで約2時間半に",
     [A(art.hokuriku, 620, 400, 720), A(art.kotoji, 620, 650, 250), W_(1460, 470, "初登場9位", 84, (220, 50, 50)),
      W_(1460, 600, "東京⇄金沢 約2時間半", 52)],
     "前の年の春、北陸新幹線が金沢まで開業。東京から金沢まで、2時間半ほどで行けるようになりました。兼六園のある金沢に、観光客が押し寄せます。"),

    ("year", 2017, "2017年。石川は10位に下がりながらも、2年連続でトップ10。新幹線の効果は、一回きりではありませんでした。"),
    ("year", 2018, "2018年。長崎が、10位に戻ってきます。"),
    ("spot", 2018, "長崎", "ふたたび世界遺産", "2018年6月「長崎と天草地方の潜伏キリシタン関連遺産」が世界遺産に",
     [A(art.church, 560, 520, 380), W_(1300, 450, "世界遺産", 80, (220, 50, 50)), W_(1300, 580, "圏外→10位", 84, UP),
      W_(1300, 700, "2015年ほどは伸びず", 52)],
     "この年の6月、「長崎と天草地方の潜伏キリシタン関連遺産」が、世界遺産に決まりました。長崎は、世界遺産の年に上がる県なんです。ただ、今回は10位。2015年ほどの伸びはありませんでした。"),

    ("year", 2019, "2019年。大阪が奈良を抜いて、6位へ。石川も9位に戻ってきました。"),
    ("spot", 2019, "大阪", "万博決定とG20サミット", "2018年11月 2025年の万博の開催が決定。2019年6月 大阪でG20サミット",
     [A(art.expo_globe, 520, 540, 380), A(art.g20, 960, 560, 380), W_(1460, 480, "7位→6位", 90, rc("大阪")),
      W_(1460, 610, "奈良を抜いた", 56)],
     "前の年に、2025年の大阪・関西万博の開催が決まり、この年の6月には、大阪でG20サミットが開かれました。"),

    ("year", 2020, "2020年。沖縄が、5年ぶりに3位を取り返します。東京は4位に戻りました。"),
    ("spot", 2020, "東京", "新型コロナの流行", "発表元「東京都は魅力度などの点数が大幅に低下し、影響がみられる」",
     [A(art.virus, 520, 540, 360), A(art.mask, 900, 560, 300), W_(1440, 480, "3位→4位", 90, (62, 120, 220)),
      W_(1440, 610, "オリンピックも延期", 52)],
     "この年は、新型コロナの流行が始まった年。発表元は、全体では大きな変化はないとしながら、東京は、魅力度などの点数が大きく下がり、影響が見られる、と分析しています。オリンピックも延期になりました。"),
    ("spot", 2020, "沖縄", "首里城の火災のあとでも", "2019年10月 首里城が火災で焼失。それでも沖縄は3位に戻った",
     [A(art.shuri, 640, 560, 480, fire=True), W_(1400, 480, "4位→3位", 90, UP), W_(1400, 610, "5年ぶり", 60)],
     "ちなみに沖縄では、前の年の秋に、首里城が火事で焼けています。それでも、沖縄の順位は上がりました。"),

    ("year", 2021, "2021年。大阪が5位に上がり、過去最高の順位に。ここから3年連続で5位です。長崎は8位、そして10位は、石川と長野が、同じ点で並びました。"),
    ("year", 2022, "2022年は、大きな動きはありません。ただ、福岡がじわじわと上がってきています。"),
    ("year", 2023, "2023年。福岡が神奈川を抜いて、6位へ。2010年には圏外に落ちていた福岡が、ついに、関東の神奈川より上に来ました。"),

    ("year", 2024, "2024年。ここで静岡が、初めてトップ10に入ります。前の年に13位だった長野も、8位に戻ってきました。"),
    ("spot", 2024, "静岡", "初めてのトップ10", "2023年の大河ドラマは「どうする家康」。家康が晩年を過ごした静岡が舞台に",
     [A(art.fuji, 520, 560, 420), A(art.kabuto, 960, 560, 300), A(art.taiga, 1430, 470, 330, "どうする家康"),
      W_(1430, 760, "初登場9位", 64, (220, 50, 50))],
     "前の年、2023年の大河ドラマは「どうする家康」。徳川家康が晩年を過ごした静岡は、ドラマの舞台として、大きく取り上げられていました。"),

    ("year", 2025, "2025年。神奈川が、調査が始まって初めての4位。東京を抜きました。そして10位には、2014年以来、11年ぶりに兵庫が戻ってきました。"),
    ("spot", 2025, "神奈川", "史上初の4位", "2025年 神奈川は「住んでみたい県」(居住意欲度)でも1位",
     [A(art.ferris, 520, 520, 380), A(art.house, 920, 560, 320), A(art.medal, 1150, 470, 200, "1位"),
      W_(1500, 480, "5位→4位", 90, UP), W_(1500, 610, "調査史上初", 60)],
     "神奈川はこの年、「住んでみたい県」でも1位になっています。"),
    ("spot", 2025, "兵庫", "11年ぶりのトップ10", "2025年は大阪・関西万博の年。会場の夢洲へは、神戸からも船で行けた",
     [A(art.expo_globe, 520, 540, 360), A(art.ship, 960, 560, 400), W_(1460, 480, "圏外→10位", 80, UP),
      W_(1460, 610, "2014年以来", 60)],
     "この年は、大阪・関西万博の年。会場の夢洲には、神戸からも船で行くことができました。"),

    ("year", 2026, "そして最新の2026年。東京が4位を取り返し、神奈川は5位に。長崎が8位に戻り、静岡も10位で、トップ10に残りました。"),

    ("lines", "長い目でみると、奈良は5位の常連から、トップ10の外へ。逆に福岡と大阪は、じわじわとランキングの順位を上げてきました。"),
    ("count", "そして、2009年から2026年までにトップ10に入った県は、わずか13。47都道府県のうち、34の県は、一度もトップ10に入っていません。"),
    ("law", "ランキングの順位が上がった年をみると、世界遺産、新幹線、大河ドラマが、よく重なっていました。ただし、大河ドラマでも、兵庫のように、下がった年もあります。出来事が、そのまま順位を上げるとは限りません。"),
    ("summary", "今日のまとめです。1位北海道、2位京都は18年間不動。3位の沖縄を抜いたのは、東京の5年間だけ。そして4位から10位は、世界遺産や新幹線の年に、新しい県が飛び込んでくる席でした。来年、トップ10に初登場するのは、どの県でしょうか。",
     ["1位北海道", "3位の沖縄", "4位から10位"]),
    ("points", "最後に、総合ランキングです。3位を8点、4位を7点と、1つ下がるごとに1点ずつ減らし、10位を1点として、2009年から2026年まで、すべての年を足しました。11位は静岡、3点。10位は兵庫、9位は石川。8位は長崎、7位は長野、6位は福岡。5位奈良、71点。4位大阪、75点。そしてトップ3。3位、神奈川、100点。2位、東京、130点。1位は、沖縄、139点！ 3位の常連、沖縄が、総合王者でした。"),
    ("next", "次回のテーマは「1日1万歩は必要？」。その数字、どこから来たのでしょうか。"),
    ("outro", "新常識クロニクルでは、これからも、ランキングや常識の移り変わりを、データで追いかけていきます。あなたの県は、何位でしたか？ ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]


# ---------- 冒頭・説明・振り返りの画面 ----------
def podium(d, cx, base, names, k=(1, 1, 1), gray=False):
    """表彰台(左に2位、まん中に1位、右に3位)。"""
    spec = [(-330, 220, "2", 1), (0, 320, "1", 0), (330, 160, "3", 2)]
    for dx, h, no, idx in spec:
        kk = k[idx]
        if kk <= 0:
            continue
        hh = h * (0.4 + 0.6 * out_back(kk))
        col = (150, 154, 166) if gray else (TRIM if no == "1" else (220, 224, 232) if no == "2" else (205, 140, 90))
        d.rounded_rectangle([cx + dx - 140, base - hh, cx + dx + 140, base], radius=18, fill=col)
        text(d, (cx + dx, base - hh + 60), no, 80, INK if not gray else (90, 94, 106), anchor="mm")
        text(d, (cx + dx, base - hh - 50), names[idx], 64, WHITE if not gray else (150, 154, 166), anchor="mm")


def at_maker(narr, keys, draw, tail=0.6):
    """ナレーションの言葉が出るときに合わせて描く。draw(t, times)。"""
    def make(alen, lead):
        times = [lead + narr.index(k) / len(narr) * alen - 0.15 for k in keys]

        def frame(t):
            return draw(t, times)
        return frame, times[-1] + tail
    return WithAudio(make)


def hook_draw(t, ts):
    im, d = stage()
    k = [seg(t, ts[0], ts[0] + 0.4), seg(t, ts[1], ts[1] + 0.4), seg(t, ts[1] + 0.3, ts[1] + 0.7)]
    podium(d, W / 2, 760, ("北海道", "京都", "沖縄"), k)
    s = seg(t, ts[2], ts[2] + 0.4)
    if s > 0:
        sc = 1.5 - 0.5 * out_back(s)
        cx, cy = W / 2, 230
        d.rounded_rectangle([cx - 330 * sc, cy - 70 * sc, cx + 330 * sc, cy + 70 * sc], radius=24 * sc, fill=(220, 50, 50),
                            outline=WHITE, width=max(3, int(7 * sc)))
        text(d, (cx, cy), "18年間 不動", int(76 * sc), WHITE, anchor="mm")
    s2 = seg(t, ts[3], ts[3] + 0.4)
    if s2 > 0:
        chip(d, W / 2, 900, "4位〜10位は 毎年入れ替わる", (62, 120, 220), int(54 * (0.6 + 0.4 * out_back(s2))))
    return im


def top3_draw(t, ts):
    im, d = stage()
    a = seg(t, ts[0], ts[0] + 0.4)
    if a > 0:
        text(d, (W / 2, 140), "地域ブランド調査(ブランド総合研究所)", 50, TRIM, anchor="mm")
        text(d, (W / 2, 215), "毎年 約3万人に聞く・都道府県は2009年から", 40, WHITE, heavy=False, anchor="mm")
    k1 = seg(t, ts[1], ts[1] + 0.4)
    gray = t >= ts[3]
    podium(d, W / 2, 700, ("北海道", "京都", "沖縄"), (k1, k1, seg(t, ts[2], ts[2] + 0.4)), gray=gray)
    s = seg(t, ts[3], ts[3] + 0.4)
    if s > 0:
        sc = 1.5 - 0.5 * out_back(s)
        cx, cy = W / 2, 560
        d.rounded_rectangle([cx - 300 * sc, cy - 66 * sc, cx + 300 * sc, cy + 66 * sc], radius=22 * sc, fill=(220, 50, 50),
                            outline=WHITE, width=max(3, int(7 * sc)))
        text(d, (cx, cy), "今回は除外", int(72 * sc), WHITE, anchor="mm")
        text(d, (W / 2, 755), "※3位は2015〜2019年だけ東京", 34, SUB, heavy=False, anchor="mm")
    s2 = seg(t, ts[4], ts[4] + 0.3)
    if s2 > 0:
        for i in range(7):
            kk = seg(t, ts[4] + i * 0.12, ts[4] + i * 0.12 + 0.35)
            if kk <= 0:
                continue
            sc = 0.6 + 0.4 * out_back(kk)
            x = W / 2 + (i - 3) * 190
            d.rounded_rectangle([x - 80 * sc, 880 - 60 * sc, x + 80 * sc, 880 + 60 * sc], radius=20 * sc, fill=WHITE)
            text(d, (x, 880), f"{4 + i}位", int(48 * sc), INK, anchor="mm")
    return im


def legend_draw(t, ts):
    im = board_static(2009)
    d = ImageDraw.Draw(im)
    for i, p in enumerate(BOARD[2009]):
        y, h = row_y(i, 7)
        k = seg(t, ts[0] + i * 0.1, ts[0] + i * 0.1 + 0.35)
        if k > 0:
            draw_row(d, 0, y, h, 4 + i, p, ("", INK), scale=0.6 + 0.4 * out_back(k))
    q = out_cubic(seg(t, ts[1], ts[1] + 1.0))
    if q > 0:
        draw_pie(d, [a * q + 0.25 * (1 - q) for a in shares(2009)], cnt=counts(2009) if q >= 1 else None)
    names = [r for r, _ in REGIONS]
    shown = [None if t < ts[2 + i] else counts(2009)[i] for i in range(4)]
    hi = None
    for i in range(4):
        if t >= ts[2 + i]:
            hi = names[i]
    for i, ((name, col), n) in enumerate(zip(REGIONS, shown)):
        if n is None:
            continue
        x = 1250 + (i % 2) * 400
        y = 820 + (i // 2) * 76
        kk = seg(t, ts[2 + i], ts[2 + i] + 0.35)
        sc = (0.6 + 0.4 * out_back(kk)) * (1.1 if hi == name else 1.0)
        d.rounded_rectangle([x - 175 * sc, y - 30 * sc, x + 175 * sc, y + 30 * sc], radius=30 * sc, fill=col)
        text(d, (x - 150 * sc, y), name, int(36 * sc), WHITE, anchor="lm")
        text(d, (x + 150 * sc, y), f"{n}県", int(40 * sc), WHITE, anchor="rm")
    return im


def rank_or_none(pref, y):
    return ranks(y).get(pref)


LINE_PREFS = [("奈良", (220, 80, 80)), ("福岡", (60, 165, 105)), ("大阪", (240, 128, 40))]


def lines_draw(t, ts):
    im, d = stage()
    panel(d, (120, 130, 1800, 1000))
    text(d, (W / 2, 195), "順位の移り変わり(2009〜2026年)", 52, INK, anchor="mm")
    gx0, gx1, gy0, gy1 = 300, 1680, 280, 880
    rows = list(range(4, 11)) + ["圏外"]

    def ypos(r):
        i = 7 if r is None else r - 4
        return gy0 + i * (gy1 - gy0) / 7

    for r in rows:
        y = ypos(None if r == "圏外" else r)
        d.line([(gx0, y), (gx1, y)], fill=(225, 222, 214), width=3)
        text(d, (gx0 - 30, y), f"{r}位" if r != "圏外" else "圏外", 32, SUB, heavy=False, anchor="rm")
    for i, y in enumerate(YEARS):
        if (y - YEARS[0]) % 3 == 0 or y == YEARS[-1]:
            x = gx0 + i * (gx1 - gx0) / (len(YEARS) - 1)
            text(d, (x, gy1 + 50), str(y), 30, SUB, heavy=False, anchor="mm")
    for j, (pref, col) in enumerate(LINE_PREFS):
        k = seg(t, ts[j], ts[j] + 1.6)
        if k <= 0:
            continue
        pts = []
        n = len(YEARS)
        upto = k * (n - 1)
        for i, y in enumerate(YEARS):
            if i > upto + 1e-6:
                break
            pts.append((gx0 + i * (gx1 - gx0) / (n - 1), ypos(rank_or_none(pref, y))))
        if len(pts) >= 2:
            d.line(pts, fill=col, width=12, joint="curve")
        for x, y in pts:
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=col)
        x, y = pts[-1]
        d.rounded_rectangle([x + 16, y - 30, x + 16 + d.textlength(pref, font=font(36)) + 30, y + 30], radius=30, fill=col)
        text(d, (x + 31, y), pref, 36, WHITE, anchor="lm")
    return im


def all_prefs():
    seen = []
    for y in YEARS:
        for p in (*TOP3[y], *BOARD[y]):
            if p not in seen:
                seen.append(p)
    return seen


def count_draw(t, ts):
    im, d = stage()
    prefs = all_prefs()
    k0 = seg(t, ts[0], ts[0] + 0.4)
    if k0 > 0:
        text(d, (W / 2, 170), "18年間でトップ10に入った県", 60, WHITE, anchor="mm")
    for i, p in enumerate(prefs):
        kk = seg(t, ts[0] + 0.2 + i * 0.12, ts[0] + 0.55 + i * 0.12)
        if kk <= 0:
            continue
        x = 330 + (i % 5) * 315
        y = 330 + (i // 5) * 140
        sc = 0.6 + 0.4 * out_back(kk)
        col = COLOR[REGION_OF[p]] if p in REGION_OF else (130, 140, 160)
        d.rounded_rectangle([x - 130 * sc, y - 50 * sc, x + 130 * sc, y + 50 * sc], radius=50 * sc, fill=col)
        text(d, (x, y), p, int(52 * sc), WHITE, anchor="mm")
    s = seg(t, ts[1], ts[1] + 0.4)
    if s > 0:
        text(d, (W / 2, 790), f"たった {len(prefs)}", int(100 * (0.6 + 0.4 * out_back(s))), TRIM, anchor="mm")
    s2 = seg(t, ts[2], ts[2] + 0.4)
    if s2 > 0:
        text(d, (W / 2, 920), f"{47 - len(prefs)}県は 一度もトップ10に入っていない", 52, WHITE, anchor="mm")
    return im


def law_draw(t, ts):
    im, d = stage()
    panel(d, (120, 130, 1800, 1000))
    text(d, (W / 2, 200), "順位が上がった年に よく重なっていたもの", 52, INK, anchor="mm")
    cols = [(380, "世界遺産", "長崎 2015・2018", lambda dd, x, y: art.gunkanjima(dd, x, y, 380)),
            (960, "新幹線", "福岡 2011・石川 2016", lambda dd, x, y: art.hokuriku(dd, x, y, 440)),
            (1540, "大河ドラマ", "長崎 2010・静岡 2024", lambda dd, x, y: art.taiga(dd, x, y, 300, "大河"))]
    layers = []
    for i, (x, name, ex, f) in enumerate(cols):
        k = seg(t, ts[i], ts[i] + 0.45)
        if k <= 0:
            continue
        lay = blank()
        dd = ImageDraw.Draw(lay)
        f(dd, x, 480)
        sc = 0.6 + 0.4 * out_back(k)
        box = lay.getbbox()
        if box:
            crop = lay.crop(box)
            w_, h_ = crop.size
            crop = crop.resize((max(1, int(w_ * sc)), max(1, int(h_ * sc))))
            layers.append((crop, ((box[0] + box[2]) // 2 - crop.size[0] // 2, (box[1] + box[3]) // 2 - crop.size[1] // 2)))
        text(d, (x, 690), name, 60, (220, 50, 50), anchor="mm")
        text(d, (x, 770), ex, 38, SUB, heavy=False, anchor="mm")
    s = seg(t, ts[3], ts[3] + 0.4)
    if s > 0:
        d.rounded_rectangle([360, 850, 1560, 940], radius=45, fill=(230, 236, 248))
        text(d, (W / 2, 895), "ただし 兵庫は「平清盛」の2012年に圏外へ", 44, (62, 120, 220), anchor="mm")
    im = im.convert("RGBA")
    for crop, xy in layers:
        im.alpha_composite(crop, xy)
    return im.convert("RGB")


SUMMARY_ITEMS = [("1位 北海道・2位 京都", "18年間 不動", INK), ("3位 沖縄を抜いたのは", "東京の5年間だけ", INK),
                 ("4位〜10位は", "世界遺産・新幹線の年に入れ替わる", (220, 50, 50))]


def summary_draw(t, ts):
    im, d = stage()
    panel(d, (200, 150, 1720, 960))
    text(d, (960, 240), "まとめ", 76, INK, anchor="mm")
    for i, (a, b, c) in enumerate(SUMMARY_ITEMS):
        k = seg(t, ts[i], ts[i] + 0.4)
        if k > 0:
            y = 360 + i * 170
            d.rounded_rectangle([280, y, 1640, y + 130], radius=65, fill=(240, 236, 228))
            d.ellipse([300, y + 25, 380, y + 105], fill=c)
            text(d, (340, y + 65), str(i + 1), 48, WHITE, anchor="mm")
            text(d, (420, y + 65), a, 44, SUB, heavy=False, anchor="lm")
            text(d, (1610, y + 65), b, 50, c, anchor="rm")
    return im


NEXT_TITLE = "1日1万歩は必要？"


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 260), "次回のテーマ", 70, TRIM, anchor="mm")
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        im = im.convert("RGBA")
        lay = blank()
        cw.foot(ImageDraw.Draw(lay), W / 2, 560, 360 * (0.6 + 0.4 * k))
        im.alpha_composite(lay)
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    text(d, (W / 2, 850), NEXT_TITLE, 100, WHITE, anchor="mm")
    return im


TOPICS = ["1日1万歩は必要？", "サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "住みたい街ランキング", "都道府県の最下位争い"]


def outro_frame(t):
    im, d = stage()
    k = out_back(seg(t, 0.2, 0.7))
    if k > 0:
        text(d, (W / 2, 230), "新常識クロニクル", int(120 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
    a = seg(t, 0.6, 1.0)
    if a > 0:
        text(d, (W / 2, 350), "あなたの県は 何位でしたか？", 56, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)),
             anchor="mm")
    for i, tp in enumerate(TOPICS):
        kk = seg(t, 1.2 + i * 0.35, 1.55 + i * 0.35)
        if kk <= 0:
            continue
        x, y = (560 if i % 2 == 0 else 1360), 480 + (i // 2) * 110
        sc = 0.6 + 0.4 * out_back(kk)
        tw = d.textlength(tp, font=font(int(46 * sc))) + 60 * sc
        d.rounded_rectangle([x - tw / 2, y - 42 * sc, x + tw / 2, y + 42 * sc], radius=42 * sc, fill=(46, 58, 92))
        text(d, (x, y), tp, int(46 * sc), WHITE, anchor="mm")
    b = seg(t, 3.6, 4.1)
    if b > 0:
        sc = 0.6 + 0.4 * out_back(b)
        cx, cy = W / 2, 850
        bw, bh = 330 * sc, 62 * sc
        d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=bh, fill=(220, 40, 40))
        text(d, (cx, cy), "チャンネル登録", int(64 * sc), WHITE, anchor="mm")
        text(d, (cx, cy + bh + 40 * sc), "高評価・コメントもよろしくお願いします", int(36 * sc), WHITE, heavy=False, anchor="mm")
    return im


# ---------- 18年間の総合ランキング(3位=8点 … 10位=1点) ----------
POINT_OF = {3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1}


def points():
    """{県: 合計点}。1位・2位(北海道・京都)は除く。3位も数える。2021年の10位同点は両方1点。"""
    out = {}
    for y in YEARS:
        p3 = TOP3[y][2]
        out[p3] = out.get(p3, 0) + POINT_OF[3]
        for p, r in ranks(y).items():
            out[p] = out.get(p, 0) + POINT_OF[r]
    return sorted(out.items(), key=lambda x: -x[1])


def points_draw(t, ts):
    im, d = stage()
    panel(d, (200, 120, 1720, 1010))
    text(d, (W / 2, 180), "18年間の総合ランキング(1位・2位の北海道・京都を除く)", 46, INK, anchor="mm")
    text(d, (W / 2, 232), "3位=8点 4位=7点 … 10位=1点 で2009〜2026年を合計", 32, SUB, heavy=False, anchor="mm")
    pts = points()
    mx = pts[0][1]
    n = len(pts)
    order = {p: i for i, p in enumerate(reversed([p for p, _ in pts]))}   # 下位から出す
    for i, (p, v) in enumerate(pts):
        j = order[p]
        k = seg(t, ts[j], ts[j] + 0.5)
        if k <= 0:
            continue
        y = 290 + i * 64
        top = i < 3
        x0 = 520
        bw = (1600 - x0 - 120) * v / mx * out_cubic(k)
        text(d, (300, y + 26), f"{i + 1}位", 38 if top else 32, (220, 50, 50) if top else INK, anchor="mm")
        text(d, (370, y + 26), p, 40 if top else 34, INK, anchor="lm")
        d.rounded_rectangle([x0, y + 4, x0 + max(bw, 8), y + 48], radius=22, fill=rc(p))
        text(d, (x0 + max(bw, 8) + 16, y + 26), f"{round(v * min(1, k * 1.3))}点", 36 if top else 30, INK, anchor="lm")
    s1 = seg(t, ts[-1] + 0.6, ts[-1] + 1.0)
    if s1 > 0:
        sc = 1.4 - 0.4 * out_back(s1)
        cx, cy = 960, 316
        d.rounded_rectangle([cx - 150 * sc, cy - 50 * sc, cx + 150 * sc, cy + 50 * sc], radius=20 * sc, fill=(220, 50, 50),
                            outline=WHITE, width=max(3, int(6 * sc)))
        text(d, (cx, cy), "総合王者", int(42 * sc), WHITE, anchor="mm")
    return im


# ---------- 組み立て ----------
def dur(narr):
    return max(3.0, len(narr) / 8.0 + 0.8)


def year_telop(y):
    b = BOARD[y]
    s = " ".join(f"{min(4 + i, 10)}{p}" for i, p in enumerate(b))
    marks = [f"{p} {badge(y, p)[0]}" for p in b if badge(y, p)[0] in ("初登場", "復帰")]
    dr = dropped(y)
    extra = (" / " + "・".join(marks) if marks else "") + (" / 圏外へ:" + "・".join(dr) if dr else "")
    return f"ボード:{s}{extra}"


def build_plan():
    plan = []
    for sc in SCENES:
        kind = sc[0]
        narr = sc[1] if kind == "summary" else sc[-1]
        if kind == "hook":
            plan.append((at_maker(narr, ["1位は", "2位は", "一度も", "4位から"], hook_draw), 0, dur(narr),
                         ("つかみ", "表彰台 1北海道 2京都 3沖縄 →「18年間 不動」→ 4位〜10位は毎年入れ替わる", narr)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES[EPISODE]).save(img)
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr),
                         ("タイトル", f"新常識クロニクル:{EPISODES[EPISODE][0]}", narr)))
        elif kind == "top3":
            plan.append((at_maker(narr, ["使うのは", "1位の北海道", "3位も", "そこで今回は", "7つの席"], top3_draw, tail=1.4), 0, dur(narr),
                         ("1〜3位を除外", "地域ブランド調査・約3万人 → 表彰台が灰色に「今回は除外」→ 4位〜10位の7つの席", narr)))
        elif kind == "legend":
            plan.append((at_maker(narr, ["左が", "右の円グラフ", "関東", "関西", "九州", "中部"], legend_draw), 0, dur(narr),
                         ("見方", "左=4位〜10位の番付、右=7つの席の地方別の比率(円グラフ)", narr)))
        elif kind == "year":
            y = sc[1]
            fn, anim = year_maker(y)
            plan.append((fn, anim, dur(narr), (f"{y}年", year_telop(y), narr)))
        elif kind == "spot":
            _, y, pref, heading, tl, els, narr = sc
            fn, anim = spot_frames(y, pref, heading, tl, els)
            plan.append((fn, anim, dur(narr), (f"{y}年 {pref}「{heading}」", tl, narr)))
        elif kind == "lines":
            plan.append((at_maker(narr, ["奈良は", "福岡", "大阪"], lines_draw, tail=1.8), 0, dur(narr),
                         ("振り返り", "折れ線:奈良・福岡・大阪の順位(2009〜2026年)", narr)))
        elif kind == "count":
            plan.append((at_maker(narr, ["2009年から", "わずか", "34の県"], count_draw, tail=0.8), 0, dur(narr),
                         ("振り返り", f"トップ10に入った{len(all_prefs())}県", narr)))
        elif kind == "law":
            plan.append((at_maker(narr, ["世界遺産", "新幹線", "大河ドラマが", "兵庫"], law_draw), 0, dur(narr),
                         ("振り返り", "世界遺産・新幹線・大河ドラマ / ただし兵庫2012", narr)))
        elif kind == "summary":
            plan.append((at_maker(narr, sc[2], summary_draw), 0, dur(narr), ("まとめ", "", narr)))
        elif kind == "points":
            keys = [p for p, _ in reversed(points())]
            plan.append((at_maker(narr, keys, points_draw, tail=1.6), 0, dur(narr),
                         ("総合ランキング", "18年間の総合ランキング(3位=8点〜10位=1点):" + " ".join(f"{i + 1}位{p}{v}点" for i, (p, v) in enumerate(points())), narr)))
        elif kind == "next":
            plan.append((next_frame, 1.0, dur(narr), ("次回予告", NEXT_TITLE, narr)))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(narr), ("エンディング", "チャンネル登録・あなたの県は何位？", narr)))
    return plan


CHECKS = [
    "**全年の順位**:まとめサイト(bg-ranking.xyz)の表から作った。ブランド総合研究所の各年の発表(news.tiiki.jp・atpress のプレスリリース)で、4〜10位を1年ずつ確かめる。特に 2021年の10位同点(石川・長野)",
    "**円グラフ**:7つの席(2021年は8県)を地方で分けた比率。点数の比率ではない(2009〜2023年の点数が手に入らなかったため)",
    "**地方の分け方**:関東=東京・神奈川、関西=大阪・奈良・兵庫、九州・沖縄=福岡・長崎・沖縄、中部・北陸=長野・石川・静岡",
    "**調査の時期**:毎年6〜7月ごろの調査か、各年の調査期間を確かめる(「その年の出来事」が調査の前か後かが変わる)",
    "**回答者数「約3万人」**:2020年 31,734人、2025年 33,449人(確認済み)。年によって違う",
    "**2010 長崎**:大河ドラマ「龍馬伝」(2010年1〜11月)で長崎が舞台の回があること。調査時点でどこまで放送されていたか",
    "**2010 奈良**:平城遷都1300年祭(2010年)。「全盛期」は順位から言っているだけ(5位は2009〜2012年)",
    "**2011 福岡**:九州新幹線 鹿児島ルート全線開業 2011年3月12日、震災で記念式典などが中止",
    "**2012 兵庫**:大河ドラマ「平清盛」(2012年)と兵庫県・神戸市の観光キャンペーン。「追い風にならなかった」は順位から言っているだけ",
    "**2015 東京**:東京オリンピック開催決定 2013年9月。「おもてなし」は2013年の流行語大賞",
    "**2015 長崎**:「明治日本の産業革命遺産」世界遺産登録 2015年7月。ブランド総合研究所の2018年の資料が、2015年の5位と産業革命遺産に触れている(確認済み)。「5位が長崎の最高順位」は表で確認済み",
    "**2016 石川**:北陸新幹線 長野〜金沢 開業 2015年3月14日。東京〜金沢 最速2時間28分",
    "**2018 長崎**:潜伏キリシタン関連遺産 世界遺産登録決定 2018年6月30日。ブランド総合研究所の資料で10位への浮上に触れている(確認済み)",
    "**2019 大阪**:2025年万博の開催決定 2018年11月、G20大阪サミット 2019年6月",
    "**2020 東京**:発表元が「全体では大きな変化はない」「東京都は魅力度など各項目の点数が大幅に低下、一部で影響」と述べた(確認済み:travelvoice 2020年10月15日)。オリンピック延期の発表は2020年3月",
    "**2020 首里城**:首里城の火災 2019年10月31日",
    "**2024 静岡**:前年14位→9位、長野 13位→8位(確認済み)。「初めてトップ10」は表で確認済み。大河「どうする家康」(2023年)と静岡の関係は、発表元が言った理由ではない",
    "**2025 神奈川**:史上初の4位(確認済み)。居住意欲度1位(確認済み:マイナビ 2025年10月)",
    "**2025 兵庫**:10位は2014年以来(表で確認)。万博の期間中に神戸から夢洲への船の便があったか確認",
    "**イラスト**:龍馬・軍艦島・教会・新幹線・兼六園の灯籠・鹿・宮殿・トーチ・電波塔・ウイルス・首里城・富士山・かぶと・観覧車は、すべてこのスクリプトで描いた図形(`scripts/miryokudo_art.py`)。キャラクターやロゴ(せんとくん・五輪マーク・万博ロゴなど)は使っていない",
]


def write_script(plan):
    total = 0.0
    lines = [f"# 台本:{EPISODES[EPISODE][0]} 〜{EPISODES[EPISODE][1]}〜", "",
             "作成：2026-11-23 / 状態：初稿。`scripts/miryokudo_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーションの長さで決まる。", "",
             "この回は議席を使わない。最初に1〜3位を除外する理由を説明し、4位〜10位の番付ボード(左)と、7つの席の地方別の比率の円グラフ(右)で年ごとに見せる。"
             "順位が入れ替わった県・初めて入った県は「その年、何があった？」の場面でイラストつきで紹介する。", "",
             "| 時間 | 場面 | 画面のテロップ・内容 | ナレーション |", "|---|---|---|---|"]
    for _, _, sec, (name, tl, narr) in plan:
        m, s = divmod(int(total), 60)
        lines.append(f"| {m}:{s:02d} | {name} | {tl} | {narr} |")
        total += sec
    m, s = divmod(int(total), 60)
    lines += ["", f"合計：約{m}分{s:02d}秒", "", "## 4位〜10位の推移と地方別の比率", "",
              "| 年 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 関東 | 関西 | 九州・沖縄 | 中部・北陸 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for y in YEARS:
        b = BOARD[y]
        cells = b[:6] + ["・".join(b[6:])]
        lines.append(f"| {y} | " + " | ".join(cells) + " | " + " | ".join(str(c) for c in counts(y)) + " |")
    lines += ["", "## 18年間の総合ランキング(3位=8点・4位=7点 … 10位=1点。1位・2位の北海道・京都は除く)", "",
              "| 順位 | 県 | 合計点 |", "|---|---|---|"] + [f"| {i + 1} | {p} | {v} |" for i, (p, v) in enumerate(points())]
    lines += ["", "## 公開前に確認すること"] + [f"- {c}" for c in CHECKS] + [""]
    with open(SCRIPT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    base = SCRIPT_MD.replace("_story.md", "")
    t, marked, plain = 0.0, [], []
    for i, (_, _, sec, (name, _, narr)) in enumerate(plan, 1):
        m, s_ = divmod(int(t), 60)
        marked.append(f"【{i:02d}】{m}:{s_:02d} {name}\n{narr}\n")
        plain.append(narr + "\n")
        t += sec
    with open(base + "_narration.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(marked))
    with open(base + "_narration_plain.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(plain))
    return total


def stills(plan):
    out = os.path.join(OUT, "stills")
    os.makedirs(out, exist_ok=True)
    for i, (fn, anim, sec, meta) in enumerate(plan):
        if isinstance(fn, WithAudio):
            fn, anim = fn.make(dur(meta[2]) - 1.0, 0.35)
        fn(max(anim, 0.0) + 0.5).save(os.path.join(out, f"{i:02d}.png"))
    print(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = build_plan()
    if "--script" in sys.argv:
        total = write_script(plan)
        print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面、目安)")
        return
    if "--stills" in sys.argv:
        stills(plan)
        return
    import numpy as np
    import soundfile as sf
    from narrate import RATE
    LEAD, TAIL = 0.35, 0.55
    voices, new_plan = [], []
    for i, (fn, anim, sec, meta) in enumerate(plan):
        v = cs.voice_for(i, meta[2], os.path.join(OUT, "voice"))
        sec = max(anim + 0.3 if anim else 2.0, LEAD + len(v) / RATE + TAIL)
        if isinstance(fn, WithAudio):
            fn, anim = fn.make(len(v) / RATE, LEAD)
            sec = max(sec, anim + 0.3)
        voices.append(v)
        new_plan.append((fn, anim, sec, meta))
        print(f"声 {i + 1:3d}/{len(plan)} {len(v) / RATE:5.1f}秒 {meta[0]}", flush=True)
    plan = new_plan
    # 声のチェック:速さが他の場面よりずっと遅い(変な声が混じっている)、または音声認識で読み間違い・余計な音が見つかったら作り直す
    import re
    import statistics
    import voice_check

    def rate(v, narr):
        return len(re.sub(r"<#[\d.]+#>", "", narrate.mm_text(narr))) / (len(v) / RATE)
    med = statistics.median(rate(voices[i], plan[i][3][2]) for i in range(len(plan)))

    def issues(v, narr):
        out = [f"声が遅すぎる({len(v) / RATE:.1f}秒)"] if rate(v, narr) < med * 0.75 else []
        return out + voice_check.problems(narr, v, RATE)
    for i in range(len(plan)):
        narr = plan[i][3][2]
        best, best_n = voices[i], issues(voices[i], narr)
        for _ in range(5):
            if not best_n:
                break
            print(f"  ! 作り直し {plan[i][3][0]}: {best_n[0]}", flush=True)
            v = cs.voice_for(i, narr, os.path.join(OUT, "voice"), fresh=True)
            n = issues(v, narr)
            if len(n) <= len(best_n):
                best, best_n = v, n
        if best_n:
            print(f"  !! まだ問題あり {plan[i][3][0]}: {best_n}", flush=True)
        if best is not voices[i]:   # いちばん良い声をキャッシュに残す
            import hashlib
            import soundfile as sf
            key = hashlib.md5(f"{narrate.voice_key()}|{narrate.mm_text(narr)}".encode()).hexdigest()[:12]
            sf.write(os.path.join(OUT, "voice", f"{key}.wav"), best, RATE)
        voices[i] = best
        fn, anim, sec, meta = plan[i]
        plan[i] = (fn, anim, max(anim + 0.3, LEAD + len(best) / RATE + TAIL), meta)
    total = write_script(plan)
    print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面)")
    if "--voice" in sys.argv:
        return

    seg_dir = os.path.join(OUT, "_seg")
    os.makedirs(seg_dir, exist_ok=True)
    parts, audio = [], []
    for i, (fn, anim, sec, (name, _, _)) in enumerate(plan):
        mp4 = os.path.join(seg_dir, f"{i:03d}.mp4")
        cw.clip(fn, min(anim, sec), sec, mp4, os.path.join(seg_dir, "_frames"))
        parts.append(mp4)
        real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                    capture_output=True, text=True).stdout)
        n = int(round(real * RATE))
        a = np.zeros(n, dtype="float32")
        v = voices[i][: max(0, n - int(LEAD * RATE))]
        a[int(LEAD * RATE): int(LEAD * RATE) + len(v)] = v
        audio.append(a)
        print(f"{i + 1:3d}/{len(plan)} {name}", flush=True)
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    silent = os.path.join(seg_dir, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    wav = os.path.join(OUT, "narration.wav")
    sf.write(wav, np.concatenate(audio), RATE)
    out = os.path.join(OUT, "miryokudo_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
