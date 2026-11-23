"""赤ワインは体にいい？：研究カードのデータ(EVENTS)と、赤ワインの回のピクトグラム(新常識クロニクル 第3回)。

物語版の動画は scripts/wine_story.py で作る(このファイルはデータと絵だけ)。
  python3 scripts/wine_war.py   -> output/wine_war/*.png(全14枚のカードを確認用に書き出す)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, LW, PANEL, SUB, WHITE, arrow, bean, heart, line, text  # noqa: E402
import coffee_war as cw  # noqa: E402
from coffee_war import big, broken_heart, brain, check, cross, crowd, label, papers, warn  # noqa: E402
from egg_war import RED, flag_jp, struck, wine  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "wine_war")
WINE = (150, 30, 60)
GRAPE = (120, 60, 150)
LEAF = (70, 160, 110)
CHEESE = (255, 210, 90)
GLASS_FILL = (190, 40, 70)


# ---------- 赤ワインの回のピクトグラム ----------
def bottle(d, cx, top, h, label_text=""):
    """ワインのボトル。top=口の上、h=高さ。"""
    w = h * 0.3
    neck = w * 0.34
    body_top = top + h * 0.36
    d.rounded_rectangle([cx - neck / 2, top, cx + neck / 2, body_top + 10], radius=6, fill=WINE, outline=INK, width=LW)
    d.rounded_rectangle([cx - w / 2, body_top, cx + w / 2, top + h], radius=w * 0.3, fill=WINE, outline=INK, width=LW)
    d.rounded_rectangle([cx - w * 0.38, top + h * 0.55, cx + w * 0.38, top + h * 0.8], radius=8, fill=PANEL, outline=INK, width=5)
    if label_text:
        text(d, (cx, top + h * 0.675), label_text, int(w * 0.28), INK, anchor="mm")
    d.rectangle([cx - neck / 2 + 4, top + 4, cx + neck / 2 - 4, top + h * 0.06], fill=(230, 200, 150))


def glass(d, cx, top, s):
    """ワイングラス(明るいパネルの上)。"""
    wine(d, cx, top, s, color=INK)


def grapes(d, cx, cy, s):
    """ぶどうの房。"""
    rows = [(0, -0.36, 3), (0, -0.12, 3), (0, 0.12, 2), (0, 0.34, 1)]
    r = s * 0.12
    for _, dy, n in rows:
        for i in range(n):
            x = cx + (i - (n - 1) / 2) * r * 2.05
            y = cy + dy * s
            d.ellipse([x - r, y - r, x + r, y + r], fill=GRAPE, outline=INK, width=6)
            d.ellipse([x - r * 0.5, y - r * 0.55, x - r * 0.15, y - r * 0.2], fill=(200, 170, 230))
    line(d, [(cx, cy - s * 0.48), (cx + s * 0.05, cy - s * 0.62)], INK, LW)
    d.ellipse([cx + s * 0.04, cy - s * 0.72, cx + s * 0.34, cy - s * 0.52], fill=LEAF, outline=INK, width=6)


def flag3(d, cx, cy, s, cols, vertical=True):
    """3色旗(フランス・イタリアなど)。"""
    x0, y0, x1, y1 = cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4
    for i, c in enumerate(cols):
        if vertical:
            d.rectangle([x0 + (x1 - x0) * i / 3, y0, x0 + (x1 - x0) * (i + 1) / 3, y1], fill=c)
        else:
            d.rectangle([x0, y0 + (y1 - y0) * i / 3, x1, y0 + (y1 - y0) * (i + 1) / 3], fill=c)
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=INK, width=6)


def flag_fr(d, cx, cy, s):
    flag3(d, cx, cy, s, [(40, 70, 160), WHITE, (220, 50, 50)])


def flag_it(d, cx, cy, s):
    flag3(d, cx, cy, s, [(30, 150, 80), WHITE, (220, 50, 50)])


def flag_dk(d, cx, cy, s):
    x0, y0, x1, y1 = cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4
    d.rectangle([x0, y0, x1, y1], fill=(200, 30, 50))
    d.rectangle([x0 + s * 0.38, y0, x0 + s * 0.52, y1], fill=WHITE)
    d.rectangle([x0, cy - s * 0.07, x1, cy + s * 0.07], fill=WHITE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=INK, width=6)


def cheese(d, cx, cy, s):
    """三角のチーズ(穴あき)。"""
    pts = [(cx - s * 0.5, cy + s * 0.3), (cx + s * 0.5, cy + s * 0.3), (cx + s * 0.5, cy - s * 0.1), (cx - s * 0.5, cy + s * 0.05)]
    d.polygon(pts, fill=CHEESE)
    d.line(pts + [pts[0]], fill=INK, width=LW, joint="curve")
    for dx, dy, r in ((-0.2, 0.17, 0.06), (0.15, 0.1, 0.08), (0.35, 0.2, 0.045)):
        d.ellipse([cx + (dx - r) * s, cy + (dy - r) * s, cx + (dx + r) * s, cy + (dy + r) * s], fill=(230, 170, 60))


def mouse(d, cx, cy, s):
    """横向きのネズミ(右向き)。"""
    d.ellipse([cx - s * 0.45, cy - s * 0.22, cx + s * 0.25, cy + s * 0.25], fill=(225, 225, 232), outline=INK, width=LW)
    d.ellipse([cx + s * 0.05, cy - s * 0.2, cx + s * 0.45, cy + s * 0.12], fill=(225, 225, 232), outline=INK, width=LW)
    d.ellipse([cx + s * 0.02, cy - s * 0.38, cx + s * 0.22, cy - s * 0.14], fill=(250, 200, 210), outline=INK, width=6)
    d.ellipse([cx + s * 0.28, cy - s * 0.09, cx + s * 0.33, cy - s * 0.04], fill=INK)
    d.ellipse([cx + s * 0.42, cy - s * 0.05, cx + s * 0.5, cy + s * 0.03], fill=(240, 140, 160))
    pts = [(cx - s * 0.45, cy + s * 0.05), (cx - s * 0.62, cy - s * 0.05), (cx - s * 0.75, cy + s * 0.08)]
    d.line(pts, fill=INK, width=6, joint="curve")


def globe(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 226, 250), outline=INK, width=LW)
    for k in (-0.5, 0, 0.5):
        y = cy + k * r
        hw = math.sqrt(max(0, 1 - k * k)) * r
        d.line([(cx - hw, y), (cx + hw, y)], fill=INK, width=5)
    d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], outline=INK, width=5)
    d.polygon([(cx - r * 0.6, cy - r * 0.3), (cx - r * 0.1, cy - r * 0.55), (cx, cy - r * 0.1), (cx - r * 0.4, cy + r * 0.15)],
              fill=LEAF)
    d.polygon([(cx + r * 0.2, cy + r * 0.1), (cx + r * 0.65, cy - r * 0.05), (cx + r * 0.5, cy + r * 0.5), (cx + r * 0.25, cy + r * 0.55)],
              fill=LEAF)


def dna(d, cx, cy, h):
    pts1, pts2 = [], []
    for i in range(41):
        t = i / 40
        y = cy - h / 2 + t * h
        x = math.sin(t * math.pi * 3) * h * 0.18
        pts1.append((cx + x, y))
        pts2.append((cx - x, y))
    for i in range(0, 41, 4):
        d.line([pts1[i], pts2[i]], fill=SUB, width=5)
    d.line(pts1, fill=GOOD, width=LW, joint="curve")
    d.line(pts2, fill=BAD, width=LW, joint="curve")


def red_face(d, cx, top, h):
    """お酒で顔が赤くなる人。"""
    bean(d, cx, top, h)
    hr = h * 0.17
    d.ellipse([cx - hr + 6, top + 6, cx + hr - 6, top + 2 * hr - 6], fill=(240, 120, 120))
    for dx in (-0.35, 0.35):
        d.ellipse([cx + dx * hr - 5, top + hr - 8, cx + dx * hr + 5, top + hr + 2], fill=INK)


def tv(d, cx, cy, s, msg=""):
    d.rounded_rectangle([cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.35], radius=20, fill=(60, 72, 104), outline=INK, width=LW)
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.31, cx + s * 0.5, cy + s * 0.26], radius=12, fill=(230, 240, 255))
    line(d, [(cx - s * 0.25, cy + s * 0.48), (cx + s * 0.25, cy + s * 0.48)], INK, LW)
    line(d, [(cx, cy + s * 0.36), (cx, cy + s * 0.48)], INK, LW)
    if msg:
        fs = int(min(s * 0.16, s * 0.16 * (s * 0.9) / max(1, d.textlength(msg, font=cw.font(int(s * 0.16))))))
        text(d, (cx, cy - s * 0.02), msg, fs, INK, anchor="mm")


def ex_drinker(d, cx, top, h):
    """お酒をやめた人(グラスに✕)。"""
    bean(d, cx, top, h, fill=(214, 228, 250))
    glass(d, cx + h * 0.55, top + h * 0.25, h * 0.45)
    cross(d, cx + h * 0.75, top + h * 0.2, h * 0.12)


# ---------- 各研究のピクトグラム(カードの中、x 150〜1080 / y 580〜800) ----------
def w01(d):
    cw.flags(d, 170, 610, 10, 70)
    arrow(d, 560, 640, 690)
    glass(d, 760, 610, 130)
    big(d, (840, 650), "多い国ほど", INK, 36, "lm")
    heart(d, 1000, 680, 70)


def w02(d):
    flag_fr(d, 240, 690, 150)
    cheese(d, 450, 690, 170)
    big(d, (560, 690), "なのに", INK, 44, "lm")
    heart(d, 800, 640, 110)
    glass(d, 970, 610, 140)


def w03(d):
    flag_dk(d, 230, 690, 140)
    crowd(d, 350, 600, 3, 2, 100)
    glass(d, 690, 610, 130)
    arrow(d, 760, 830, 690)
    big(d, (850, 690), "-49%", GOOD, 64, "lm")


def w04(d):
    flag_jp(d, 230, 690, 150)
    crowd(d, 360, 600, 3, 2, 100)
    big(d, (680, 660), "週150g", GOOD, 50, "lm")
    big(d, (680, 725), "未満", INK, 40, "lm")
    big(d, (880, 690), "-36%", GOOD, 64, "lm")


def w05(d):
    flag_it(d, 220, 690, 130)
    papers(d, 360, 600, 170)
    arrow(d, 560, 640, 690)
    glass(d, 720, 610, 130)
    heart(d, 880, 640, 90)
    big(d, (960, 690), "-32%", GOOD, 52, "lm")


def w06(d):
    grapes(d, 250, 700, 200)
    arrow(d, 360, 440, 690)
    mouse(d, 600, 700, 230)
    big(d, (780, 650), "死亡", INK, 44, "lm")
    big(d, (780, 730), "-31%", GOOD, 60, "lm")


def w07(d):
    flag_it(d, 220, 690, 130)
    grapes(d, 420, 700, 180)
    big(d, (530, 690), "多くても", INK, 44, "lm")
    heart(d, 820, 640, 100)
    big(d, (900, 690), "差なし", BAD, 52, "lm")


def w08(d):
    bean(d, 230, 585, 150)
    text(d, (230, 760), "一生飲まない", 26, INK, heavy=False, anchor="ma")
    ex_drinker(d, 470, 585, 150)
    text(d, (470, 760), "病気でやめた", 26, BAD, heavy=False, anchor="ma")
    big(d, (720, 690), "を分けると", INK, 44, "lm")
    cross(d, 1000, 690, 46)


def w09(d):
    globe(d, 260, 690, 100)
    big(d, (400, 690), "195か国", INK, 52, "lm")
    arrow(d, 640, 720, 690)
    glass(d, 830, 610, 140)
    big(d, (920, 690), "0杯", BAD, 64, "lm")


def w10(d):
    dna(d, 230, 690, 210)
    red_face(d, 400, 590, 190)
    arrow(d, 540, 620, 690)
    brain(d, 750, 690, 170)
    big(d, (880, 690), "脳卒中↑", BAD, 50, "lm")


def w11(d):
    label(d, 180, 630, 220, 120, "WHO", (200, 226, 250))
    arrow(d, 440, 520, 690)
    glass(d, 640, 610, 140)
    struck(d, 570, 610, 720, 770)
    big(d, (800, 660), "安全な量は", INK, 40, "lm")
    big(d, (800, 725), "ない", BAD, 60, "lm")


def w12(d):
    flag_jp(d, 230, 690, 150)
    arrow(d, 360, 440, 690)
    warn(d, 560, 690, 150)
    big(d, (680, 650), "少量でも", INK, 44, "lm")
    big(d, (680, 725), "がん↑", BAD, 60, "lm")


def w13(d):
    papers(d, 180, 600, 170)
    arrow(d, 380, 460, 690)
    heart(d, 570, 640, 100)
    big(d, (650, 690), "↓", GOOD, 64, "lm")
    line(d, [(740, 600), (740, 790)], (222, 218, 210), 4)
    big(d, (780, 660), "乳がん", INK, 44, "lm")
    big(d, (780, 730), "↑", BAD, 64, "lm")


def w14(d):
    flag3(d, 220, 690, 130, [(200, 30, 40), (250, 200, 40), (200, 30, 40)], vertical=False)
    glass(d, 410, 610, 140)
    big(d, (500, 690), "尿で確認", INK, 40, "lm")
    arrow(d, 690, 770, 690)
    heart(d, 870, 640, 90)
    big(d, (950, 690), "-50%", GOOD, 52, "lm")


G, B = "g", "b"
# (年, 国, 種類, 見出し[(文字, 色)], データ, 絵, 前, 後, 速報の見出し, 出典)
EVENTS = [
    ("1979", "イギリス", "18か国の比較", [[("ワインを", INK), ("多く飲む国", G), ("ほど", INK)], [("心臓病の死亡が", INK), ("少ない", G)]],
     [("比べた国", "18か国"), ("種類", "国ごとの比較"), ("注意", "国の違いも混ざる")], w01, 50, 53,
     "18か国の比較「ワインの国は心臓病が少ない」", "出典：St Leger, Cochrane & Moore, Lancet 1979"),
    ("1992", "フランス", "研究者の説", [[("フランス人は", INK), ("脂っこいのに", INK)], [("心臓病が", INK), ("少ない", G)]],
     [("名前", "フレンチ・パラドックス"), ("提唱", "セルジュ・ルノー"), ("説", "赤ワインのおかげ")], w02, 53, 56,
     "「フレンチ・パラドックス」の説", "出典：Renaud & de Lorgeril, Lancet 1992"),
    ("1995", "デンマーク", "約1万3千人の追跡調査", [[("ワインを飲む人", G), ("は", INK)], [("死亡リスク", INK), ("-49%", G)]],
     [("対象", "約1万3千人"), ("期間", "10〜12年"), ("ビール", "差なし")], w03, 56, 62,
     "コペンハーゲン「ワインを飲む人は長生き」", "出典：Grønbæk et al., BMJ 1995(Copenhagen City Heart Study)"),
    ("1999", "日本", "40〜59歳男性の追跡調査", [[("少し飲む人", G), ("が", INK)], [("死亡リスク", INK), ("いちばん低い", G)]],
     [("対象", "40〜59歳の男性"), ("期間", "約7年"), ("少し", "週150g未満")], w04, 62, 68,
     "日本の男性「少し飲む人がいちばん長生き」", "出典：Tsugane et al., American Journal of Epidemiology 1999(JPHC研究)"),
    ("2002", "イタリア", "研究のまとめ", [[("ワインを飲む人は", INK)], [("心臓・血管の病気", INK), ("-32%", G)]],
     [("まとめた数", "13の研究"), ("対象", "約21万人"), ("形", "Jの字のカーブ")], w05, 68, 78,
     "研究のまとめ「ワインで-32%」", "出典：Di Castelnuovo et al., Circulation 2002"),
    ("2006", "アメリカ", "マウスの実験", [[("レスベラトロール", G), ("で", INK)], [("マウスが", INK), ("長生き", G)]],
     [("対象", "マウス"), ("食事", "高カロリー"), ("死亡", "-31%")], w06, 78, 81,
     "マウスの実験「赤ワインの成分で長生き」", "出典：Baur et al., Nature 2006"),
    ("2014", "イタリア", "783人の追跡調査", [[("レスベラトロールが", INK), ("多くても", INK)], [("長生きと", INK), ("関係なし", B)]],
     [("対象", "65歳以上783人"), ("場所", "キャンティ地方"), ("期間", "約9年")], w07, 81, 78,
     "ワインの産地で「成分の効果なし」", "出典：Semba et al., JAMA Internal Medicine 2014(InCHIANTI)"),
    ("2016", "カナダ", "研究のまとめ", [[("「やめた人」", INK), ("を分けると", INK)], [("少量の効果は", INK), ("消えた", B)]],
     [("まとめた数", "87の研究"), ("偏りなし", "13の研究だけ"), ("少量", "効果なし")], w08, 78, 68,
     "87の研究「少しなら長生きは見かけ」", "出典：Stockwell et al., Journal of Studies on Alcohol and Drugs 2016"),
    ("2018", "世界", "研究のまとめ", [[("害がいちばん少ない量は", INK)], [("0杯", B)]],
     [("範囲", "195か国"), ("調べた病気", "23種類"), ("心臓", "少し得もある")], w09, 68, 58,
     "195か国の分析「いちばん安全なのは0杯」", "出典：GBD 2016 Alcohol Collaborators, Lancet 2018"),
    ("2019", "中国", "約51万人の追跡調査", [[("遺伝子で調べると", INK)], [("少量でも", INK), ("脳卒中↑", B)]],
     [("対象", "約51万人"), ("遺伝子", "約16万人"), ("方法", "体質のくじ引き")], w10, 58, 52,
     "中国51万人「少量でも守る効果なし」", "出典：Millwood et al., Lancet 2019(China Kadoorie Biobank)"),
    ("2023", "ヨーロッパ", "WHOの公式見解", [[("安全な飲酒量は", INK)], [("ない", B)]],
     [("出した所", "WHO欧州事務局"), ("理由", "がんのリスク"), ("心臓の得", "がんを上回らない")], w11, 52, 37,
     "WHO「安全な飲酒量はない」", "出典：Anderson et al., Lancet Public Health 2023(WHO欧州)"),
    ("2024.2", "日本", "国のガイドライン", [[("少量でも", INK)], [("リスクが上がる病気", B)]],
     [("出した所", "厚生労働省"), ("大腸がん", "1日20g〜"), ("目安", "男40g・女20g")], w12, 37, 22,
     "日本初の飲酒ガイドライン", "出典：厚生労働省「健康に配慮した飲酒に関するガイドライン」(2024年2月)"),
    ("2024.12", "アメリカ", "研究のまとめ", [[("少し飲む人は", INK), ("死亡リスク", INK)], [("低め", G), ("・乳がんは", INK), ("高め", B)]],
     [("出した所", "全米アカデミーズ"), ("確かさ", "中くらい"), ("乳がん", "高め")], w13, 22, 29,
     "全米アカデミーズ「少しなら死亡は低め」", "出典：National Academies, Review of Evidence on Alcohol and Health(2024)"),
    ("2025", "スペイン", "1,232人の調査", [[("グラス半分〜1杯", G), ("の人は", INK)], [("心臓・血管の病気", INK), ("-50%", G)]],
     [("対象", "1,232人"), ("方法", "尿の酒石酸"), ("注意", "心臓病の高リスク者")], w14, 29, 32,
     "スペイン「尿で測ると、ワインで-50%」", "出典：Domínguez-López et al., European Heart Journal 2025(PREDIMED)"),
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
