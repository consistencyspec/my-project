"""一日1万歩の呪縛：研究カードのデータ(EVENTS)と、1万歩の回のピクトグラム(新常識クロニクル 第4回)。

物語版の動画は scripts/steps_story.py で作る(このファイルはデータと絵だけ)。
  python3 scripts/steps_war.py   -> output/steps_war/*.png(全13枚のカードを確認用に書き出す)

必要派(オレンジ)=「一日1万歩は必要(多いほどいい)」/不要派(青)=「1万歩もいらない(7,000〜8,000歩で十分)」。
画面の派の名前は motion.LABELS で「必要派」「不要派」にする(steps_story.py で設定)。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, LW, PANEL, SUB, WHITE, arrow, bean, heart, line, text  # noqa: E402
import coffee_war as cw  # noqa: E402
from coffee_war import big, brain, crowd, foot, label, papers  # noqa: E402
from egg_war import flag_jp  # noqa: E402
from wine_war import flag_dk, globe  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "steps_war")
LEAF = (70, 160, 110)
MOUNT = (120, 170, 120)
SCREEN = (214, 236, 214)
CASE = (250, 214, 90)


# ---------- 1万歩の回のピクトグラム ----------
def pedometer(d, cx, cy, s, num="10000", fill=CASE):
    """昔の万歩計(腰につける小さな箱。窓に歩数)。"""
    w, h = s * 0.8, s
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=s * 0.18, fill=fill, outline=INK, width=LW)
    d.rounded_rectangle([cx - w * 0.36, cy - h * 0.3, cx + w * 0.36, cy + h * 0.02], radius=s * 0.06, fill=SCREEN, outline=INK,
                        width=max(4, LW - 2))
    if num:
        fs = int(min(s * 0.2, s * 0.2 * (w * 0.62) / max(1, d.textlength(num, font=cw.font(int(s * 0.2))))))
        text(d, (cx, cy - h * 0.14), num, fs, INK, anchor="mm")
    text(d, (cx, cy + h * 0.24), "万歩", int(s * 0.17), INK, anchor="mm")
    d.rounded_rectangle([cx - w * 0.18, cy - h / 2 - s * 0.1, cx + w * 0.18, cy - h / 2 + 4], radius=8, fill=SUB, outline=INK, width=5)


def person(d, cx, top, h, fill=None, step=False):
    """スニーカーを履いた人(頭+縦長の胴+腕+足)。step=True で手足を前後に振る(歩いている形)。"""
    hr = h * 0.12
    hy = top + hr
    bw = h * 0.17
    bt, bb = top + 2 * hr + h * 0.03, top + h * 0.64
    foot_y = top + h
    lw = LW + 2
    # 腕(胴の後ろ)
    for side in (-1, 1):
        sx, sy = cx + side * bw * 0.8, bt + h * 0.07
        hx = cx + (side * h * 0.2 if step else side * bw * 1.25)
        hand_y = bt + h * (0.25 if step else 0.27)
        line(d, [(sx, sy), (hx, hand_y)], INK, lw)
        d.ellipse([hx - h * 0.03, hand_y - h * 0.03, hx + h * 0.03, hand_y + h * 0.03], fill=PANEL, outline=INK, width=5)
    # 足とスニーカー(つま先は右向き)
    sw_, sh = h * 0.24, h * 0.1
    for side in (-1, 1):
        hip = (cx + side * bw * 0.45, bb - 8)
        fx = cx + side * (h * 0.17 if step else bw * 0.95)
        line(d, [hip, (fx, foot_y - sh * 0.8)], INK, lw)
        x0 = fx - sw_ * 0.35
        d.rounded_rectangle([x0, foot_y - sh, x0 + sw_, foot_y], radius=sh * 0.45, fill=GOOD, outline=INK, width=6)
        d.rectangle([x0 + 6, foot_y - sh * 0.32, x0 + sw_ - 6, foot_y - 6], fill=WHITE)
        for k in range(2):
            x = x0 + sw_ * (0.3 + k * 0.18)
            d.line([(x, foot_y - sh * 0.85), (x + sh * 0.25, foot_y - sh * 0.55)], fill=WHITE, width=4)
    # 胴と頭
    d.rounded_rectangle([cx - bw, bt, cx + bw, bb], radius=bw * 0.95, outline=INK, width=LW, fill=fill or PANEL)
    d.ellipse([cx - hr, top, cx + hr, top + 2 * hr], outline=INK, width=LW, fill=PANEL)
    line(d, [(cx - h * 0.35, foot_y + 10), (cx + h * 0.35, foot_y + 10)], INK, max(4, LW // 2))


def walker(d, cx, top, h, fill=None):
    """歩いている人(スニーカーを履いた人が足を開く+うしろに動きの線)。"""
    person(d, cx, top, h, fill=fill, step=True)
    for k in range(3):
        y = top + h * (0.5 + k * 0.14)
        line(d, [(cx - h * 0.55 - k * 10, y), (cx - h * 0.42 - k * 10, y)], SUB, 6)


def man_char(d, cx, cy, s):
    """漢字の「万」が歩く人に見える、という話の絵。"""
    text(d, (cx, cy), "万", int(s), INK, anchor="mm")


def calendar(d, cx, cy, s, marks=(1, 4)):
    """1週間のカレンダー。marks の曜日に色をつける。"""
    x0, y0 = cx - s * 0.7, cy - s * 0.45
    cell = s * 1.4 / 7
    d.rounded_rectangle([x0, y0, x0 + s * 1.4, y0 + s * 0.9], radius=14, fill=WHITE, outline=INK, width=LW)
    d.rectangle([x0 + 4, y0 + 4, x0 + s * 1.4 - 4, y0 + s * 0.25], fill=(220, 70, 70))
    for i in range(7):
        x = x0 + cell * (i + 0.5)
        y = y0 + s * 0.58
        r = cell * 0.32
        d.ellipse([x - r, y - r, x + r, y + r], fill=GOOD if i in marks else (232, 228, 220), outline=INK, width=4)


def curve(d, x0, y0, w, h, kind="plateau", color=GOOD):
    """歩数(横)と効果(縦)のグラフ。plateau=途中で頭打ち、rise=ずっと上がる。"""
    line(d, [(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], INK, 6)
    pts = []
    for i in range(41):
        t = i / 40
        v = (1 - math.exp(-4.2 * t)) if kind == "plateau" else (0.15 + 0.85 * t ** 0.8)
        pts.append((x0 + 10 + t * (w - 20), y0 + h - 10 - v * (h - 30)))
    d.line(pts, fill=color, width=LW, joint="curve")


def town(d, cx, cy, s):
    """山あいの町(群馬県中之条町)。"""
    d.polygon([(cx - s * 0.7, cy + s * 0.25), (cx - s * 0.25, cy - s * 0.35), (cx + s * 0.15, cy + s * 0.25)], fill=MOUNT,
              outline=INK)
    d.polygon([(cx - s * 0.1, cy + s * 0.25), (cx + s * 0.3, cy - s * 0.2), (cx + s * 0.7, cy + s * 0.25)], fill=(150, 195, 140),
              outline=INK)
    for dx in (-0.4, 0.0, 0.4):
        x = cx + dx * s
        d.rectangle([x - s * 0.1, cy + s * 0.1, x + s * 0.1, cy + s * 0.35], fill=WHITE, outline=INK, width=5)
        d.polygon([(x - s * 0.14, cy + s * 0.12), (x, cy - s * 0.02), (x + s * 0.14, cy + s * 0.12)], fill=(220, 70, 70), outline=INK)
    line(d, [(cx - s * 0.75, cy + s * 0.36), (cx + s * 0.75, cy + s * 0.36)], INK, 6)


def flag_h3(d, cx, cy, s, cols):
    """横3色の旗(オランダなど)。"""
    x0, y0, x1, y1 = cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4
    for i, c in enumerate(cols):
        d.rectangle([x0, y0 + (y1 - y0) * i / len(cols), x1, y0 + (y1 - y0) * (i + 1) / len(cols)], fill=c)
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=INK, width=6)


def flag_pl(d, cx, cy, s):
    flag_h3(d, cx, cy, s, [WHITE, (220, 30, 60)])


def flag_nl(d, cx, cy, s):
    flag_h3(d, cx, cy, s, [(200, 30, 50), WHITE, (30, 70, 150)])


def flag_au(d, cx, cy, s):
    x0, y0, x1, y1 = cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4
    d.rectangle([x0, y0, x1, y1], fill=(20, 40, 120))
    for px, py, r in ((0.3, 0.15, 0.07), (0.4, -0.15, 0.05), (0.15, -0.05, 0.05), (-0.3, 0.2, 0.09)):
        x, y = cx + px * s, cy + py * s
        d.ellipse([x - r * s, y - r * s, x + r * s, y + r * s], fill=WHITE)
    d.rectangle([x0, y0, cx, cy], fill=(20, 40, 120))
    d.rectangle([x0, (y0 + cy) / 2 - s * 0.04, cx, (y0 + cy) / 2 + s * 0.04], fill=WHITE)
    d.rectangle([(x0 + cx) / 2 - s * 0.04, y0, (x0 + cx) / 2 + s * 0.04, cy], fill=WHITE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=INK, width=6)


def shoe(d, cx, cy, s, fill=GOOD):
    """スニーカー(横向き)。"""
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.05, cx + s * 0.5, cy + s * 0.22], radius=s * 0.1, fill=WHITE, outline=INK, width=LW)
    d.pieslice([cx - s * 0.5, cy - s * 0.45, cx + s * 0.25, cy + s * 0.3], 180, 360, fill=fill, outline=INK, width=LW)
    d.rounded_rectangle([cx - s * 0.1, cy - s * 0.12, cx + s * 0.5, cy + s * 0.06], radius=s * 0.08, fill=fill, outline=INK, width=LW)
    for k in range(3):
        x = cx - s * 0.28 + k * s * 0.12
        line(d, [(x, cy - s * 0.3), (x + s * 0.06, cy - s * 0.2)], WHITE, 6)


# ---------- 各研究のピクトグラム(カードの中、x 150〜1080 / y 580〜800) ----------
def s01(d):
    flag_jp(d, 230, 690, 150)
    pedometer(d, 450, 700, 190)
    arrow(d, 580, 660, 690)
    big(d, (700, 650), "一日1万歩", GOOD, 52, "lm")
    big(d, (700, 730), "が合言葉に", INK, 40, "lm")


def s02(d):
    papers(d, 180, 600, 170)
    arrow(d, 380, 460, 690)
    for i, (n, c) in enumerate((("5千歩未満", BAD), ("1万歩以上", GOOD))):
        y = 640 + i * 95
        d.rounded_rectangle([500, y - 38, 1060, y + 38], radius=38, fill=(240, 236, 228))
        text(d, (530, y), n, 40, c, anchor="lm")
        text(d, (1040, y), "座りがち" if i == 0 else "活動的", 40, INK, anchor="rm")


def s03(d):
    papers(d, 180, 600, 170)
    pedometer(d, 480, 700, 170)
    arrow(d, 600, 680, 690)
    big(d, (720, 650), "歩数↑", GOOD, 56, "lm")
    big(d, (720, 735), "血圧↓", GOOD, 56, "lm")


def s04(d):
    flag_jp(d, 220, 690, 130)
    town(d, 430, 690, 240)
    big(d, (640, 650), "8,000歩", BAD, 60, "lm")
    big(d, (640, 735), "+速歩き20分", INK, 44, "lm")


def s05(d):
    crowd(d, 170, 600, 3, 2, 100)
    curve(d, 470, 600, 300, 190, "plateau", BAD)
    text(d, (620, 805), "歩数→", 26, SUB, heavy=False, anchor="mm")
    big(d, (810, 650), "7,500歩で", INK, 44, "lm")
    big(d, (810, 730), "頭打ち", BAD, 56, "lm")


def s06(d):
    walker(d, 260, 590, 190, fill=(255, 226, 196))
    arrow(d, 400, 480, 690)
    big(d, (520, 650), "8,000歩", INK, 48, "lm")
    big(d, (520, 730), "-51%", GOOD, 60, "lm")
    line(d, [(770, 600), (770, 790)], (222, 218, 210), 4)
    big(d, (800, 650), "1万2千歩", INK, 44, "lm")
    big(d, (800, 730), "-65%", GOOD, 60, "lm")


def s07(d):
    globe(d, 240, 690, 90)
    big(d, (360, 690), "15の調査", INK, 44, "lm")
    curve(d, 600, 600, 260, 190, "plateau", BAD)
    big(d, (890, 650), "60歳〜", INK, 36, "lm")
    big(d, (890, 730), "頭打ち", BAD, 50, "lm")


def s08(d):
    flag_dk(d, 220, 690, 130)
    brain(d, 440, 690, 170)
    arrow(d, 560, 640, 690)
    big(d, (680, 650), "約1万歩で", INK, 44, "lm")
    big(d, (680, 735), "認知症 -51%", GOOD, 56, "lm")


def s09(d):
    flag_jp(d, 220, 690, 130)
    calendar(d, 470, 690, 210)
    arrow(d, 640, 720, 690)
    big(d, (760, 650), "週1〜2日でも", INK, 40, "lm")
    big(d, (760, 735), "死亡↓", BAD, 56, "lm")


def s10(d):
    flag_pl(d, 220, 690, 130)
    curve(d, 340, 600, 280, 190, "rise", GOOD)
    big(d, (660, 650), "2万歩まで", INK, 44, "lm")
    big(d, (660, 735), "上限なし", GOOD, 60, "lm")


def s11(d):
    flag_nl(d, 220, 690, 130)
    curve(d, 340, 600, 280, 190, "plateau", BAD)
    big(d, (660, 650), "いちばんは", INK, 40, "lm")
    big(d, (660, 735), "約8,700歩", BAD, 60, "lm")


def s12(d):
    flag_jp(d, 220, 690, 130)
    label(d, 310, 630, 270, 120, "厚生労働省", (200, 226, 250))
    big(d, (620, 650), "大人 8,000歩", BAD, 50, "lm")
    big(d, (620, 735), "高齢者 6,000歩", BAD, 50, "lm")


def s13(d):
    flag_au(d, 220, 690, 130)
    papers(d, 340, 600, 170)
    big(d, (560, 650), "7,000歩で", INK, 44, "lm")
    big(d, (560, 735), "死亡 -47%", BAD, 56, "lm")
    foot(d, 990, 690, 120)


G, B = "g", "b"
# (年, 国, 種類, 見出し[(文字, 色)], データ, 絵, 前, 後, 速報の見出し, 出典)
EVENTS = [
    ("1965", "日本", "商品の発売", [[("「万歩計」", G), ("発売", INK)], [("一日1万歩", G), ("が合言葉に", INK)]],
     [("発売", "山佐時計計器"), ("名前", "万歩計"), ("根拠", "研究ではない")], s01, 50, 53,
     "「万歩計」発売「一日1万歩歩こう」", "出典：山佐時計計器「万歩計」(1965年)/Tudor-Locke & Bassett, Sports Med 2004"),
    ("2004", "アメリカ", "研究のまとめ", [[("1万歩は", INK)], [("健康な大人の", INK), ("目安", G)]],
     [("5千歩未満", "座りがち"), ("1万歩以上", "活動的"), ("注意", "高齢者には多いことも")], s02, 53, 63,
     "研究のまとめ「1万歩は大人の目安」", "出典：Tudor-Locke & Bassett, Sports Medicine 2004"),
    ("2007", "アメリカ", "研究のまとめ", [[("目標", INK), ("1万歩", G), ("で", INK)], [("歩数が増え", G), ("血圧も下がる", G)]],
     [("まとめた数", "26の研究"), ("歩数", "1日 約2,500歩増"), ("血圧", "-3.8")], s03, 63, 73,
     "26の研究「歩数計と目標で、歩数も血圧も改善」", "出典：Bravata et al., JAMA 2007"),
    ("2010", "日本", "約5,000人の追跡調査", [[("8,000歩", B), ("で", INK)], [("病気の予防は", INK), ("十分", B)]],
     [("対象", "中之条町の高齢者"), ("始まり", "2000年〜"), ("条件", "うち20分は速歩き")], s04, 73, 67,
     "中之条研究「8,000歩・速歩き20分」", "出典：Aoyagi & Shephard, Geriatrics & Gerontology International 2010(中之条研究)"),
    ("2019", "アメリカ", "約1万7千人の追跡調査", [[("約4,400歩", B), ("でも", INK)], [("死亡リスク", INK), ("-41%", B)]],
     [("対象", "高齢の女性"), ("平均", "72歳"), ("頭打ち", "約7,500歩")], s05, 67, 61,
     "1万歩の出どころは宣伝「7,500歩で頭打ち」", "出典：Lee et al., JAMA Internal Medicine 2019(Women's Health Study)"),
    ("2020", "アメリカ", "4,840人の追跡調査", [[("8,000歩", G), ("で", INK)], [("死亡リスク", INK), ("-51%", G)]],
     [("対象", "40歳以上4,840人"), ("比べた相手", "4,000歩の人"), ("1万2千歩", "-65%")], s06, 61, 64,
     "アメリカ「歩くほど死亡が減る」", "出典：Saint-Maurice et al., JAMA 2020"),
    ("2022.3", "世界", "研究のまとめ", [[("60歳以上は", INK)], [("6,000〜8,000歩", B), ("で頭打ち", INK)]],
     [("まとめた数", "15の調査"), ("対象", "約4万7千人"), ("60歳未満", "8,000〜1万歩")], s07, 64, 54,
     "15の調査「60歳以上は6,000〜8,000歩で頭打ち」", "出典：Paluch et al., Lancet Public Health 2022"),
    ("2022.9", "デンマーク", "約7万8千人の追跡調査", [[("約1万歩", G), ("まで", INK)], [("歩くほど", INK), ("認知症↓", G)]],
     [("対象", "イギリスの約7万8千人"), ("約1万歩", "-51%"), ("3,800歩", "-25%")], s08, 54, 60,
     "約7万8千人「1万歩近くで認知症が半分」", "出典：del Pozo Cruz et al., JAMA Neurology 2022(UK Biobank)"),
    ("2023.3", "日本", "3,101人の追跡調査", [[("8,000歩", B), ("は", INK)], [("週1〜2日", B), ("でも効果", INK)]],
     [("研究", "京都大学など"), ("対象", "アメリカの3,101人"), ("10年の死亡", "約15ポイント↓")], s09, 60, 57,
     "京都大学など「8,000歩は週1〜2日でも」", "出典：Inoue et al., JAMA Network Open 2023"),
    ("2023.8", "ポーランド", "研究のまとめ", [[("歩くほど", INK), ("死亡↓", G)], [("2万歩まで", INK), ("上限なし", G)]],
     [("まとめた数", "17の研究"), ("対象", "約23万人"), ("1,000歩ごと", "死亡 -15%")], s10, 57, 67,
     "22万人の分析「2万歩まで、歩くほどいい」", "出典：Banach et al., European Journal of Preventive Cardiology 2023"),
    ("2023.10", "オランダ", "研究のまとめ", [[("効果がいちばん大きいのは", INK)], [("約8,700歩", B)]],
     [("まとめた数", "12の研究"), ("対象", "約11万人"), ("心臓・血管", "約7,100歩")], s11, 67, 57,
     "オランダ「ちょうどいいのは約8,700歩」", "出典：Stens et al., Journal of the American College of Cardiology 2023"),
    ("2024.1", "日本", "国のガイド", [[("大人は", INK), ("8,000歩", B)], [("高齢者は", INK), ("6,000歩", B)]],
     [("出した所", "厚生労働省"), ("大人", "約8,000歩以上"), ("高齢者", "約6,000歩以上")], s12, 57, 42,
     "国のガイド「大人8,000歩・高齢者6,000歩」", "出典：厚生労働省「健康づくりのための身体活動・運動ガイド2023」(2024年1月)"),
    ("2025", "オーストラリア", "研究のまとめ", [[("7,000歩", B), ("で", INK)], [("死亡リスク", INK), ("-47%", B)]],
     [("まとめた数", "57の研究"), ("比べた相手", "2,000歩の人"), ("1万歩", "さらに少し得")], s13, 42, 35,
     "57の研究「7,000歩でかなりの効果」", "出典：Ding et al., Lancet Public Health 2025"),
]


def main():
    import motion
    motion.LABELS[:] = ["必要派", "不要派"]
    from motion import Card
    os.makedirs(OUT, exist_ok=True)
    for i, (year, country, kind, title, facts, picto, before, after, _, source) in enumerate(EVENTS, 1):
        rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
        diff = after - before
        card = Card(year, country, kind, rows, facts, picto, before, after,
                    f"{'必要派' if diff > 0 else '不要派'} +{abs(diff)}議席", source)
        path = os.path.join(OUT, f"{i:02d}_{year.replace('.', '_')}.png")
        card.frame(Card.ANIM_END).save(path)
        print(path)


if __name__ == "__main__":
    sys.exit(main())
