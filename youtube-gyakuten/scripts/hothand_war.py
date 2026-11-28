"""よく当たる売り場は本当？：研究カードのデータ(EVENTS)・ピクトグラム・確認用スライド(新常識クロニクル ホットハンド編)。

この回の2つの派:流れ派(オレンジ・左)=流れやツキは本当にあり、乗った人が得をする
                確率派(青・右)=偶然は偶然。流れに乗っても得はしない
入り口は年末ジャンボの「よく当たる売り場」。裏の理論は「ホットハンド」。
宝くじ・カジノ・スポーツ・投資の作戦を、研究ごとに判定する。

  .venv/bin/python scripts/hothand_war.py   -> output/hothand_war/slides/*.png と一覧 contact_sheet.png
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames  # noqa: E402
from frames import (BAD, GOOD, INK, LW, PANEL, SUB, TRIM, WHITE, H, W, arrow, bean, font, line,  # noqa: E402
                    panel, parliament, stage, study_card, text)
from thumbnail import series_card, thumbnail  # noqa: E402

frames.LBL[:] = ["流れ派", "確率派"]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "hothand_war", "slides")
TITLE = "よく当たる売り場は本当？"
SUBTITLE = "「流れ派」vs「確率派」勝負の行方"
RED = (205, 50, 50)
GOLD = (236, 190, 70)
BALL = (232, 120, 40)
GREEN = (40, 140, 90)


# ---------- ピクトグラム ----------
def ticket(d, cx, cy, s, color=(255, 236, 214)):
    w, h = s, s * 0.5
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=14, fill=color, outline=INK, width=LW)
    d.line([(cx + w * 0.22, cy - h / 2 + 10), (cx + w * 0.22, cy + h / 2 - 10)], fill=SUB, width=4)
    text(d, (cx - w * 0.14, cy - h * 0.12), "宝くじ", int(s * 0.16), RED, anchor="mm")
    text(d, (cx - w * 0.14, cy + h * 0.2), "1等", int(s * 0.11), INK, anchor="mm")
    text(d, (cx + w * 0.36, cy), "¥", int(s * 0.2), GOLD, anchor="mm")


def shop(d, cx, cy, s, banner="1等出ました"):
    w = s
    d.rectangle([cx - w / 2, cy - s * 0.25, cx + w / 2, cy + s * 0.4], fill=PANEL, outline=INK, width=LW)
    for i in range(6):  # 日よけ
        x0 = cx - w / 2 + i * w / 6
        d.rectangle([x0, cy - s * 0.42, x0 + w / 6, cy - s * 0.25], fill=RED if i % 2 == 0 else WHITE)
    d.rectangle([cx - w / 2, cy - s * 0.42, cx + w / 2, cy - s * 0.25], outline=INK, width=LW)
    d.rectangle([cx - w * 0.3, cy - s * 0.12, cx + w * 0.3, cy + s * 0.1], fill=(220, 236, 250), outline=INK, width=6)
    d.rounded_rectangle([cx - w * 0.46, cy + s * 0.15, cx + w * 0.46, cy + s * 0.33], radius=8, fill=GOLD)
    text(d, (cx, cy + s * 0.24), banner, int(s * 0.12), INK, anchor="mm")


def queue(d, x0, top, n, h, fill=None):
    for i in range(n):
        bean(d, x0 + i * h * 0.55, top, h, fill=fill, w=5)


def roulette(d, cx, cy, r):
    n = 18
    for k in range(n):
        a0, a1 = 360 * k / n, 360 * (k + 1) / n
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=RED if k % 2 else INK)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 0, 360 / n, fill=GREEN)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(150, 100, 50), width=LW + 4)
    d.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=(190, 140, 80), outline=INK, width=6)
    d.ellipse([cx + r * 0.62, cy - r * 0.2, cx + r * 0.78, cy - r * 0.04], fill=WHITE, outline=INK, width=3)


def board(d, x, y, nums):
    """直前に出た数字の電光板。"""
    w, h = 150, 66 * len(nums) + 30
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=INK)
    for i, (n, c) in enumerate(nums):
        text(d, (x + w / 2, y + 48 + i * 66), str(n), 46, c, anchor="mm")


def basketball(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BALL, outline=INK, width=LW)
    d.line([(cx - r, cy), (cx + r, cy)], fill=INK, width=6)
    d.line([(cx, cy - r), (cx, cy + r)], fill=INK, width=6)
    d.arc([cx - r * 1.5, cy - r, cx - r * 0.3, cy + r], -60, 60, fill=INK, width=6)
    d.arc([cx + r * 0.3, cy - r, cx + r * 1.5, cy + r], 120, 240, fill=INK, width=6)


def volleyball(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=LW)
    d.arc([cx - r * 0.9, cy - r * 1.6, cx + r * 1.4, cy + r * 0.2], 90, 200, fill=BAD, width=8)
    d.arc([cx - r * 1.4, cy - r * 0.2, cx + r * 0.9, cy + r * 1.6], 270, 20, fill=GOLD, width=8)
    d.arc([cx - r * 0.2, cy - r * 0.6, cx + r * 1.8, cy + r * 1.4], 150, 250, fill=INK, width=6)


def baseball(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=LW)
    d.arc([cx - r * 1.6, cy - r, cx - r * 0.4, cy + r], -55, 55, fill=RED, width=6)
    d.arc([cx + r * 0.4, cy - r, cx + r * 1.6, cy + r], 125, 235, fill=RED, width=6)


URA = (92, 104, 128)        # 裏=濃い灰青(表=金と見分けやすく)
DIM_OMOTE = (246, 228, 180)  # 数えない回は薄く
DIM_URA = (196, 202, 214)


def coin(d, cx, cy, r, face="表", counted=None):
    """表=金に黒文字/裏=灰青に白文字。counted=True で「数える回」のオレンジの輪、False で薄く表示。"""
    omote = face == "表"
    if counted is False:
        fill, ink, edge = (DIM_OMOTE if omote else DIM_URA), (170, 170, 180) if omote else WHITE, (200, 200, 210)
    else:
        fill, ink, edge = (GOLD if omote else URA), (INK if omote else WHITE), INK
    if counted:
        d.ellipse([cx - r - 9, cy - r - 9, cx + r + 9, cy + r + 9], outline=GOOD, width=7)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=edge, width=max(3, int(r * 0.12)))
    text(d, (cx, cy), face, int(r * 1.0), ink, anchor="mm")


def fire(d, cx, cy, s):
    d.polygon([(cx, cy - s), (cx + s * 0.55, cy - s * 0.1), (cx + s * 0.4, cy + s * 0.5), (cx - s * 0.4, cy + s * 0.5),
               (cx - s * 0.55, cy - s * 0.1)], fill=(240, 90, 40))
    d.polygon([(cx, cy - s * 0.45), (cx + s * 0.28, cy + s * 0.05), (cx + s * 0.2, cy + s * 0.45),
               (cx - s * 0.2, cy + s * 0.45), (cx - s * 0.28, cy + s * 0.05)], fill=(255, 210, 80))


def chart(d, x, y, w, h, pts, color=GOOD):
    d.line([(x, y), (x, y + h), (x + w, y + h)], fill=INK, width=6)
    xy = [(x + 20 + i * (w - 40) / (len(pts) - 1), y + h - 20 - p * (h - 40)) for i, p in enumerate(pts)]
    d.line(xy, fill=color, width=10, joint="curve")
    for px, py in xy:
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=color)


def big_x(d, cx, cy, s, color=BAD):
    line(d, [(cx - s, cy - s), (cx + s, cy + s)], color, 16)
    line(d, [(cx - s, cy + s), (cx + s, cy - s)], color, 16)


def eq(d, x, y, s, color=BAD):
    text(d, (x, y), "=", s, color, anchor="mm")


# 研究ごとの絵(左のパネルの下半分。y≈540〜800 に収める)
def p_store(d):
    shop(d, 300, 660, 260)
    queue(d, 470, 610, 5, 150)
    arrow(d, 870, 950, 680)
    text(d, (1010, 640), "+12〜", 40, GOOD, anchor="mm")
    text(d, (1010, 700), "38%", 56, GOOD, anchor="mm")


def p_odds(d):
    ticket(d, 260, 610, 220)
    ticket(d, 260, 740, 220)
    text(d, (450, 670), "どこで", 42, INK, anchor="lm")
    text(d, (450, 730), "買っても", 42, INK, anchor="lm")
    eq(d, 700, 690, 110)
    text(d, (900, 650), "2,000万枚", 50, BAD, anchor="mm")
    text(d, (900, 720), "に1本", 50, BAD, anchor="mm")


def p_lotto(d):
    for i, (n, c) in enumerate([(7, BAD), (13, GOOD), (21, GOOD), (36, BAD)]):
        cx = 200 + i * 135
        d.ellipse([cx - 52, 610, cx + 52, 714], fill=WHITE, outline=c, width=LW)
        text(d, (cx, 662), str(n), 46, INK, anchor="mm")
    text(d, (265, 760), "先週出た→避ける", 32, BAD, anchor="mm")
    text(d, (540, 760), "よく出る→賭ける", 32, GOOD, anchor="mm")
    arrow(d, 760, 840, 662)
    text(d, (960, 662), "同じ", 64, BAD, anchor="mm")


def p_casino(d):
    roulette(d, 300, 680, 120)
    board(d, 480, 560, [(32, RED), (19, RED), (4, WHITE)])
    arrow(d, 680, 760, 680)
    bean(d, 850, 580, 200, fill=GOOD)
    text(d, (980, 610), "もっと", 34, GOOD, anchor="mm")
    text(d, (980, 655), "賭ける", 34, GOOD, anchor="mm")


def p_1985(d):
    basketball(d, 220, 680, 80)
    for i, ok in enumerate([1, 1, 1]):
        text(d, (360 + i * 60, 680), "○", 54, GOOD, anchor="mm")
    arrow(d, 550, 610, 680)
    text(d, (720, 640), "46%", 70, BAD, anchor="mm")
    text(d, (920, 640), "56%", 70, GOOD, anchor="mm")
    text(d, (720, 720), "3本入った後", 28, SUB, heavy=False, anchor="mm")
    text(d, (920, 720), "3本外れた後", 28, SUB, heavy=False, anchor="mm")


def p_coin(d):
    seq = "表表裏表"
    for i, f in enumerate(seq):
        coin(d, 200 + i * 115, 640, 46, f, counted=(i > 0 and seq[i - 1] == "表"))
    text(d, (370, 752), "表の直後(○)だけ数える", 32, INK, anchor="mm")
    arrow(d, 640, 720, 650)
    text(d, (860, 600), "50%", 50, SUB, anchor="mm")
    line(d, [(800, 606), (920, 606)], RED, 8)
    text(d, (860, 700), "約40%", 70, GOOD, anchor="mm")


def p_volley(d):
    volleyball(d, 230, 670, 85)
    bean(d, 430, 580, 200, fill=GOOD)
    fire(d, 430, 545, 40)
    arrow(d, 560, 640, 680)
    text(d, (830, 640), "ボールを集めると", 38, INK, anchor="mm")
    text(d, (830, 710), "得点が増えた", 54, GOOD, anchor="mm")


def p_nba(d):
    basketball(d, 220, 680, 80)
    fire(d, 220, 570, 40)
    text(d, (470, 640), "難しいシュート", 40, BAD, anchor="mm")
    text(d, (470, 710), "が増える", 40, INK, anchor="mm")
    arrow(d, 640, 720, 680)
    text(d, (880, 640), "そろえると", 36, INK, anchor="mm")
    text(d, (880, 710), "+1〜2pt", 60, GOOD, anchor="mm")


def p_mlb(d):
    baseball(d, 230, 680, 80)
    chart(d, 380, 580, 340, 210, [0.2, 0.5, 0.35, 0.8, 0.6, 0.9])
    text(d, (890, 640), "打者も", 46, GOOD, anchor="mm")
    text(d, (890, 710), "投手も", 46, GOOD, anchor="mm")


def p_fund(d):
    d.rounded_rectangle([150, 580, 520, 790], radius=16, fill=WHITE, outline=INK, width=LW)
    text(d, (335, 630), "過去1年", 40, INK, anchor="mm")
    text(d, (335, 710), "+30%!", 72, GOOD, anchor="mm")
    arrow(d, 560, 640, 690)
    chart(d, 680, 580, 380, 210, [0.9, 0.4, 0.6, 0.3, 0.5, 0.35], BAD)


def p_bet(d):
    text(d, (250, 640), "連勝中", 50, GOOD, anchor="mm")
    text(d, (250, 715), "買われすぎ", 40, INK, anchor="mm")
    arrow(d, 420, 500, 680)
    text(d, (660, 640), "逆に賭けても", 40, INK, anchor="mm")
    text(d, (660, 715), "手数料で消える", 40, BAD, anchor="mm")
    text(d, (960, 680), "¥", 110, GOLD, anchor="mm")


# 1件=(年, 国, 種類, 見出し, データ3つ, 絵, 前の議席, 後の議席, 速報の見出し, 出典)
G, B, K = GOOD, BAD, INK
EVENTS = [
    ("2008", "アメリカ", "テキサス州の売り上げデータ", [[("当たりが出た売り場は", K)], [("売り上げ", K), ("12〜38%増", G)]],
     [("対象", "テキサス州"), ("続いた期間", "最長40週"), ("当たる確率", "同じ")], p_store, 50, 44,
     "「ラッキーな売り場」は思い込み", "出典：Guryan & Kearney, American Economic Review 2008"),
    ("2016", "デンマーク", "ロトの数字の選び方", [[("出た数字を避け", B), ("、", K)], [("よく出る数字に", G), ("賭ける", K)]],
     [("対象", "デンマークのロト"), ("2つの思い込み", "両方あり"), ("当たりやすさ", "同じ")], p_lotto, 44, 38,
     "くじの玉に記憶はない", "出典：Suetens, Galbo-Jørgensen & Tyran, J. of the European Economic Association 2016"),
    ("2005", "アメリカ", "カジノの実際の賭け", [[("勝った客ほど", K)], [("たくさん賭けた", G)]],
     [("客", "139人"), ("賭け", "24,131回"), ("確率", "変わらない")], p_casino, 38, 35,
     "流れを読んでも勝てない", "出典：Croson & Sundali, Journal of Risk and Uncertainty 2005"),
    ("1985", "アメリカ", "決定的な分析", [[("ホットハンドは", K)], [("錯覚", B), ("だった？", K)]],
     [("信じたファン", "91%"), ("3本成功の後", "46%"), ("3本失敗の後", "56%")], p_1985, 35, 25,
     "学者の常識は「錯覚」", "出典：Gilovich, Vallone & Tversky, Cognitive Psychology 1985"),
    ("2015", "スペイン", "数学の証明", [[("計算に", K), ("偏り", G), ("があった", K)], [("直すと", K), ("+13ポイント", G)]],
     [("コイン4回", "約40%"), ("偏り", "約8ポイント"), ("掲載", "Econometrica")], p_coin, 25, 40,
     "ホットハンドは本当にあった", "出典：Miller & Sanjurjo, Econometrica 2018(2015年に公開)"),
    ("2012", "ドイツ", "バレーボール1部の26選手", [[("調子のいい選手に", K)], [("集めると", K), ("得点増", G)]],
     [("対象", "トップ26人"), ("波", "あり"), ("セッター", "見抜く")], p_volley, 40, 43,
     "流れを使う作戦は勝つ", "出典：Raab, Gula & Gigerenzer, J. of Experimental Psychology: Applied 2012"),
    ("2014", "アメリカ", "NBAの全シュート", [[("難しさをそろえると", K)], [("成功率", K), ("アップ", G)]],
     [("データ", "カメラの位置"), ("シュート", "難しくなる"), ("成功率", "+1〜2pt")], p_nba, 43, 49,
     "乗りすぎに注意。でも波はある", "出典：Bocskocsky, Ezekowitz & Stein, MIT Sloan Sports Analytics Conf. 2014"),
    ("2018", "アメリカ", "大リーグの打席", [[("打者にも投手にも", K)], [("調子の波", G), ("がある", K)]],
     [("対象", "大リーグ"), ("打者", "波あり"), ("投手", "波あり")], p_mlb, 49, 55,
     "スポーツでは流れ派が逆転", "出典：Green & Zwiebel, Management Science 2018"),
    ("1997", "アメリカ", "投資信託30年分", [[("好成績は", K), ("続かない", B)]],
     [("期間", "30年分"), ("つぶれた投信", "も含む"), ("説明", "市場と手数料")], p_fund, 55, 45,
     "お金の世界で確率派が再逆転", "出典：Carhart, Journal of Finance 1997"),
    ("1989", "アメリカ", "スポーツの賭け", [[("連勝チームは", K)], [("買われすぎ", B), ("。得は胴元", K)]],
     [("市場", "NBAの賭け"), ("連勝", "買われすぎ"), ("逆張り", "手数料で消える")], p_bet, 45, 42,
     "得をするのは胴元", "出典：Camerer, American Economic Review 1989/Brown & Sauer 1993"),
]


def delta_label(before, after):
    return f"{frames.LBL[0] if after > before else frames.LBL[1]} +{abs(after - before)}議席"


# ---------- 確認用スライド ----------
def hook_slide(path):
    im, d = stage()
    panel(d, (140, 150, W - 140, 960))
    text(d, (W / 2, 250), "年末ジャンボ発売中", 64, RED, anchor="mm")
    shop(d, 520, 600, 420, "1等続々！")
    queue(d, 820, 470, 7, 230)
    text(d, (W / 2, 880), "この売り場、本当によく当たる？", 76, INK, anchor="mm")
    im.save(path)


def rules_slide(path):
    im, d = stage()
    panel(d, (140, 140, W - 140, 980))
    text(d, (W / 2, 220), "今日のルール", 72, INK, anchor="mm")
    for cx, lab, desc, c in ((W / 2 - 420, "流れ派", "流れやツキは本当にある\n乗った人が得をする", GOOD),
                             (W / 2 + 420, "確率派", "偶然は偶然\n流れに乗っても得はしない", BAD)):
        d.rounded_rectangle([cx - 220, 300, cx + 220, 400], radius=50, fill=c)
        text(d, (cx, 350), lab, 60, WHITE, anchor="mm")
        for k, s in enumerate(desc.split("\n")):
            text(d, (cx, 460 + k * 60), s, 42, INK, anchor="mm")
    text(d, (W / 2, 350), "vs", 56, TRIM, anchor="mm")
    rows = [("数学の証明", 15), ("研究のまとめ・決定的な分析", 10), ("何万件もの実データ", 6), ("条件が限られた結果", 3)]
    for i, (k, n) in enumerate(rows):
        y = 640 + i * 80
        text(d, (560, y), k, 44, INK, anchor="lm")
        text(d, (1360, y), f"{n}議席", 48, GOOD if i == 0 else INK, anchor="rm")
    text(d, (W / 2, 950), "スタートは 50 対 50", 40, SUB, heavy=False, anchor="mm")
    im.save(path)


def theory_slide(path):
    im, d = stage()
    panel(d, (140, 150, W - 140, 960))
    text(d, (W / 2, 250), "裏にある理論", 54, SUB, anchor="mm")
    text(d, (W / 2, 360), "ホットハンド", 130, GOOD, anchor="mm")
    basketball(d, 520, 640, 110)
    fire(d, 520, 480, 60)
    for i in range(3):
        text(d, (720 + i * 90, 640), "○", 80, GOOD, anchor="mm")
    arrow(d, 1010, 1110, 640)
    text(d, (1320, 640), "次も入る？", 80, INK, anchor="mm")
    text(d, (W / 2, 870), "続けて成功した人は、次も成功しやすい？", 56, INK, anchor="mm")
    im.save(path)


def coin_slide(path):
    """コイン4回:表の直後の表の割合を、並びごとに出して平均すると約40%。表=金・裏=灰青、数える回にオレンジの輪。"""
    im, d = stage()
    panel(d, (140, 120, W - 140, 1000))
    text(d, (W / 2, 190), "コインを4回投げて「表の直後」だけを見ると…", 54, INK, anchor="mm")
    # 凡例
    coin(d, 520, 262, 22, "表")
    text(d, (556, 262), "表", 34, INK, anchor="lm")
    coin(d, 680, 262, 22, "裏")
    text(d, (716, 262), "裏", 34, INK, anchor="lm")
    coin(d, 860, 262, 22, "表", counted=True)
    text(d, (900, 262), "＝数える回(表の直後)", 34, GOOD, anchor="lm")
    seqs = []
    for k in range(16):
        q = "".join("表" if (k >> (3 - i)) & 1 else "裏" for i in range(4))
        after = [q[i + 1] for i in range(3) if q[i] == "表"]
        if after:
            seqs.append((q, sum(a == "表" for a in after), len(after)))
    seqs.sort(key=lambda t: t[1] / t[2])
    for j, (q, hit, n) in enumerate(seqs):
        col, row = j // 7, j % 7
        x, y = 250 + col * 800, 345 + row * 78
        for i, f in enumerate(q):
            coin(d, x + i * 70, y, 26, f, counted=(i > 0 and q[i - 1] == "表"))
        pct = hit / n
        c = GOOD if pct > 0.5 else (BAD if pct < 0.5 else SUB)
        text(d, (x + 300, y), f"{hit}/{n}", 34, SUB, heavy=False, anchor="lm")
        text(d, (x + 560, y), f"{round(pct * 100)}%", 44, c, anchor="rm")
    avg = sum(h / n for _, h, n in seqs) / len(seqs)
    d.line([(W / 2, 315), (W / 2, 860)], fill=(222, 218, 210), width=3)
    d.rounded_rectangle([W / 2 - 450, 900, W / 2 + 450, 975], radius=38, fill=GOOD)
    text(d, (W / 2, 938), f"14通りの平均 = 約{round(avg * 100)}%(50%にならない)", 46, WHITE, anchor="mm")
    im.save(path)


def verdict_slide(path):
    im, d = stage()
    text(d, (W / 2, 150), "最終判定", 80, TRIM, anchor="mm")
    cols = [("スポーツ", "人がプレーする世界", "流れ派の勝ち", GOOD, "流れは本当にある。\nうまく使うと勝てる"),
            ("くじ・カジノ・投資", "偶然と市場の世界", "確率派の勝ち", BAD, "流れに乗っても\n得はしない")]
    for i, (title, sub, res, c, body) in enumerate(cols):
        x0 = 140 + i * 840
        panel(d, (x0, 240, x0 + 800, 760))
        text(d, (x0 + 400, 320), title, 64, INK, anchor="mm")
        text(d, (x0 + 400, 395), sub, 38, SUB, heavy=False, anchor="mm")
        d.rounded_rectangle([x0 + 150, 450, x0 + 650, 550], radius=50, fill=c)
        text(d, (x0 + 400, 500), res, 56, WHITE, anchor="mm")
        for k, s in enumerate(body.split("\n")):
            text(d, (x0 + 400, 620 + k * 60), s, 44, INK, anchor="mm")
    d.rounded_rectangle([340, 820, W - 340, 960], radius=30, fill=TRIM)
    text(d, (W / 2, 890), "確実に勝つのは「流れを信じる気持ち」を売る側", 56, INK, anchor="mm")
    im.save(path)


def summary_slide(path):
    im, d = stage()
    panel(d, (140, 150, W - 140, 960))
    text(d, (W / 2, 240), "今日のまとめ", 72, INK, anchor="mm")
    items = [("宝くじ", "どの売り場でも、1枚の当たる確率は同じ"),
             ("買い方", "予算を決めて、夢を買う。行列は年末のお楽しみ"),
             ("スポーツ", "調子のいい選手に任せるのはアリ。差は数ポイント"),
             ("作戦", "流れは、信じすぎないのが一番")]
    for i, (k, v) in enumerate(items):
        y = 380 + i * 135
        d.rounded_rectangle([230, y - 42, 500, y + 42], radius=42, fill=GOOD if i % 2 else BAD)
        text(d, (365, y), k, 44, WHITE, anchor="mm")
        text(d, (550, y), v, 48, INK, anchor="lm")
    im.save(path)


def contact_sheet(paths, out, cols=4):
    tw, th = 480, 270
    rows = math.ceil(len(paths) / cols)
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (16, 20, 32))
    for i, p in enumerate(paths):
        im = Image.open(p).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
    sheet.save(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = []

    def p(name):
        path = os.path.join(OUT, name)
        paths.append(path)
        return path

    hook_slide(p("00_hook.png"))
    series_card(TITLE, SUBTITLE, *frames.LBL).save(p("01_title.png"))
    rules_slide(p("02_rules.png"))
    flash = {"2005": ("くじやカジノでは確率派が圧勝", None), "2018": ("スポーツで逆転！", None),
             "1989": ("お金の世界で再逆転", None)}
    for i, (year, country, kind, title, facts, picto, before, after, _, source) in enumerate(EVENTS, 1):
        if year == "1985":
            theory_slide(p(f"{i + 2:02d}_0_theory.png"))
        if year == "2015":
            coin_slide(p(f"{i + 2:02d}_0_coin.png"))
        study_card(p(f"{i + 2:02d}_1_{year}.png"), year, country, kind, title, facts, picto, before, after,
                   delta_label(before, after), source)
        if year in flash:
            parliament(p(f"{i + 2:02d}_2_seats.png"), year, flash[year][0], after)
    verdict_slide(p("90_verdict.png"))
    summary_slide(p("91_summary.png"))
    contact_sheet(paths, os.path.join(OUT, "..", "contact_sheet.png"))
    print(thumbnail("hothand_war", TITLE, SUBTITLE, *frames.LBL))
    print(len(paths), "slides ->", OUT)


if __name__ == "__main__":
    sys.exit(main())
