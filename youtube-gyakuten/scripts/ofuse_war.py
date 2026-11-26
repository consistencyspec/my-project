"""【ボツネタ・2026-11-26 公開しないと決定】お布施はいくら？：出来事カードのデータ(EVENTS)と、お布施の回のピクトグラム(新常識クロニクル お布施編)。

この回の2つの派:お気持ち派(オレンジ・左)=金額は決めず気持ちで/定額派(青・右)=金額をはっきり示すべき。
物語版の動画は scripts/ofuse_story.py で作る(このファイルはデータと絵だけ)。
  python3 scripts/ofuse_war.py   -> output/ofuse_war/*.png(全カードを確認用に書き出す)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames  # noqa: E402
from frames import BAD, GOOD, INK, LW, PANEL, SUB, WHITE, arrow, bean, line, text  # noqa: E402
import coffee_war as cw  # noqa: E402
from coffee_war import big, crowd, label, papers  # noqa: E402

frames.LBL[:] = ["お気持ち派", "定額派"]   # 議席の左右の名前(この回だけ)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "ofuse_war")
ROBE = (150, 140, 170)
KESA = (235, 175, 70)
ROOF = (90, 96, 110)
WOOD = (190, 120, 70)
BILL = (214, 232, 214)
GRAY = (150, 156, 170)


# ---------- お布施の回のピクトグラム ----------
def envelope(d, cx, cy, h, label_text="御布施"):
    """白い封筒(縦書きで「御布施」)。"""
    w = h * 0.56
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=10, fill=WHITE, outline=INK, width=LW)
    fs = int(h * 0.17)
    n = len(label_text)
    for i, ch in enumerate(label_text):
        text(d, (cx, cy - h * 0.3 + i * fs * 1.08 + (3 - n) * fs * 0.5), ch, fs, INK, anchor="ma")


def monk(d, cx, top, h, fill=ROBE):
    """お坊さん(丸い頭+衣+袈裟の帯)。"""
    bean(d, cx, top, h, fill=fill)
    hr = h * 0.17
    bw = h * 0.36
    bt = top + 2 * hr + h * 0.06
    # 胸の絡子(らくす):首からひもで下げる四角い布
    d.line([(cx - bw * 0.3, bt + h * 0.02), (cx - bw * 0.22, bt + h * 0.2)], fill=KESA, width=max(4, int(h * 0.025)))
    d.line([(cx + bw * 0.3, bt + h * 0.02), (cx + bw * 0.22, bt + h * 0.2)], fill=KESA, width=max(4, int(h * 0.025)))
    d.rounded_rectangle([cx - bw * 0.32, bt + h * 0.18, cx + bw * 0.32, bt + h * 0.38], radius=6, fill=KESA,
                        outline=INK, width=max(3, int(h * 0.018)))


def temple(d, cx, cy, s):
    """お寺(屋根+柱)。"""
    d.polygon([(cx - s * 0.62, cy - s * 0.12), (cx - s * 0.4, cy - s * 0.42), (cx + s * 0.4, cy - s * 0.42),
               (cx + s * 0.62, cy - s * 0.12)], fill=ROOF, outline=INK)
    d.line([(cx - s * 0.62, cy - s * 0.12), (cx - s * 0.4, cy - s * 0.42), (cx + s * 0.4, cy - s * 0.42),
            (cx + s * 0.62, cy - s * 0.12), (cx - s * 0.62, cy - s * 0.12)], fill=INK, width=LW, joint="curve")
    d.rounded_rectangle([cx - s * 0.46, cy - s * 0.12, cx + s * 0.46, cy + s * 0.38], radius=6, fill=PANEL, outline=INK, width=LW)
    for k in (-0.3, 0, 0.3):
        d.line([(cx + k * s, cy - s * 0.1), (cx + k * s, cy + s * 0.36)], fill=WOOD, width=max(6, int(s * 0.05)))
    d.rectangle([cx - s * 0.56, cy + s * 0.38, cx + s * 0.56, cy + s * 0.46], fill=INK)


def bill(d, cx, cy, s, n=3):
    """お札の束(¥)。"""
    for k in range(n - 1, -1, -1):
        ox, oy = k * s * 0.08, -k * s * 0.08
        d.rounded_rectangle([cx - s * 0.5 + ox, cy - s * 0.26 + oy, cx + s * 0.5 + ox, cy + s * 0.26 + oy], radius=10,
                            fill=BILL, outline=INK, width=6)
    d.ellipse([cx - s * 0.15, cy - s * 0.15, cx + s * 0.15, cy + s * 0.15], outline=INK, width=5)
    text(d, (cx, cy), "¥", int(s * 0.22), INK, anchor="mm")


def price_tag(d, cx, cy, s, msg, color=BAD):
    """値札。"""
    w = max(s, d.textlength(msg, font=frames.font(int(s * 0.3))) + s * 0.5)
    pts = [(cx - w / 2, cy - s * 0.28), (cx + w / 2 - s * 0.2, cy - s * 0.28), (cx + w / 2, cy),
           (cx + w / 2 - s * 0.2, cy + s * 0.28), (cx - w / 2, cy + s * 0.28)]
    d.polygon(pts, fill=color)
    d.ellipse([cx + w / 2 - s * 0.27, cy - s * 0.06, cx + w / 2 - s * 0.15, cy + s * 0.06], fill=WHITE)
    text(d, (cx - s * 0.08, cy), msg, int(s * 0.3), WHITE, anchor="mm")


def cart(d, cx, cy, s):
    """買い物かご(通販)。"""
    d.line([(cx - s * 0.55, cy - s * 0.35), (cx - s * 0.4, cy - s * 0.35), (cx - s * 0.25, cy + s * 0.2),
            (cx + s * 0.4, cy + s * 0.2), (cx + s * 0.5, cy - s * 0.2), (cx - s * 0.33, cy - s * 0.2)],
           fill=INK, width=LW, joint="curve")
    for x in (cx - s * 0.18, cx + s * 0.32):
        d.ellipse([x - s * 0.07, cy + s * 0.28, x + s * 0.07, cy + s * 0.42], fill=INK)


def question(d, cx, top, h):
    """首をかしげる人(?マーク)。"""
    bean(d, cx, top, h, fill=(214, 228, 250))
    text(d, (cx + h * 0.42, top + h * 0.05), "？", int(h * 0.4), BAD, anchor="mt")


def ballot(d, cx, cy, s):
    """投票箱。"""
    d.rounded_rectangle([cx - s * 0.45, cy - s * 0.15, cx + s * 0.45, cy + s * 0.45], radius=12, fill=PANEL, outline=INK, width=LW)
    d.rounded_rectangle([cx - s * 0.25, cy - s * 0.2, cx + s * 0.25, cy - s * 0.1], radius=4, fill=INK)
    d.rounded_rectangle([cx - s * 0.18, cy - s * 0.55, cx + s * 0.18, cy - s * 0.12], radius=6, fill=WHITE, outline=INK, width=6)
    line(d, [(cx - s * 0.08, cy - s * 0.35), (cx - s * 0.01, cy - s * 0.27), (cx + s * 0.1, cy - s * 0.45)], BAD, 6)


def bars(d, x0, base_y, items, maxv, h, bw=110, gap=70, unit="万円"):
    """棒グラフ。items=[(ラベル, 値, 色)]。"""
    for i, (lab, v, c) in enumerate(items):
        x = x0 + i * (bw + gap)
        top = base_y - h * v / maxv
        d.rounded_rectangle([x, top, x + bw, base_y], radius=14, fill=c, outline=INK, width=6)
        text(d, (x + bw / 2, top - 12), f"{v:g}{unit}", 40, INK, anchor="mb")
        text(d, (x + bw / 2, base_y + 14), lab, 34, SUB, heavy=False, anchor="ma")
    d.line([(x0 - 30, base_y), (x0 + len(items) * (bw + gap) - gap + 30, base_y)], fill=INK, width=5)


# ---------- 各カードのピクトグラム(カードの中、x 150〜1080 / y 580〜800) ----------
def o01(d):
    cart(d, 260, 690, 200)
    monk(d, 470, 585, 200)
    arrow(d, 600, 680, 690)
    price_tag(d, 880, 690, 150, "3万5千円")


def o02(d):
    temple(d, 270, 690, 230)
    envelope(d, 520, 690, 200)
    big(d, (640, 650), "値段を", INK, 44, "lm")
    big(d, (640, 730), "つけないで", GOOD, 50, "lm")


def o03(d):
    temple(d, 260, 690, 210)
    big(d, (420, 650), "山形・福井・山梨", INK, 44, "lm")
    big(d, (420, 730), "奈良・大分", GOOD, 50, "lm")


def o04(d):
    big(d, (170, 640), "葬儀の総額", SUB, 36, "lm")
    big(d, (170, 715), "178万→111万円", INK, 52, "lm")
    big(d, (170, 780), "約67万円ダウン", INK, 36, "lm")
    line(d, [(610, 600), (610, 800)], (222, 218, 210), 4)
    big(d, (650, 640), "お布施", SUB, 36, "lm")
    big(d, (650, 715), "23.7万→22.4万円", BAD, 50, "lm")
    big(d, (650, 780), "ほぼ横ばい", BAD, 36, "lm")


def o05(d):
    temple(d, 250, 690, 200)
    question(d, 470, 590, 190)
    big(d, (620, 650), "金額が分からない", INK, 40, "lm")
    big(d, (620, 730), "64.9%", BAD, 60, "lm")


def o06(d):
    ballot(d, 250, 700, 220)
    big(d, (420, 650), "幅を持たせて明示", BAD, 44, "lm")
    big(d, (420, 730), "47.5%", BAD, 60, "lm")


def o07(d):
    crowd(d, 180, 600, 3, 2, 100)
    big(d, (520, 650), "明示に賛成", INK, 44, "lm")
    big(d, (520, 730), "68.7%", BAD, 64, "lm")
    big(d, (820, 730), "反対 11.1%", GOOD, 40, "lm")


def o08(d):
    for k in range(3):
        monk(d, 210 + k * 115, 595, 170)
    big(d, (600, 620), "賛成 26.6%", BAD, 40, "lm")
    big(d, (600, 690), "反対 33.0%", GOOD, 40, "lm")
    big(d, (600, 760), "どちらでもない 40.4%", SUB, 36, "lm")


G, B = "g", "b"
# (年, 国, 種類, 見出し[(文字, 色)], データ, 絵, 前, 後, 速報の見出し, 出典)   前・後=お気持ち派の議席
EVENTS = [
    ("2015.12", "日本", "大手の新サービス", [[("Amazonに", INK), ("定額の", B)], [("「お坊さん便」", B), ("登場", INK)]],
     [("価格", "3万5千円(税込)"), ("内容", "法事・法要の読経"), ("お墓の前", "+1万円")], o01, 50, 35,
     "Amazonに定額の「お坊さん便」", "出典：ネットショップ担当者フォーラム(2015年12月)、J-CAST ニュース(2016年3月8日)"),
    ("2016.3", "日本", "団体の声明", [[("お布施は", INK)], [("サービスの対価", G), ("ではない", G)]],
     [("出した所", "全日本仏教会"), ("求めたこと", "販売の取りやめ"), ("心配", "宗教性・課税")], o02, 35, 50,
     "全日本仏教会がAmazonに抗議", "出典：J-CAST ニュース(2016年3月8日)、婦人公論(Yahoo!ニュース)"),
    ("2017", "日本", "全国調査(地域の結果)", [[("しきたりを重視", G), ("する", INK)], [("地域も残る", INK)]],
     [("ベスト5", "山形・福井など"), ("家族葬", "約4割"), ("回答", "1,999件")], o03, 50, 53,
     "しきたりを重視する地域ベスト5", "出典：鎌倉新書「第3回お葬式に関する全国調査」(2017年)"),
    ("2022", "日本", "全国調査", [[("葬儀は", INK), ("安く", INK), ("なったのに", INK)], [("お布施は", INK), ("横ばい", B)]],
     [("葬儀の総額", "110.7万円"), ("お布施", "22.4万円"), ("家族葬", "55.7%")], o04, 53, 43,
     "葬儀は安くなったのに、お布施は下がらない", "出典：鎌倉新書「第4回・第5回お葬式に関する全国調査」(2020年・2022年)"),
    ("2022", "日本", "意識調査", [[("お布施の金額が", INK)], [("分からない", B), ("64.9%", B)]],
     [("調べた所", "全日本仏教会"), ("明示が必要", "53.5%"), ("種類", "意識調査")], o05, 43, 37,
     "仏教会の調査でも「金額が分からない」", "出典：全日本仏教会の調査(2022年。ben54 ほかの報道による)"),
    ("2024.2", "日本", "ネット投票", [[("「幅を持たせて明示」", B)], [("がいちばん多い", INK)]],
     [("賛成", "30.5%"), ("幅を持たせて", "47.5%"), ("反対", "16.9%")], o06, 37, 34,
     "ネット投票「幅を持たせて明示」が最多", "出典：Surfvote「お布施の金額は、明示すべきか？」(2023年11月〜2024年1月、59票)"),
    ("2024.11", "日本", "約200人の意識調査", [[("一般の人は", INK)], [("明示に賛成", B), ("68.7%", B)]],
     [("対象", "一般の人208人"), ("反対", "11.1%"), ("調べた所", "Zoom安居")], o07, 34, 28,
     "一般の人「金額の明示に賛成」が約7割", "出典：鵜飼秀徳「お布施、50万円以上が1割も！」JBpress(2024年11月5日)"),
    ("2024.11", "日本", "約200人の意識調査", [[("お坊さんは", INK)], [("反対", G), ("がやや多い", INK)]],
     [("対象", "僧侶203人"), ("どちらでもない", "40.4%"), ("調べた所", "Zoom安居")], o08, 28, 31,
     "お坊さんは「反対」がやや多く、意見が割れる", "出典：鵜飼秀徳「お布施、50万円以上が1割も！」JBpress(2024年11月5日)"),
]


def delta_label(before, after):
    return f"{frames.LBL[0] if after > before else frames.LBL[1]} +{abs(after - before)}議席"


def main():
    from motion import Card
    os.makedirs(OUT, exist_ok=True)
    for i, (year, country, kind, title, facts, picto, before, after, _, source) in enumerate(EVENTS, 1):
        rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
        card = Card(year, country, kind, rows, facts, picto, before, after, delta_label(before, after), source)
        path = os.path.join(OUT, f"{i:02d}_{year.replace('.', '_')}.png")
        card.frame(Card.ANIM_END).save(path)
        print(path)


if __name__ == "__main__":
    sys.exit(main())
