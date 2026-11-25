"""コーヒー10年戦争：全16研究のカードと議席アニメを作り、絵だけの通し動画にする。

  python3 scripts/coffee_war.py   -> output/coffee_war/coffee_war_draft.mp4(と各カードの PNG)

ナレーションはまだ入っていない。カード1枚=CARD_SEC 秒(パーツが順に出る→席がひっくり返り天秤が傾く)。大きな動きは全画面の「開票速報」も入る。
"""
import math
import os
import shutil
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion import Card, out_back, parliament_frame, seg  # noqa: E402
from frames import (  # noqa: E402
    BAD, GOOD, H, INK, LBL, LW, PANEL, SUB, TRIM, W, WHITE, arrow, bean, font, heart, hemicycle, line,
    meter, mug, panel, parliament, stage, study_card, text,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "coffee_war")
FPS = 30
CARD_SEC = 6.5
CREAM = (255, 236, 214)
LIGHT_BAD = (214, 228, 250)


# ---------- 追加のピクトグラム ----------
def check(d, cx, cy, r, color=GOOD):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    line(d, [(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.35)], WHITE, LW)


def cross(d, cx, cy, r, color=BAD):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    k = r * 0.4
    line(d, [(cx - k, cy - k), (cx + k, cy + k)], WHITE, LW)
    line(d, [(cx - k, cy + k), (cx + k, cy - k)], WHITE, LW)


def warn(d, cx, cy, s, fill=(255, 214, 102)):
    pts = [(cx, cy - s * 0.55), (cx + s * 0.6, cy + s * 0.45), (cx - s * 0.6, cy + s * 0.45)]
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=INK, width=LW, joint="curve")
    line(d, [(cx, cy - s * 0.18), (cx, cy + s * 0.12)], INK, LW)
    d.ellipse([cx - 6, cy + s * 0.24, cx + 6, cy + s * 0.36], fill=INK)


def thermo(d, cx, top, h, level=0.8, color=(220, 50, 50)):
    w = h * 0.16
    d.rounded_rectangle([cx - w / 2, top, cx + w / 2, top + h * 0.78], radius=w / 2, outline=INK, width=LW, fill=PANEL)
    d.rounded_rectangle([cx - w / 4, top + h * 0.78 * (1 - level), cx + w / 4, top + h * 0.8], radius=w / 4, fill=color)
    r = h * 0.14
    d.ellipse([cx - r, top + h * 0.72, cx + r, top + h * 0.72 + 2 * r], fill=color, outline=INK, width=LW)


def crowd(d, x0, y0, cols, rows, h, fill=None):
    for r in range(rows):
        for c in range(cols):
            bean(d, x0 + c * h * 0.85, y0 + r * h * 0.95, h * 0.8, fill=fill, w=5)


def flags(d, x0, y0, n, s):
    cols = [(240, 128, 40), (62, 120, 220), (70, 160, 110), (220, 70, 70), (250, 200, 60)]
    for i in range(n):
        x = x0 + (i % 5) * s * 1.25
        y = y0 + (i // 5) * s * 0.95
        d.rounded_rectangle([x, y, x + s, y + s * 0.66], radius=8, fill=cols[i % 5], outline=INK, width=5)
        line(d, [(x, y), (x, y + s * 0.85)], INK, 5)


def u_chart(d, x0, y0, w, h):
    line(d, [(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], INK, 6)
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((x0 + 20 + t * (w - 40), y0 + 20 + (h - 50) * (1 - 2.8 * (t - 0.45) ** 2)))
    d.line(pts, fill=GOOD, width=LW, joint="curve")
    bx, by = x0 + 20 + 0.45 * (w - 40), y0 + 20 + (h - 50)
    d.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=GOOD)
    text(d, (bx, by - 26), "3〜4杯", 30, INK, heavy=False, anchor="md")
    text(d, (x0 - 14, y0 + 10), "リスク", 24, SUB, heavy=False, anchor="ra")


def gavel(d, cx, cy, s):
    """裁判所の建物(柱とひさし、階段)に「カリフォルニア州」の札。"""
    col = (236, 230, 216)
    w = s * 0.62
    d.polygon([(cx - w, cy - s * 0.18), (cx, cy - s * 0.52), (cx + w, cy - s * 0.18)], fill=col, outline=INK, width=LW)
    d.rectangle([cx - w, cy - s * 0.18, cx + w, cy - s * 0.08], fill=col, outline=INK, width=6)
    for i in range(5):
        x = cx - w * 0.8 + i * w * 0.4
        d.rectangle([x - s * 0.04, cy - s * 0.08, x + s * 0.04, cy + s * 0.32], fill=WHITE, outline=INK, width=5)
    d.rectangle([cx - w * 1.05, cy + s * 0.32, cx + w * 1.05, cy + s * 0.4], fill=col, outline=INK, width=6)
    d.rectangle([cx - w * 1.15, cy + s * 0.4, cx + w * 1.15, cy + s * 0.48], fill=col, outline=INK, width=6)
    text(d, (cx, cy - s * 0.27), "COURT", int(s * 0.08), INK, anchor="mm")
    text(d, (cx, cy + s * 0.6), "カリフォルニア州の裁判所", int(s * 0.1), INK, heavy=False, anchor="mm")


def label(d, x, y, w, h, title, color=(255, 214, 102)):
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=color, outline=INK, width=LW)
    text(d, (x + w / 2, y + h / 2), title, int(h * 0.36), INK, anchor="mm")


def broken_heart(d, cx, cy, s):
    heart(d, cx, cy, s, fill=BAD)
    r = s * 0.28
    line(d, [(cx, cy - r * 0.6), (cx - r * 0.3, cy + r * 0.3), (cx + r * 0.25, cy + r * 0.8), (cx, cy + r * 1.9)], PANEL, 8)


def brain(d, cx, cy, s, fill=LIGHT_BAD):
    for dx, dy, r in ((-0.28, -0.12, 0.3), (0.0, -0.25, 0.32), (0.28, -0.12, 0.3), (-0.22, 0.15, 0.28), (0.22, 0.15, 0.28)):
        d.ellipse([cx + (dx - r) * s, cy + (dy - r) * s, cx + (dx + r) * s, cy + (dy + r) * s], fill=fill, outline=INK, width=LW)
    for dx, dy, r in ((-0.28, -0.12, 0.3), (0.0, -0.25, 0.32), (0.28, -0.12, 0.3), (-0.22, 0.15, 0.28), (0.22, 0.15, 0.28)):
        rr = r - 0.05
        d.ellipse([cx + (dx - rr) * s, cy + (dy - rr) * s, cx + (dx + rr) * s, cy + (dy + rr) * s], fill=fill)
    line(d, [(cx, cy - s * 0.4), (cx, cy + s * 0.35)], INK, 6)


def sugar(d, x, y, s):
    d.rounded_rectangle([x, y, x + s, y + s], radius=s * 0.18, fill=WHITE, outline=INK, width=LW)
    for i, j in ((0.3, 0.3), (0.65, 0.45), (0.4, 0.7)):
        d.ellipse([x + i * s - 5, y + j * s - 5, x + i * s + 5, y + j * s + 5], fill=SUB)


def dripper(d, cx, top, s):
    d.polygon([(cx - s * 0.5, top), (cx + s * 0.5, top), (cx + s * 0.18, top + s * 0.6), (cx - s * 0.18, top + s * 0.6)],
              fill=CREAM, outline=INK, width=LW)
    line(d, [(cx - s * 0.32, top + s * 0.68), (cx + s * 0.32, top + s * 0.68)], INK, LW)
    for i in range(3):
        y = top + s * 0.8 + i * 18
        d.ellipse([cx - 5, y - 5, cx + 5, y + 5], fill=INK)


def pot(d, cx, top, s):
    d.rounded_rectangle([cx - s * 0.45, top + s * 0.2, cx + s * 0.45, top + s * 0.8], radius=s * 0.12, fill=CREAM, outline=INK, width=LW)
    line(d, [(cx - s * 0.62, top + s * 0.32), (cx - s * 0.45, top + s * 0.32)], INK, LW)
    line(d, [(cx + s * 0.45, top + s * 0.32), (cx + s * 0.62, top + s * 0.32)], INK, LW)
    for i in range(3):
        x = cx - s * 0.25 + i * s * 0.25
        line(d, [(x, top + s * 0.12), (x + 8, top + s * 0.02), (x, top - s * 0.08)], INK, 6)


def foot(d, cx, cy, s, fill=GOOD):
    for dx, dy in ((-0.25, 0.1), (0.25, -0.15)):
        x, y = cx + dx * s, cy + dy * s
        d.ellipse([x - s * 0.16, y - s * 0.3, x + s * 0.16, y + s * 0.18], fill=fill, outline=INK, width=6)
        d.ellipse([x - s * 0.12, y + s * 0.22, x + s * 0.12, y + s * 0.4], fill=fill, outline=INK, width=6)


def ecg(d, x, y, w, color=BAD):
    pts = [(x, y), (x + w * 0.25, y), (x + w * 0.33, y - 50), (x + w * 0.42, y + 40), (x + w * 0.5, y - 70),
           (x + w * 0.58, y + 30), (x + w * 0.66, y), (x + w, y)]
    d.line(pts, fill=color, width=LW, joint="curve")


def moon(d, cx, cy, r, fill=(255, 214, 102)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=INK, width=LW)
    d.ellipse([cx - r * 0.3, cy - r * 1.05, cx + r * 1.4, cy + r * 0.75], fill=PANEL)


def sun(d, cx, cy, r, fill=(255, 190, 60)):
    for i in range(8):
        a = i * math.pi / 4
        line(d, [(cx + r * 1.3 * math.cos(a), cy + r * 1.3 * math.sin(a)),
                 (cx + r * 1.7 * math.cos(a), cy + r * 1.7 * math.sin(a))], INK, 6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=INK, width=LW)


def papers(d, x, y, s, n=4):
    for i in range(n - 1, -1, -1):
        ox, oy = x + i * 16, y - i * 16
        d.rounded_rectangle([ox, oy, ox + s * 0.75, oy + s], radius=12, fill=WHITE, outline=INK, width=6)
    for k in range(4):
        line(d, [(x + s * 0.12, y + s * (0.22 + k * 0.17)), (x + s * 0.6, y + s * (0.22 + k * 0.17))], SUB, 5)


def big(d, xy, s, color, size=72, anchor="lm"):
    text(d, xy, s, size, color, anchor=anchor)


# ---------- 各研究のピクトグラム ----------
def p01(d):
    mug(d, 190, 600, 140, fill=CREAM)
    big(d, (420, 690), "＝", INK, 80, "mm")
    warn(d, 590, 690, 190)
    big(d, (760, 690), "？", BAD, 120, "lm")


def p02(d):
    crowd(d, 150, 590, 5, 2, 105)
    arrow(d, 640, 720, 700)
    heart(d, 850, 630, 110)
    big(d, (850, 725), "長生き", GOOD, 48, "ma")


def p03(d):
    mug(d, 170, 610, 120, fill=CREAM)
    check(d, 380, 640, 46)
    text(d, (290, 780), "コーヒー", 34, INK, heavy=False, anchor="ma")
    line(d, [(520, 590), (520, 800)], (222, 218, 210), 4)
    thermo(d, 680, 585, 200)
    big(d, (760, 650), "65℃超", (220, 50, 50), 56, "lm")
    cross(d, 980, 720, 40)


def p04(d):
    flags(d, 150, 600, 10, 72)
    arrow(d, 620, 700, 690)
    crowd(d, 740, 620, 2, 1, 110, fill=GOOD)
    heart(d, 1000, 650, 80)


def p05(d):
    u_chart(d, 200, 590, 460, 190)
    line(d, [(720, 590), (720, 800)], (222, 218, 210), 4)
    bean(d, 850, 600, 170, fill=CREAM)
    d.ellipse([850, 700, 905, 755], fill=PANEL, outline=INK, width=6)
    cross(d, 990, 650, 36)
    text(d, (990, 700), "妊娠中", 30, INK, heavy=False, anchor="ma")


def p06(d):
    gavel(d, 280, 690, 230)
    arrow(d, 470, 550, 690)
    mug(d, 600, 610, 130, fill=CREAM)
    label(d, 780, 640, 260, 110, "がん警告")


def p08(d):
    for i in range(6):
        mug(d, 150 + (i % 3) * 112, 600 + (i // 3) * 118, 82, steam=False, w=7, fill=CREAM)
    arrow(d, 520, 600, 690)
    broken_heart(d, 720, 640, 140)
    big(d, (840, 690), "+22%", BAD, 80, "lm")


def p09(d):
    label(d, 170, 630, 280, 120, "がん警告")
    line(d, [(160, 760), (460, 620)], BAD, LW + 6)
    arrow(d, 520, 600, 690)
    mug(d, 660, 610, 130, fill=CREAM)
    check(d, 920, 680, 60)


def p10(d):
    dripper(d, 230, 600, 170)
    check(d, 400, 650, 44)
    line(d, [(520, 590), (520, 800)], (222, 218, 210), 4)
    pot(d, 680, 620, 170)
    big(d, (820, 640), "△", BAD, 90, "lm")
    text(d, (950, 780), "60歳以上の男性", 28, INK, heavy=False, anchor="mb")


def p11(d):
    for i in range(6):
        mug(d, 150 + (i % 3) * 112, 600 + (i // 3) * 118, 82, steam=False, w=7, fill=CREAM)
    arrow(d, 520, 600, 690)
    brain(d, 730, 690, 220)
    big(d, (870, 690), "+53%", BAD, 80, "lm")


def p12(d):
    mug(d, 170, 620, 130, fill=CREAM)
    big(d, (370, 700), "+", INK, 80, "mm")
    sugar(d, 430, 650, 100)
    arrow(d, 580, 660, 700)
    heart(d, 780, 660, 120)
    big(d, (880, 700), "-3割", GOOD, 80, "lm")


def p14(d):
    for i, (x, draw, val, col) in enumerate(((150, "foot", "+1000歩", GOOD), (470, "ecg", "×1.5", BAD), (790, "moon", "-36分", BAD))):
        if draw == "foot":
            foot(d, x + 120, 650, 150)
        elif draw == "ecg":
            ecg(d, x + 20, 660, 220)
        else:
            moon(d, x + 120, 650, 60)
        text(d, (x + 120, 735), val, 52, col, anchor="ma")


def p15(d):
    sun(d, 220, 650, 52)
    mug(d, 340, 610, 100, fill=CREAM)
    big(d, (500, 650), "-16%", GOOD, 64, "lm")
    line(d, [(720, 590), (720, 800)], (222, 218, 210), 4)
    moon(d, 810, 650, 52)
    text(d, (950, 640), "一日中", 40, INK, anchor="mm")
    text(d, (950, 700), "差なし", 44, SUB, anchor="mm")


def p16(d):
    papers(d, 170, 620, 160)
    arrow(d, 400, 480, 690)
    for i in range(3):
        mug(d, 520 + i * 110, 625, 82, steam=False, w=7, fill=CREAM)
    heart(d, 960, 650, 110)


def p07(d):
    for i in range(8):
        mug(d, 150 + (i % 4) * 112, 585 + (i // 4) * 118, 82, steam=False, w=7, fill=CREAM)
    arrow(d, 610, 690, 690)
    bean(d, 790, 575, 215, fill=GOOD)
    heart(d, 975, 610, 80)
    text(d, (975, 700), "長生き", 54, GOOD, anchor="ma")


def p13(d):
    meter(d, 250, 740, 105, needle=0.88)
    text(d, (250, 770), "160/100以上", 28, INK, heavy=False, anchor="ma")
    text(d, (410, 700), "+", 80, INK, anchor="mm")
    mug(d, 460, 615, 92, fill=CREAM)
    mug(d, 580, 615, 92, fill=CREAM)
    arrow(d, 730, 810, 690)
    bean(d, 880, 585, 205, fill=BAD)
    text(d, (955, 655), "×2", 84, BAD, anchor="la")


G, B = "g", "b"
# (年, 国, 種類, 見出し[(文字, 色)], データ, 絵, 前, 後, 速報の見出し, 出典)
EVENTS = [
    ("1991", "WHO の機関", "公的機関の判断", [[("コーヒーに", INK)], [("発がん性", B), ("の疑い", INK)]],
     [("機関", "IARC"), ("分類", "グループ2B"), ("意味", "可能性がある")], p01, 50, 35,
     "WHO の機関「発がん性の疑い」", "出典：IARC Monographs Vol.51(1991)"),
    ("2015", "日本", "約9万人の追跡調査", [[("飲む人ほど", INK)], [("死亡リスクが", INK), ("低い", G)]],
     [("対象", "約9万人"), ("年齢", "40〜69歳"), ("種類", "観察研究")], p02, 35, 41,
     "日本の9万人調査「飲む人ほど長生き」", "出典：Saito et al., American Journal of Clinical Nutrition 2015(JPHC研究)"),
    ("2016", "WHO の機関", "公的機関の判断", [[("発がん性は", INK), ("判断できず", G)], [("ただし", INK), ("65℃超は危険", B)]],
     [("見直し", "1,000以上"), ("コーヒー", "グループ3"), ("熱い飲み物", "グループ2A")], p03, 41, 53,
     "WHO の機関「判断できず」に変更", "出典：IARC Monographs Vol.116(2016)"),
    ("2017", "ヨーロッパ10か国", "約52万人の追跡調査", [[("10か国", G), ("どこでも", INK)], [("死亡リスクが", INK), ("低い", G)]],
     [("対象", "約52万人"), ("国", "10か国"), ("種類", "観察研究")], p04, 53, 59,
     "欧州52万人「どの国でも同じ結果」", "出典：Gunter et al., Annals of Internal Medicine 2017(EPIC)"),
    ("2017", "イギリス", "研究のまとめ", [[("1日", INK), ("3〜4杯", G), ("が", INK)], [("いちばん好結果", G)]],
     [("まとめた数", "200以上"), ("最適", "3〜4杯"), ("例外", "妊娠中")], p05, 59, 66,
     "英国の研究まとめ「3〜4杯が最適」", "出典：Poole et al., BMJ 2017"),
    ("2018.3", "アメリカ", "裁判所の判断", [[("裁判所", INK), ("「がんの", B)], [("警告表示が必要」", B)]],
     [("場所", "ロサンゼルス"), ("理由", "アクリルアミド"), ("確定", "2018年5月")], p06, 66, 51,
     "裁判所「がんの警告表示が必要」", "出典：NPR 2018/3/30 ほか"),
    ("2018.7", "イギリス", "約50万人の追跡調査", [[("1日", INK), ("8杯以上", G), ("でも", INK)], [("死亡リスクは", INK), ("低い", G)]],
     [("対象", "約50万人"), ("期間", "10年"), ("種類", "観察研究")], p07, 51, 57,
     "英国50万人「8杯以上でもいい結果」", "出典：Loftfield et al., JAMA Internal Medicine 2018(UK Biobank)"),
    ("2019.5", "オーストラリア", "約35万人の追跡調査", [[("1日", INK), ("6杯以上", B), ("で", INK)], [("心臓病リスク", INK), ("+22%", B)]],
     [("対象", "約35万人"), ("比べた相手", "1〜2杯の人"), ("種類", "観察研究")], p08, 57, 51,
     "豪の研究「6杯以上で心臓病+22%」", "出典：Zhou & Hyppönen, American Journal of Clinical Nutrition 2019"),
    ("2019.6", "アメリカ", "州の決定", [[("州が", INK), ("「警告は", G)], [("不要」", G), ("と決定", INK)]],
     [("決めた所", "カリフォルニア州"), ("理由", "危険は小さい"), ("施行", "2019年10月")], p09, 51, 66,
     "カリフォルニア州「警告は不要」", "出典：California OEHHA(2019)"),
    ("2020", "ノルウェー", "約50万人の追跡調査", [[("濾したコーヒー", G), ("は◯", INK)], [("煮出し", B), ("は△", INK)]],
     [("対象", "約50万人"), ("年齢", "20〜79歳"), ("注意", "60歳以上の男性")], p10, 66, 69,
     "ノルウェー「濾したコーヒーは◯」", "出典：Tverdal et al., European Journal of Preventive Cardiology 2020"),
    ("2021", "オーストラリア", "約40万人の追跡調査", [[("1日", INK), ("6杯以上", B), ("で", INK)], [("認知症", B), ("の可能性+53%", INK)]],
     [("対象", "約40万人"), ("脳の画像", "約1.8万人"), ("種類", "観察研究")], p11, 69, 63,
     "豪の研究「6杯以上で認知症+53%」", "出典：Pham et al., Nutritional Neuroscience 2021"),
    ("2022.5", "中国のチーム", "約17万人の追跡調査", [[("砂糖入り", G), ("でも", INK)], [("死亡リスク", INK), ("約3割低い", G)]],
     [("対象", "約17万人"), ("杯数", "1.5〜3.5杯"), ("データ", "英国")], p12, 63, 69,
     "中国のチーム「砂糖入りでもOK」", "出典：Liu et al., Annals of Internal Medicine 2022"),
    ("2022.12", "日本", "約1.9万人の追跡調査", [[("血圧が高い人は", INK)], [("1日2杯", B), ("で死亡", INK), ("2倍", B)]],
     [("対象", "約1.9万人"), ("年齢", "40〜79歳"), ("緑茶", "差なし")], p13, 69, 66,
     "日本の研究「高血圧なら2杯で2倍」", "出典：Teramoto et al., Journal of the American Heart Association 2022(JACC研究)"),
    ("2023", "アメリカ", "100人の実験", [[("飲む日は", INK), ("歩数↑", G)], [("でも", INK), ("脈の乱れ↑ 睡眠↓", B)]],
     [("対象", "100人"), ("方法", "くじで飲む日"), ("期間", "14日")], p14, 66, 63,
     "くじ引き実験「歩数↑ でも睡眠↓」", "出典：Marcus et al., New England Journal of Medicine 2023"),
    ("2025.1", "アメリカ", "約4万人の追跡調査", [[("朝だけ", G), ("飲む人は", INK)], [("死亡リスク", INK), ("-16%", G)]],
     [("対象", "約4万人"), ("朝だけ", "-16%"), ("一日中", "差なし")], p15, 63, 66,
     "米国4万人「朝のコーヒーがいい」", "出典：Wang et al., European Heart Journal 2025"),
    ("2025.8", "研究のまとめ", "研究のまとめ", [[("1日", INK), ("3〜5杯", G), ("で", INK)], [("主な病気のリスク", INK), ("低い", G)]],
     [("範囲", "2025年まで"), ("杯数", "3〜5杯"), ("注意", "観察研究中心")], p16, 66, 76,
     "2025年の研究まとめ「3〜5杯で低リスク」", "出典：Emadi & Kamangar, Nutrients 2025"),
]
WEIGHT = {"公的機関の判断": 15, "裁判所の判断": 15, "州の決定": 15, "研究のまとめ": 10}


def color_of(c):
    return GOOD if c == G else BAD if c == B else c


def title_card(path):
    """タイトル画面(サムネイルと同じテンプレート)。"""
    from thumbnail import EPISODES, series_card
    series_card(*EPISODES["coffee_war"]).save(path)


def rules_card(path):
    im, d = stage()
    panel(d, (300, 150, 1620, 960))
    text(d, (W / 2, 230), "議席を動かすルール", 80, INK, anchor="mm")
    rows = [("公的機関・裁判所の判断", "15議席"), ("たくさんの研究のまとめ", "10議席"),
            ("数十万人の追跡調査", "6議席"), ("条件つきの結果", "3議席")]
    for i, (k, v) in enumerate(rows):
        y = 360 + i * 120
        d.rounded_rectangle([380, y, 1540, y + 96], radius=48, fill=(240, 236, 228))
        text(d, (430, y + 48), k, 52, INK, anchor="lm")
        text(d, (1490, y + 48), v, 60, GOOD, anchor="rm")
    text(d, (W / 2, 880), "※ 議席は演出のための目安です", 36, SUB, heavy=False, anchor="mm")
    im.save(path)


def final_frame(good, t, note="ほとんどが観察研究：因果関係はまだ証明されていない"):
    im, d = stage()
    text(d, (W / 2, 160), "最終結果", 80, TRIM, anchor="mm")
    cx, cy, R = W / 2, 720, 470
    hemicycle(d, cx, cy, R, good)
    for x, lab, n, c in ((cx - R * 0.72, LBL[0], good, GOOD), (cx + R * 0.72, LBL[1], 100 - good, BAD)):
        text(d, (x, cy + 30), lab, 52, c, anchor="ma")
        text(d, (x, cy + 86), str(n), 112, WHITE, anchor="ma")
    # 「当選確実」のハンコ → 押されそうになって止まる
    k = seg(t, 0.8, 1.3)
    if k > 0:
        sc = 1.6 - 0.6 * out_back(k)
        sx, sy, r = cx, cy - 95, 150 * sc
        red = (220, 60, 60)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(27, 36, 58), outline=red, width=max(4, int(14 * sc)))
        text(d, (sx, sy - 35 * sc), "当選確実", int(58 * sc), red, anchor="mm")
        if t > 1.8:
            text(d, (sx, sy + 45 * sc), "まだ出せない", int(40 * sc), WHITE, anchor="mm")
    a = seg(t, 2.0, 2.5)
    if a > 0:
        text(d, (cx, 985), note, 40,
             tuple(int(255 * a + 40 * (1 - a)) for _ in range(3)), heavy=False, anchor="mm")
    return im


def clip(frame_fn, anim_sec, total_sec, mp4, tmp):
    """frame_fn(t) を anim_sec 秒ぶん描き、残りは最後の絵で止める。"""
    os.makedirs(tmp, exist_ok=True)
    n = int(anim_sec * FPS)
    for f in range(n + 1):
        frame_fn(f / FPS).save(os.path.join(tmp, f"{f:04d}.png"))
    hold = max(0.0, total_sec - (n + 1) / FPS)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-vf", f"tpad=stop_mode=clone:stop_duration={hold:.3f}", "-pix_fmt", "yuv420p", "-c:v", "libx264",
                    "-r", str(FPS), mp4], check=True)
    shutil.rmtree(tmp)


BIG = ("公的機関の判断", "裁判所の判断", "州の決定")


def main():
    os.makedirs(OUT, exist_ok=True)
    seg_dir = os.path.join(OUT, "_seg")
    os.makedirs(seg_dir, exist_ok=True)
    tmp = os.path.join(seg_dir, "_frames")
    parts = []

    def add(frame_fn, anim_sec, total_sec):
        mp4 = os.path.join(seg_dir, f"{len(parts):03d}.mp4")
        clip(frame_fn, anim_sec, total_sec, mp4, tmp)
        parts.append(mp4)

    title_card(os.path.join(OUT, "00_title.png"))
    title = Image.open(os.path.join(OUT, "00_title.png"))
    add(lambda t: title, 0, 4)
    rules_card(os.path.join(OUT, "00_rules.png"))
    rules = Image.open(os.path.join(OUT, "00_rules.png"))
    add(lambda t: rules, 0, 5)
    add(lambda t: parliament_frame("開戦前", "最初は50対50", 50, 50, t), 0.6, 3)

    for i, (year, country, kind, title_, facts, picto, before, after, headline, source) in enumerate(EVENTS, 1):
        rows = [[(s, color_of(c)) for s, c in row] for row in title_]
        diff = after - before
        delta = f"{'いい派' if diff > 0 else '悪い派'} +{abs(diff)}議席"
        card = Card(year, country, kind, rows, facts, picto, before, after, delta, source)
        card.frame(Card.ANIM_END).save(os.path.join(OUT, f"{i:02d}_{year.replace('.', '_')}.png"))
        add(card.frame, Card.ANIM_END, CARD_SEC)
        big = kind in BIG or (before > 50) != (after > 50)
        if big:  # 大きな動きは全画面の「開票速報」でもう一度見せる
            add(lambda t, y=year, h=headline, b=before, a=after: parliament_frame(y, h, b, a, t), 2.6, 3.6)
        print(f"{i:2d}/{len(EVENTS)} {year} {before}->{after}{' (速報)' if big else ''}", flush=True)

    add(lambda t: final_frame(EVENTS[-1][7], t), 2.6, 6)
    final_frame(EVENTS[-1][7], 3).save(os.path.join(OUT, "99_final.png"))

    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    out = os.path.join(OUT, "coffee_war_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
