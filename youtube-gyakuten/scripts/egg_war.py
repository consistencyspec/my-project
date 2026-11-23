"""卵は1日1個まで？：研究カードのデータ(EVENTS)と、卵の回のピクトグラム。

物語版の動画は scripts/egg_story.py で作る(このファイルはデータと絵だけ)。
  python3 scripts/egg_war.py   -> output/egg_war/*.png(全15枚のカードを確認用に書き出す)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, LW, PANEL, SUB, WHITE, arrow, bean, heart, line, meter, text  # noqa: E402
import coffee_war as cw  # noqa: E402
from coffee_war import big, broken_heart, check, cross, crowd, label, papers  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "egg_war")
YOLK = (255, 190, 50)
SHELL = (255, 246, 230)
RED = (220, 60, 60)


# ---------- 卵の回のピクトグラム ----------
def egg(d, cx, cy, s, fill=SHELL, half=False):
    """殻つきの卵(下がふくらんだ形)。s=高さ。half=True で上半分がない(半個)。"""
    pts = []
    for i in range(72):
        a = i / 72 * 2 * math.pi
        y = math.sin(a)
        x = math.cos(a) * (1 + 0.14 * y)
        pts.append((cx + x * s * 0.37, cy + y * s * 0.5))
    if half:
        pts = [p for p in pts if p[1] >= cy - 2]
        pts = pts + [(cx + s * 0.37, cy)]
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=INK, width=LW, joint="curve")
    if half:  # 切り口に黄身
        r = s * 0.2
        d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 1.1], fill=YOLK, outline=INK, width=6)


def fried(d, cx, cy, s):
    """目玉焼き。"""
    for dx, dy, r in ((-0.18, 0.02, 0.32), (0.16, -0.06, 0.3), (0.05, 0.16, 0.3), (-0.05, -0.18, 0.26)):
        d.ellipse([cx + (dx - r) * s - 5, cy + (dy - r) * s - 5, cx + (dx + r) * s + 5, cy + (dy + r) * s + 5], fill=INK)
    for dx, dy, r in ((-0.18, 0.02, 0.32), (0.16, -0.06, 0.3), (0.05, 0.16, 0.3), (-0.05, -0.18, 0.26)):
        d.ellipse([cx + (dx - r) * s + 4, cy + (dy - r) * s + 4, cx + (dx + r) * s - 4, cy + (dy + r) * s - 4], fill=WHITE)
    r = s * 0.17
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YOLK, outline=INK, width=6)


def yolk(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YOLK, outline=INK, width=LW)
    d.ellipse([cx - r * 0.5, cy - r * 0.55, cx - r * 0.15, cy - r * 0.2], fill=WHITE)


def rabbit(d, cx, cy, s):
    """座ったウサギ(横向き)。(cx, cy)=体の中心。"""
    for ex in (0.08, 0.26):  # 耳
        d.rounded_rectangle([cx + ex * s, cy - s * 0.95, cx + (ex + 0.13) * s, cy - s * 0.3], radius=s * 0.07,
                            fill=WHITE, outline=INK, width=LW)
    d.ellipse([cx - s * 0.5, cy - s * 0.25, cx + s * 0.3, cy + s * 0.45], fill=WHITE, outline=INK, width=LW)  # 体
    d.ellipse([cx - s * 0.02, cy - s * 0.45, cx + s * 0.5, cy + s * 0.05], fill=WHITE, outline=INK, width=LW)  # 頭
    d.ellipse([cx + s * 0.3, cy - s * 0.27, cx + s * 0.36, cy - s * 0.21], fill=INK)  # 目
    d.ellipse([cx - s * 0.6, cy + s * 0.05, cx - s * 0.4, cy + s * 0.25], fill=WHITE, outline=INK, width=6)  # しっぽ


def grass(d, cx, base, s):
    for dx, h in ((-0.3, 0.7), (-0.1, 1.0), (0.1, 0.8), (0.3, 0.6)):
        line(d, [(cx + dx * s, base), (cx + (dx + 0.06) * s, base - h * s * 0.5), (cx + (dx + 0.14) * s, base - h * s)],
             (70, 160, 110), LW)


def vessel(d, cx, cy, w, h, plaque=True):
    """血管の断面(横の管)。plaque=True で内側に脂がたまる。"""
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h / 2, fill=(250, 214, 210), outline=INK, width=LW)
    if plaque:
        d.ellipse([cx - w * 0.2, cy - h * 0.5, cx + w * 0.2, cy - h * 0.05], fill=YOLK, outline=INK, width=6)
        d.ellipse([cx - w * 0.12, cy + h * 0.1, cx + w * 0.16, cy + h * 0.5], fill=YOLK, outline=INK, width=6)


def liver(d, cx, cy, s):
    """肝臓(赤茶の丸い形)。"""
    pts = []
    for i in range(60):
        a = i / 60 * 2 * math.pi
        r = 1 + 0.25 * math.cos(a) - 0.12 * math.sin(2 * a)
        pts.append((cx + math.cos(a) * s * 0.5 * r, cy + math.sin(a) * s * 0.28 * (1.1 - 0.4 * math.cos(a))))
    d.polygon(pts, fill=(196, 92, 80))
    d.line(pts + [pts[0]], fill=INK, width=LW, joint="curve")


def bacon(d, cx, cy, s):
    """ベーコン(波打つ帯)。"""
    pts_t, pts_b = [], []
    for i in range(31):
        t = i / 30
        x = cx - s * 0.5 + t * s
        y = cy + math.sin(t * math.pi * 3) * s * 0.06
        pts_t.append((x, y - s * 0.13))
        pts_b.append((x, y + s * 0.13))
    d.polygon(pts_t + pts_b[::-1], fill=(214, 96, 86))
    mid = [(x, y + s * 0.13) for x, y in pts_t]
    d.line(mid, fill=(255, 226, 214), width=int(s * 0.05))
    d.line(pts_t + pts_b[::-1] + [pts_t[0]], fill=INK, width=LW, joint="curve")


def butter(d, cx, cy, s):
    d.polygon([(cx - s * 0.5, cy), (cx - s * 0.2, cy - s * 0.25), (cx + s * 0.5, cy - s * 0.25), (cx + s * 0.2, cy)],
              fill=(255, 236, 140), outline=INK, width=6)
    d.rectangle([cx - s * 0.5, cy, cx + s * 0.2, cy + s * 0.25], fill=(255, 226, 110), outline=INK, width=6)
    d.polygon([(cx + s * 0.2, cy), (cx + s * 0.5, cy - s * 0.25), (cx + s * 0.5, cy), (cx + s * 0.2, cy + s * 0.25)],
              fill=(240, 206, 90), outline=INK, width=6)


def flag_jp(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4], radius=10, fill=WHITE, outline=INK, width=6)
    d.ellipse([cx - s * 0.22, cy - s * 0.22, cx + s * 0.22, cy + s * 0.22], fill=RED)


def eggs_row(d, x, cy, n, s, gap=None, fill=SHELL):
    gap = gap or s * 0.85
    for i in range(n):
        egg(d, x + i * gap, cy, s, fill=fill)


def struck(d, x0, y0, x1, y1):
    line(d, [(x0, y1), (x1, y0)], RED, LW + 6)


def wine(d, cx, top, s, color=INK):
    """ワイングラス(次回予告)。暗い背景では color=WHITE。"""
    d.chord([cx - s * 0.35, top, cx + s * 0.35, top + s * 0.7], 0, 180, fill=(190, 40, 70))
    d.arc([cx - s * 0.35, top, cx + s * 0.35, top + s * 0.7], 0, 180, fill=color, width=LW)
    line(d, [(cx - s * 0.35, top + s * 0.35), (cx - s * 0.35, top + s * 0.05)], color, LW)
    line(d, [(cx + s * 0.35, top + s * 0.35), (cx + s * 0.35, top + s * 0.05)], color, LW)
    line(d, [(cx, top + s * 0.7), (cx, top + s * 1.05)], color, LW)
    line(d, [(cx - s * 0.22, top + s * 1.08), (cx + s * 0.22, top + s * 1.08)], color, LW)


# ---------- 各研究のピクトグラム(カードの中、x 150〜1080 / y 580〜800) ----------
def q01(d):
    rabbit(d, 260, 700, 190)
    big(d, (440, 690), "＋", INK, 80, "mm")
    yolk(d, 560, 690, 60)
    arrow(d, 650, 730, 690)
    vessel(d, 900, 690, 260, 120)


def q02(d):
    eggs_row(d, 210, 680, 3, 130)
    big(d, (500, 690), "/週", INK, 64, "lm")
    label(d, 720, 630, 330, 120, "300mg未満")


def q03(d):
    crowd(d, 150, 590, 4, 2, 105)
    egg(d, 640, 690, 120)
    arrow(d, 710, 790, 690)
    heart(d, 900, 640, 110)
    check(d, 1010, 620, 36)


def q04(d):
    flag_jp(d, 250, 690, 170)
    arrow(d, 390, 470, 690)
    label(d, 510, 625, 300, 130, "上限の目安")
    egg(d, 940, 690, 130)
    cross(d, 1010, 620, 34)


def q05(d):
    crowd(d, 150, 590, 4, 2, 105)
    eggs_row(d, 620, 690, 2, 100, 70)
    arrow(d, 760, 840, 690)
    heart(d, 960, 640, 110)


def q06(d):
    papers(d, 180, 600, 170)
    arrow(d, 420, 500, 690)
    egg(d, 600, 690, 120)
    big(d, (670, 690), "まで", INK, 46, "lm")
    heart(d, 960, 640, 110)


def q07(d):
    flag_jp(d, 250, 690, 170)
    label(d, 450, 630, 300, 120, "上限の目安")
    struck(d, 440, 630, 760, 750)
    check(d, 900, 690, 70)


def q08(d):
    label(d, 180, 630, 320, 120, "1日300mg")
    struck(d, 170, 630, 510, 750)
    arrow(d, 560, 640, 690)
    eggs_row(d, 760, 690, 3, 120, 100)


def q09(d):
    crowd(d, 150, 590, 4, 2, 105)
    egg(d, 620, 690, 120)
    arrow(d, 690, 770, 690)
    heart(d, 860, 640, 100)
    big(d, (930, 690), "-11%", GOOD, 56, "lm")


def q10(d):
    egg(d, 250, 710, 150, half=True)
    big(d, (360, 690), "+", INK, 80, "mm")
    arrow(d, 430, 510, 690)
    broken_heart(d, 640, 640, 120)
    big(d, (740, 690), "+6%", BAD, 64, "lm")
    big(d, (900, 690), "死亡+8%", BAD, 44, "lm")


def q11(d):
    heart(d, 240, 640, 130, fill=(220, 70, 70))
    arrow(d, 360, 440, 690)
    egg(d, 560, 690, 130)
    check(d, 640, 620, 38)
    big(d, (760, 660), "高齢者は", INK, 40, "lm")
    big(d, (760, 720), "2個まで", GOOD, 56, "lm")


def q12(d):
    flag_jp(d, 230, 690, 150)
    meter(d, 480, 760, 105, needle=0.85)
    text(d, (480, 785), "脂質異常症", 26, INK, heavy=False, anchor="ma")
    egg(d, 800, 690, 140)
    big(d, (880, 650), "約", INK, 40, "lm")
    big(d, (880, 715), "200mg", BAD, 50, "lm")


def q13(d):
    crowd(d, 150, 590, 4, 2, 105)
    egg(d, 620, 710, 130, half=True)
    arrow(d, 690, 770, 690)
    big(d, (800, 650), "死亡", INK, 46, "lm")
    big(d, (800, 730), "+7%", BAD, 64, "lm")


def q14(d):
    bean(d, 230, 585, 170, fill=(200, 200, 210))
    text(d, (230, 790), "70歳以上", 30, INK, heavy=False, anchor="ma")
    eggs_row(d, 430, 690, 3, 100, 70)
    arrow(d, 620, 700, 690)
    heart(d, 820, 640, 100)
    big(d, (910, 690), "-29%", GOOD, 60, "lm")


def q15(d):
    eggs_row(d, 220, 690, 2, 130, 95)
    check(d, 380, 620, 38)
    line(d, [(520, 590), (520, 800)], (222, 218, 210), 4)
    bacon(d, 700, 660, 220)
    butter(d, 720, 760, 140)
    cross(d, 900, 640, 38)
    text(d, (980, 740), "飽和脂肪", 40, BAD, anchor="mm")


G, B = "g", "b"
# (年, 国, 種類, 見出し[(文字, 色)], データ, 絵, 前, 後, 速報の見出し, 出典)
EVENTS = [
    ("1913", "ロシア", "ウサギの実験", [[("ウサギに", INK), ("卵黄", B), ("を", INK)], [("血管が", INK), ("詰まった", B)]],
     [("対象", "ウサギ"), ("与えた物", "卵黄など"), ("注意", "ウサギは草食")], q01, 50, 47,
     "ウサギの実験「血管が詰まった」", "出典：Anitschkow & Chalatow(1913)"),
    ("1968", "アメリカ", "学会の公式勧告", [[("卵は", INK), ("週3個まで", B)]],
     [("出した所", "米国心臓協会"), ("卵", "週3個まで"), ("コレステロール", "1日300mg未満")], q02, 47, 32,
     "米国心臓協会「卵は週3個まで」", "出典：American Heart Association(1968)"),
    ("1999", "アメリカ", "約12万人の追跡調査", [[("1日1個", G), ("でも", INK)], [("心臓病は", INK), ("増えない", G)]],
     [("対象", "約12万人"), ("期間", "8〜14年"), ("例外", "糖尿病の人")], q03, 32, 35,
     "ハーバード大「1日1個でも増えない」", "出典：Hu et al., JAMA 1999"),
    ("2005", "日本", "国の基準", [[("国の基準に", INK)], [("コレステロールの", INK), ("上限", B)]],
     [("出した所", "厚生労働省"), ("男性", "750mg未満"), ("女性", "600mg未満")], q04, 35, 20,
     "日本の基準に「上限の目安」", "出典：日本人の食事摂取基準(2005年版)"),
    ("2006", "日本", "約9万人の追跡調査", [[("よく食べても", INK)], [("心臓病は", INK), ("増えない", G)]],
     [("対象", "約9万人"), ("年齢", "40〜69歳"), ("種類", "観察研究")], q05, 20, 26,
     "日本の9万人調査「心臓病は増えない」", "出典：Nakamura et al., British Journal of Nutrition 2006(JPHC研究)"),
    ("2013", "中国のチーム", "研究のまとめ", [[("1日1個", G), ("までなら", INK)], [("心臓病・脳卒中", INK), ("増えず", G)]],
     [("まとめた数", "17の報告"), ("範囲", "1日1個まで"), ("例外", "糖尿病の人")], q06, 26, 33,
     "研究のまとめ「1日1個まで問題なし」", "出典：Rong et al., BMJ 2013"),
    ("2015", "日本", "国の基準", [[("コレステロールの", INK)], [("上限を", INK), ("撤廃", G)]],
     [("出した所", "厚生労働省"), ("理由", "根拠が足りない"), ("例外", "脂質異常症の人")], q07, 33, 48,
     "日本の基準「上限の目安をやめる」", "出典：日本人の食事摂取基準(2015年版)"),
    ("2016", "アメリカ", "国の指針", [[("国の指針から", INK)], [("300mgの上限", G), ("が消えた", INK)]],
     [("指針", "2015〜2020年版"), ("発表", "2016年1月"), ("ただし", "食べすぎ注意")], q08, 48, 63,
     "アメリカの指針「300mgの上限をやめる」", "出典：Dietary Guidelines for Americans 2015–2020"),
    ("2018", "中国", "約42万人の追跡調査", [[("毎日食べる人", G), ("は", INK)], [("心臓・血管の病気", INK), ("-11%", G)]],
     [("対象", "約42万人"), ("期間", "約9年"), ("脳出血", "-26%")], q09, 63, 69,
     "中国42万人「毎日の卵で-11%」", "出典：Qin et al., Heart 2018(China Kadoorie Biobank)"),
    ("2019.3", "アメリカ", "約3万人の追跡調査", [[("1日", INK), ("半個", B), ("増えるごとに", INK)], [("死亡リスク", INK), ("+8%", B)]],
     [("対象", "約3万人"), ("期間", "中央値17.5年"), ("心臓病", "+6%")], q10, 69, 63,
     "米国3万人「卵はやっぱり危ない」", "出典：Zhong et al., JAMA 2019"),
    ("2019.12", "アメリカ", "学会の公式見解", [[("健康な人は", INK)], [("1日1個", G), ("までOK", INK)]],
     [("出した所", "米国心臓協会"), ("健康な人", "1日1個"), ("高齢者", "1日2個まで")], q11, 63, 78,
     "米国心臓協会「1日1個までOK」", "出典：Carson et al., Circulation 2020(2019年12月公開)"),
    ("2020", "日本", "条件つきの基準", [[("脂質異常症の人は", INK)], [("1日200mg未満", B)]],
     [("出した所", "厚生労働省"), ("対象", "脂質異常症の人"), ("卵1個", "約200mg")], q12, 78, 75,
     "日本の基準「脂質異常症の人は控えめに」", "出典：日本人の食事摂取基準(2020年版)"),
    ("2021", "アメリカ", "約52万人の追跡調査", [[("1日", INK), ("半個", B), ("増えるごとに", INK)], [("死亡リスク", INK), ("+7%", B)]],
     [("対象", "約52万人"), ("期間", "中央値16年"), ("白身だけ", "むしろ低め")], q13, 75, 69,
     "米国52万人「半個ごとに+7%」", "出典：Zhuang et al., PLOS Medicine 2021(NIH-AARP)"),
    ("2025.1", "オーストラリア", "70歳以上の追跡調査", [[("週1〜6回", G), ("食べる人は", INK)], [("心臓病の死亡", INK), ("-29%", G)]],
     [("対象", "約8,700人"), ("年齢", "70歳以上"), ("毎日", "差なし")], q14, 69, 72,
     "豪の70歳以上「週に数個で-29%」", "出典：Nutrients 2025;17(2):323(ASPREE)"),
    ("2025.7", "オーストラリア", "61人の実験", [[("1日2個", G), ("でも", INK)], [("悪玉コレステロール", INK), ("↓", G)]],
     [("対象", "61人"), ("期間", "各5週間"), ("上げた物", "飽和脂肪")], q15, 72, 75,
     "くじ引き実験「真犯人は飽和脂肪」", "出典：Carter et al., American Journal of Clinical Nutrition 2025"),
]


def main():
    from motion import Card
    os.makedirs(OUT, exist_ok=True)
    for i, (year, country, kind, title, facts, picto, before, after, _, source) in enumerate(EVENTS, 1):
        rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
        diff = after - before
        card = Card(year, country, kind, rows, facts, picto, before, after,
                    f"{'いい派' if diff > 0 else '悪い派'} +{abs(diff)}議席", source)
        path = os.path.join(OUT, f"{i:02d}_{year.replace('.', '_')}.png")
        card.frame(Card.ANIM_END).save(path)
        print(path)


if __name__ == "__main__":
    sys.exit(main())
