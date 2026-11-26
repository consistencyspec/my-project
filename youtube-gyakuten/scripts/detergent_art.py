"""液体洗剤の回のイラスト(丸みのある線画。線の太さをそろえ、色は少しだけ塗る)。

どれも (d, cx, cy, s) で、(cx, cy) が絵のまん中、s がだいたいの幅。
  .venv/bin/python scripts/detergent_art.py  -> output/detergent_story/ の 1:41(アタック)・2:53(アタックNeo)・トップNANOX の場面の見本

商品の写真やロゴはそのまま使わず、番組の線画の絵柄で「それとわかる」程度に描く
(緑の箱・取っ手・白い帯・紺の文字・赤と黄色の線)。
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, LW, WHITE, font, line, text  # noqa: E402

BOX_GREEN = (52, 156, 112)
BOX_GREEN_DARK = (34, 118, 84)
BOX_TOP = (226, 238, 230)
NAVY = (32, 52, 120)
RED = (214, 52, 48)
YELLOW = (246, 196, 60)
SPOON = (205, 212, 222)
POWDER = (250, 250, 252)


def powder_box(d, cx, cy, s, name="アタック"):
    """1987年ごろの箱入りの粉洗剤(取っ手つきの緑の箱)。s は箱の正面の幅。"""
    w, h = s, s * 1.08
    dep = s * 0.22                       # 奥行き(右上にずらして側面を見せる)
    x0, x1 = cx - w / 2 - dep / 2, cx + w / 2 - dep / 2
    y0, y1 = cy - h / 2 + dep / 2, cy + h / 2 + dep / 2
    # 取っ手(白いプラスチックの持ち手)
    hx0, hx1, hy = x0 + w * 0.12 + dep / 2, x1 - w * 0.12 + dep / 2, y0 - dep / 2
    hx0, hx1 = hx0 + w * 0.1, hx1 - w * 0.1
    d.arc([hx0, hy - s * 0.26, hx1, hy + s * 0.26], 180, 360, fill=INK, width=LW + 12)
    d.arc([hx0, hy - s * 0.26, hx1, hy + s * 0.26], 180, 360, fill=WHITE, width=12)
    # 上の面・側面・正面
    d.polygon([(x0, y0), (x0 + dep, y0 - dep), (x1 + dep, y0 - dep), (x1, y0)], fill=BOX_TOP, outline=INK)
    d.polygon([(x1, y0), (x1 + dep, y0 - dep), (x1 + dep, y1 - dep), (x1, y1)], fill=BOX_GREEN_DARK, outline=INK)
    d.rectangle([x0, y0, x1, y1], fill=BOX_GREEN)
    line(d, [(x0, y0), (x0 + dep, y0 - dep), (x1 + dep, y0 - dep), (x1 + dep, y1 - dep), (x1, y1), (x0, y1), (x0, y0)])
    line(d, [(x0, y0), (x1, y0), (x1 + dep, y0 - dep)])
    line(d, [(x1, y0), (x1, y1)])
    # 取っ手の付け根
    for hx in (hx0, hx1):
        d.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], fill=WHITE, outline=INK, width=5)
    # 上の白い帯「スプーン1杯で驚きの白さに」
    by = y0 + h * 0.15
    d.rounded_rectangle([x0 + w * 0.06, by - h * 0.07, x1 - w * 0.06, by + h * 0.07], radius=h * 0.07, fill=WHITE, outline=INK, width=5)
    pill, rest = "スプーン1杯", "で驚きの白さに"
    fs = int(s * 0.075)
    while d.textlength(pill, font=font(fs)) + fs * 0.85 + d.textlength(rest, font=font(int(fs * 0.9))) > w * 0.8:
        fs -= 1
    pw = d.textlength(pill, font=font(fs)) + fs * 0.6
    px = x0 + w * 0.09
    d.rounded_rectangle([px, by - fs * 0.72, px + pw, by + fs * 0.72], radius=fs * 0.72, fill=RED)
    text(d, (px + pw / 2, by), pill, fs, WHITE, anchor="mm")
    text(d, (px + pw + fs * 0.25, by), rest, int(fs * 0.9), INK, anchor="lm")
    # 商品名(番組の太いゴシックで。ロゴの字体はまねない)
    ly = y0 + h * 0.5
    d.rounded_rectangle([x0 + w * 0.05, ly - h * 0.19, x1 - w * 0.05, ly + h * 0.17], radius=24, fill=WHITE, outline=INK, width=6)
    ns = int(min(s * 0.24, s * 0.24 * (w * 0.82) / max(1, d.textlength(name, font=font(int(s * 0.24))))))
    text(d, (cx - dep / 2, ly - h * 0.02), name, ns, NAVY, anchor="mm")
    # 赤と黄色の線
    sy = ly + h * 0.115
    d.rectangle([x0 + w * 0.1, sy, x1 - w * 0.1, sy + h * 0.025], fill=RED)
    d.rectangle([x0 + w * 0.1, sy + h * 0.035, x1 - w * 0.1, sy + h * 0.05], fill=YELLOW)


def spoon(d, cx, cy, s):
    """粉をすくった計量スプーン。"""
    r = s * 0.28
    bx, by = cx - s * 0.18, cy
    # 柄
    d.rounded_rectangle([bx + r * 0.8, by - s * 0.05, cx + s * 0.5, by + s * 0.05], radius=s * 0.05, fill=SPOON, outline=INK, width=LW - 2)
    # すくう所と、山もりの粉
    d.chord([bx - r * 0.95, by - r * 0.55, bx + r * 0.95, by + r * 0.35], 180, 360, fill=POWDER, outline=INK, width=6)
    d.chord([bx - r, by - r, bx + r, by + r], 0, 180, fill=SPOON, outline=INK, width=LW - 2)
    for dx, dy in ((-0.4, -0.15), (0.1, -0.35), (0.45, -0.1)):
        d.ellipse([bx + dx * r - 5, by + dy * r - 5, bx + dx * r + 5, by + dy * r + 5], fill=(200, 210, 230))


def white_shirt(d, cx, cy, s):
    """まっ白に洗い上がったシャツと、きらきら。"""
    w, h = s, s * 0.9
    x0, y0 = cx - w / 2, cy - h / 2
    pts = [(x0 + w * 0.32, y0), (x0, y0 + h * 0.18), (x0 + w * 0.1, y0 + h * 0.4), (x0 + w * 0.22, y0 + h * 0.34),
           (x0 + w * 0.22, y0 + h), (x0 + w * 0.78, y0 + h), (x0 + w * 0.78, y0 + h * 0.34), (x0 + w * 0.9, y0 + h * 0.4),
           (x0 + w, y0 + h * 0.18), (x0 + w * 0.68, y0)]
    d.polygon(pts, fill=WHITE)
    line(d, pts + [pts[0]])
    d.polygon([(x0 + w * 0.32, y0), (cx, y0 + h * 0.2), (x0 + w * 0.68, y0)], fill=(236, 240, 248))
    line(d, [(x0 + w * 0.32, y0), (cx, y0 + h * 0.2), (x0 + w * 0.68, y0)], w=6)
    line(d, [(cx, y0 + h * 0.2), (cx, y0 + h * 0.95)], w=5)
    for k in range(3):
        yy = y0 + h * (0.38 + k * 0.18)
        d.ellipse([cx + 10, yy - 7, cx + 24, yy + 7], fill=INK)
    for sx, sy, r in ((x0 - s * 0.08, y0 + h * 0.05, s * 0.09), (x0 + w + s * 0.1, y0 + h * 0.3, s * 0.12),
                      (x0 + w + s * 0.02, y0 + h * 0.85, s * 0.07)):
        sparkle(d, sx, sy, r)


def sparkle(d, cx, cy, r, color=YELLOW):
    pts = [(cx, cy - r), (cx + r * 0.25, cy - r * 0.25), (cx + r, cy), (cx + r * 0.25, cy + r * 0.25),
           (cx, cy + r), (cx - r * 0.25, cy + r * 0.25), (cx - r, cy), (cx - r * 0.25, cy - r * 0.25)]
    d.polygon(pts, fill=color, outline=INK)
    line(d, pts + [pts[0]], w=5)


# 1:41「第1話 粉の黄金時代」の場面の要素(story の要素のリストにそのまま入れる)
def attack_scene_elements():
    from coffee_story import words, year_tag
    from frames import arrow
    return [
        lambda d: year_tag(d, 960, 270, "1987年"),
        lambda d: powder_box(d, 560, 520, 300),
        lambda d: spoon(d, 990, 520, 240),
        lambda d: arrow(d, 1140, 1230, 530),
        lambda d: white_shirt(d, 1450, 490, 270),
        lambda d: words(d, 1450, 700, "驚きの白さ", 56, GOOD),
    ]


TEAL = (0, 150, 170)
TEAL_DARK = (0, 110, 130)
PINK = (226, 70, 120)


def neo_bottle(d, cx, cy, s, name="アタック", sub="Neo"):
    """2009年の超コンパクト液体洗剤(白い細長ボトル・青緑のキャップ・紺の商品名に Neo)。s はボトルの幅。"""
    w, h = s, s * 2.5
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    # キャップ(青緑。上に注ぎ口)
    cw_, ch = w * 0.62, h * 0.13
    cap = [cx - cw_ / 2, y0, cx + cw_ / 2, y0 + ch]
    d.rounded_rectangle([cx - cw_ * 0.3, y0 - h * 0.04, cx + cw_ * 0.3, y0 + 10], radius=12, fill=TEAL_DARK, outline=INK, width=6)
    d.rounded_rectangle(cap, radius=18, fill=TEAL, outline=INK, width=LW - 2)
    for k in range(1, 4):
        xx = cap[0] + cw_ * k / 4
        d.line([(xx, y0 + 12), (xx, y0 + ch - 12)], fill=TEAL_DARK, width=5)
    # 肩と胴(白)
    by0 = y0 + ch
    body = [(cx - cw_ / 2, by0), (x0, by0 + h * 0.1), (x0, y1 - 20), (x0 + 20, y1), (x1 - 20, y1), (x1, y1 - 20),
            (x1, by0 + h * 0.1), (cx + cw_ / 2, by0)]
    d.polygon(body, fill=WHITE)
    # 下の青緑の波
    wy = y1 - h * 0.22
    d.polygon([(x0, wy + h * 0.06), (cx, wy - h * 0.03), (x1, wy), (x1, y1 - 20), (x1 - 20, y1), (x0 + 20, y1), (x0, y1 - 20)], fill=TEAL)
    d.polygon([(x0, wy + h * 0.1), (cx, wy + h * 0.03), (x1, wy + h * 0.05), (x1, y1 - 20), (x1 - 20, y1), (x0 + 20, y1), (x0, y1 - 20)], fill=TEAL_DARK)
    line(d, body + [body[0]])
    # 上の帯(青緑の細い線)と ULTRA
    ty = by0 + h * 0.14
    d.line([(x0 + 14, ty), (x1 - 14, ty)], fill=TEAL, width=8)
    text(d, (cx, ty + h * 0.045), "ULTRA", int(w * 0.13), TEAL_DARK, anchor="mm")
    # 商品名(番組の太いゴシック。ロゴの字体はまねない)
    ny = by0 + h * 0.33
    ns = int(w * 0.3)
    while d.textlength(name, font=font(ns)) > w * 0.9:
        ns -= 1
    text(d, (cx, ny), name, ns, NAVY, anchor="mm")
    d.rectangle([x0 + w * 0.08, ny + ns * 0.62, x1 - w * 0.08, ny + ns * 0.62 + 8], fill=RED)
    d.rectangle([x0 + w * 0.08, ny + ns * 0.62 + 12, x1 - w * 0.08, ny + ns * 0.62 + 18], fill=YELLOW)
    # Neo(青緑の斜めの字)
    text(d, (x1 - w * 0.08, ny + ns * 1.55), sub, int(w * 0.26), TEAL, anchor="rm")
    # 小さい帯「濃縮」
    py = ny + ns * 2.45
    d.rounded_rectangle([cx - w * 0.3, py - w * 0.075, cx + w * 0.3, py + w * 0.075], radius=w * 0.075, fill=PINK)
    text(d, (cx, py), "超濃縮", int(w * 0.1), WHITE, anchor="mm")


def plain_bottle(d, cx, cy, s, label="1kg"):
    """それまでの大きな液体洗剤のボトル(取っ手つき・灰色がかった線画)。"""
    w, h = s, s * 1.45
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    d.rounded_rectangle([cx - w * 0.36, y0, cx - w * 0.04, y0 + h * 0.1], radius=10, fill=(214, 220, 230), outline=INK, width=6)
    d.rounded_rectangle([x0, y0 + h * 0.1, x1, y1], radius=36, fill=(236, 240, 246), outline=INK, width=LW)
    d.rounded_rectangle([x1 - w * 0.36, y0 + h * 0.2, x1 - w * 0.1, y0 + h * 0.5], radius=26, fill=WHITE, outline=INK, width=6)
    d.rounded_rectangle([x0 + w * 0.1, cy, x1 - w * 0.1, cy + h * 0.28], radius=16, fill=WHITE, outline=INK, width=5)
    text(d, (cx, cy + h * 0.14), label, int(w * 0.2), SUB_INK, anchor="mm")


SUB_INK = (90, 96, 112)


# 2:53「第3話 アタックNeo」の場面の要素
def neo_scene_elements():
    from coffee_story import chip, words, year_tag
    return [
        lambda d: year_tag(d, 1420, 280, "2009年8月"),
        lambda d: plain_bottle(d, 430, 460, 260, "1kg"),
        lambda d: words(d, 430, 720, "それまでの液体", 44, SUB_INK),
        lambda d: words(d, 680, 470, "=", 110, INK),
        lambda d: neo_bottle(d, 920, 450, 190),
        lambda d: words(d, 920, 720, "400g", 48, INK),
        lambda d: chip(d, 1420, 440, "約2.5倍に濃縮", GOOD, 56),
        lambda d: chip(d, 1420, 600, "すすぎ1回", GOOD, 56),
    ]


NANO_BLUE = (30, 110, 200)
NANO_LIGHT = (200, 228, 248)


def nanox_bottle(d, cx, cy, s, name="NANOX", kana="ナノックス", brand="トップ"):
    """2010年の高濃度の液体洗剤(白くて丸みのあるボトル・白いキャップ・青い NANOX)。s はボトルの幅。"""
    w, h = s, s * 1.55
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    # キャップ(白に水色の帯)
    cw_, ch = w * 0.66, h * 0.14
    d.rounded_rectangle([cx - cw_ / 2, y0, cx + cw_ / 2, y0 + ch], radius=22, fill=WHITE, outline=INK, width=LW - 2)
    d.rectangle([cx - cw_ / 2 + 6, y0 + ch * 0.62, cx + cw_ / 2 - 6, y0 + ch * 0.8], fill=NANO_LIGHT)
    # 胴(丸い肩)
    by0 = y0 + ch - 4
    d.rounded_rectangle([x0, by0, x1, y1], radius=w * 0.22, fill=WHITE, outline=INK, width=LW)
    # 下の水色
    d.rounded_rectangle([x0 + 8, y1 - h * 0.17, x1 - 8, y1 - 8], radius=w * 0.15, fill=NANO_LIGHT)
    d.line([(x0 + 10, y1 - h * 0.17), (x1 - 10, y1 - h * 0.17)], fill=INK, width=4)
    # 赤い小さなブランド名(左上。ロゴの形はまねない)
    bs = int(w * 0.11)
    bw = d.textlength(brand, font=font(bs)) + bs * 0.8
    bx, byy = x0 + w * 0.1, by0 + h * 0.1
    d.rounded_rectangle([bx, byy - bs * 0.7, bx + bw, byy + bs * 0.7], radius=bs * 0.7, fill=RED)
    text(d, (bx + bw / 2, byy), brand, bs, WHITE, anchor="mm")
    # 青い細い文字の帯(キャッチコピーの代わり)
    for k in range(2):
        yy = byy + h * (0.08 + k * 0.045)
        d.line([(x0 + w * 0.18, yy), (x1 - w * 0.12, yy)], fill=NANO_LIGHT, width=8)
    # かな と NANOX
    ky = by0 + h * 0.36
    text(d, (cx, ky), kana, int(w * 0.09), NANO_BLUE, anchor="mm")
    ns = int(w * 0.3)
    while d.textlength(name, font=font(ns)) > w * 0.84:
        ns -= 1
    text(d, (cx, ky + ns * 0.85), name, ns, NANO_BLUE, anchor="mm")
    # 「高濃度」の小さな帯
    py = ky + ns * 1.75
    d.rounded_rectangle([cx - w * 0.28, py - w * 0.065, cx + w * 0.28, py + w * 0.065], radius=w * 0.065, fill=NANO_BLUE)
    text(d, (cx, py), "高濃度", int(w * 0.085), WHITE, anchor="mm")


# 「第3話 トップNANOX」の場面の要素(アタックNeo と並べてライバルに見せる)
def nanox_scene_elements():
    from coffee_story import chip, words, year_tag
    return [
        lambda d: year_tag(d, 1420, 280, "2010年1月"),
        lambda d: neo_bottle(d, 420, 440, 150),
        lambda d: words(d, 420, 690, "2009年 花王", 40, SUB_INK),
        lambda d: words(d, 640, 470, "VS", 96, RED),
        lambda d: nanox_bottle(d, 900, 450, 280),
        lambda d: words(d, 900, 720, "2010年 ライオン", 44, INK),
        lambda d: chip(d, 1420, 440, "皮脂汚れを落とす", GOOD, 52),
        lambda d: chip(d, 1420, 600, "高濃度の液体", GOOD, 52),
    ]


LOGOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logos")


def logo(d, cx, cy, s, name):
    """ブランドのロゴ画像(assets/logos/<name>.png)を、白い角丸の台の上に置く。s は台の幅。"""
    im = Image.open(os.path.join(LOGOS, name + ".png")).convert("RGBA")
    # 白っぽい背景(画像のふち)は透明にして、台の白になじませる
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    a[(rgb.min(-1) > 220) & (rgb.max(-1) - rgb.min(-1) < 25), 3] = 0
    im = Image.fromarray(a)
    pad = s * 0.08
    k = min((s - pad * 2) / im.width, (s - pad * 2) / im.height)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    d.rounded_rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], radius=28, fill=WHITE, outline=INK, width=6)
    d._image.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# 「第2話 服が変わる」の場面の要素(海外・国内のファストファッションの年表)
def fashion_scene_elements():
    from coffee_story import words, year_tag
    cols = [(470, "1995年", "gap", "GAPが日本に上陸"), (960, "1998年ごろ", "uniqlo", "ユニクロのフリース"),
            (1450, "2008年", "hm", "H&Mが銀座に上陸")]
    out = []
    for x, y, n, cap in cols:
        out += [lambda d, x=x, y=y: year_tag(d, x, 300, y),
                lambda d, x=x, n=n: logo(d, x, 520, 280, n),
                lambda d, x=x, cap=cap: words(d, x, 730, cap, 46)]
    return out


GEL_BLUE = (30, 70, 170)
GEL_BLUE_DARK = (20, 48, 128)
GEL_GREEN = (60, 180, 110)
GEL_SKY = (90, 170, 235)


def gel_pod(d, cx, cy, s):
    """ジェルボール1粒(上から見た丸い粒。青・緑・白の3つの部屋)。s は粒の幅。"""
    r = s / 2
    d.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], fill=GEL_BLUE, outline=INK, width=max(4, int(s * 0.05)))
    d.pieslice([cx - r * 0.82, cy - r * 0.7, cx + r * 0.82, cy + r * 0.7], 200, 330, fill=GEL_GREEN)
    d.pieslice([cx - r * 0.82, cy - r * 0.7, cx + r * 0.82, cy + r * 0.7], 330, 90, fill=WHITE)
    d.ellipse([cx - r * 0.3, cy - r * 0.26, cx + r * 0.3, cy + r * 0.26], fill=GEL_SKY)
    d.ellipse([cx - r * 0.55, cy - r * 0.62, cx - r * 0.25, cy - r * 0.42], fill=(255, 255, 255, 200))


def gel_box(d, cx, cy, s, brand="アリエール", name="ジェルボール"):
    """ジェルボールの箱(白い上部・青い胴・粒が見える窓)。s は箱の正面の幅。"""
    w, h = s, s * 0.95
    dep = s * 0.16
    x0, x1 = cx - w / 2 - dep / 2, cx + w / 2 - dep / 2
    y0, y1 = cy - h / 2 + dep / 2, cy + h / 2 + dep / 2
    # 上の面(ふた)・側面・正面
    d.polygon([(x0, y0), (x0 + dep, y0 - dep), (x1 + dep, y0 - dep), (x1, y0)], fill=(238, 242, 248))
    d.polygon([(x1, y0), (x1 + dep, y0 - dep), (x1 + dep, y1 - dep), (x1, y1)], fill=GEL_BLUE_DARK)
    d.rectangle([x0, y0, x1, y1], fill=GEL_BLUE)
    d.rectangle([x0, y0, x1, y0 + h * 0.36], fill=WHITE)
    d.polygon([(x1, y0), (x1 + dep, y0 - dep), (x1 + dep, y0 - dep + h * 0.36), (x1, y0 + h * 0.36)], fill=(214, 222, 236))
    # ブランド名(青い字。ロゴの字体はまねない)と青い丸
    bs = int(w * 0.13)
    d.ellipse([x0 + w * 0.06, y0 + h * 0.07, x0 + w * 0.2, y0 + h * 0.21], fill=GEL_SKY, outline=GEL_BLUE, width=5)
    text(d, (x0 + w * 0.24, y0 + h * 0.14), brand, bs, GEL_BLUE, anchor="lm")
    ns = int(w * 0.105)
    text(d, (x0 + w * 0.06, y0 + h * 0.28), name, ns, GEL_BLUE_DARK, anchor="lm")
    # 窓と、中に見える粒
    wy = y0 + h * 0.62
    d.rounded_rectangle([x0 + w * 0.06, wy - h * 0.2, x0 + w * 0.7, wy + h * 0.2], radius=h * 0.2, fill=(200, 225, 250), outline=INK, width=5)
    for k, (dx, dy) in enumerate(((0.2, 0.03), (0.38, -0.06), (0.55, 0.05))):
        gel_pod(d, x0 + w * dx, wy + h * dy, w * 0.2)
    # 右下の「洗浄力」の白い帯
    d.rounded_rectangle([x0 + w * 0.73, wy - h * 0.08, x1 - w * 0.03, wy + h * 0.08], radius=12, fill=WHITE)
    text(d, (x0 + w * 0.855, wy), "洗浄力", int(w * 0.06), GEL_BLUE, anchor="mm")
    line(d, [(x0, y0), (x0 + dep, y0 - dep), (x1 + dep, y0 - dep), (x1 + dep, y1 - dep), (x1, y1), (x0, y1), (x0, y0)])
    line(d, [(x0, y0), (x1, y0), (x1 + dep, y0 - dep)])
    line(d, [(x1, y0), (x1, y1)])


# 「第3話 第3の洗剤」の場面の要素(粉・液体・ジェルボール)
def gel_scene_elements():
    from coffee_story import chip, words, year_tag
    return [
        lambda d: year_tag(d, 1450, 280, "2014年"),
        lambda d: powder_box(d, 330, 470, 170),
        lambda d: words(d, 330, 690, "粉", 52, SUB_INK),
        lambda d: neo_bottle(d, 640, 450, 115),
        lambda d: words(d, 640, 690, "液体", 52, SUB_INK),
        lambda d: gel_box(d, 1050, 470, 330),
        lambda d: words(d, 1050, 720, "ジェルボール", 52, INK),
        lambda d: chip(d, 1530, 470, "第3の洗剤", GOOD, 60),
        lambda d: gel_pod(d, 1530, 620, 120),
    ]


# ---------- 動画用の小物 ----------
def soap_bar(d, cx, cy, s, label="石けん"):
    """固形石けん(角の丸い白っぽい四角)。"""
    w, h = s, s * 0.6
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h * 0.4, fill=(250, 236, 214), outline=INK, width=LW)
    d.rounded_rectangle([cx - w * 0.36, cy - h * 0.3, cx + w * 0.36, cy + h * 0.3], radius=h * 0.25, outline=(214, 190, 150), width=6)
    text(d, (cx, cy), label, int(s * 0.16), (150, 110, 60), anchor="mm")
    for dx, dy, r in ((0.45, -0.55, 0.08), (0.58, -0.75, 0.05), (0.3, -0.8, 0.06)):
        d.ellipse([cx + dx * w - r * s, cy + dy * h - r * s, cx + dx * w + r * s, cy + dy * h + r * s], outline=(120, 180, 230), width=5)


def washer(d, cx, cy, s, drum=True):
    """洗濯機。drum=True でドラム式(正面に丸い窓)、False で縦型(上にふた)。"""
    w, h = s, s * 1.15
    x0, y0 = cx - w / 2, cy - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=28, fill=WHITE, outline=INK, width=LW)
    d.line([(x0 + 8, y0 + h * 0.18), (x0 + w - 8, y0 + h * 0.18)], fill=INK, width=5)
    for k in range(3):
        d.ellipse([x0 + w * (0.1 + k * 0.1), y0 + h * 0.07, x0 + w * (0.16 + k * 0.1), y0 + h * 0.12], fill=SUB_INK)
    if drum:
        r = w * 0.32
        c = (cx, y0 + h * 0.58)
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(210, 226, 240), outline=INK, width=LW)
        d.chord([c[0] - r * 0.8, c[1] - r * 0.8, c[0] + r * 0.8, c[1] + r * 0.8], 20, 160, fill=(140, 190, 235))
    else:
        d.rounded_rectangle([x0 + w * 0.15, y0 - h * 0.06, x0 + w * 0.85, y0 + h * 0.02], radius=12, fill=(220, 230, 240), outline=INK, width=6)
        d.rounded_rectangle([x0 + w * 0.2, y0 + h * 0.3, x0 + w * 0.8, y0 + h * 0.85], radius=20, fill=(210, 226, 240), outline=INK, width=6)


def pct_bars(d, x0, base_y, items, h=300, bw=170, gap=90):
    """割合の棒グラフ(0〜100%)。items=[(ラベル, 値, 色)]。"""
    for i, (lab, v, c) in enumerate(items):
        x = x0 + i * (bw + gap)
        top = base_y - h * v / 100
        d.rounded_rectangle([x, top, x + bw, base_y], radius=14, fill=c, outline=INK, width=6)
        text(d, (x + bw / 2, top - 12), f"{v:g}%", 50, INK, anchor="mb")
        text(d, (x + bw / 2, base_y + 16), lab, 36, SUB_INK, heavy=False, anchor="ma")
    d.line([(x0 - 30, base_y), (x0 + len(items) * (bw + gap) - gap + 30, base_y)], fill=INK, width=5)


def ton_bars(d, x0, base_y, items, maxv, h=200, bw=110, gap=40):
    """生産量の棒グラフ(トン)。items=[(ラベル, 値(万トン), 色)]。"""
    for i, (lab, v, c) in enumerate(items):
        x = x0 + i * (bw + gap)
        top = base_y - h * v / maxv
        d.rounded_rectangle([x, top, x + bw, base_y], radius=12, fill=c, outline=INK, width=5)
        text(d, (x + bw / 2, top - 8), f"{v:g}万t", 32, INK, anchor="mb")
        text(d, (x + bw / 2, base_y + 10), lab, 30, SUB_INK, heavy=False, anchor="ma")
    d.line([(x0 - 20, base_y), (x0 + len(items) * (bw + gap) - gap + 20, base_y)], fill=INK, width=4)


def fleece(d, cx, cy, s, color=(90, 150, 220)):
    """フリース(ジッパーつきの上着)。"""
    w, h = s, s * 0.9
    x0, y0 = cx - w / 2, cy - h / 2
    pts = [(x0 + w * 0.3, y0), (x0, y0 + h * 0.2), (x0 + w * 0.05, y0 + h), (x0 + w * 0.22, y0 + h), (x0 + w * 0.24, y0 + h * 0.45),
           (x0 + w * 0.24, y0 + h), (x0 + w * 0.76, y0 + h), (x0 + w * 0.76, y0 + h * 0.45), (x0 + w * 0.78, y0 + h),
           (x0 + w * 0.95, y0 + h), (x0 + w, y0 + h * 0.2), (x0 + w * 0.7, y0)]
    d.polygon(pts, fill=color)
    line(d, pts + [pts[0]])
    d.rectangle([x0 + w * 0.3, y0 - h * 0.06, x0 + w * 0.7, y0 + h * 0.06], fill=color, outline=INK, width=6)
    line(d, [(cx, y0), (cx, y0 + h)], w=6)


def main():
    from coffee_story import story_frames
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "detergent_story")
    os.makedirs(out, exist_ok=True)
    frame, length = story_frames(1, "粉の黄金時代", "1987年4月 花王「アタック」発売。「スプーン1杯で驚きの白さ」。酵素入りの小型濃縮の粉",
                                 attack_scene_elements(), False)
    path = os.path.join(out, "scene_1987_attack.png")
    frame(length + 1).save(path)
    print(path)
    frame, length = story_frames(3, "アタックNeo", "2009年8月 花王「アタックNeo」発売。約2.5倍に濃縮・すすぎ1回でOK・400gで従来の液体1kg分",
                                 neo_scene_elements(), False)
    path = os.path.join(out, "scene_2009_attack_neo.png")
    frame(length + 1).save(path)
    print(path)
    frame, length = story_frames(3, "トップNANOX", "2010年1月 ライオン「トップNANOX」発売。においの元の皮脂汚れを落とす高濃度の液体",
                                 nanox_scene_elements(), False)
    path = os.path.join(out, "scene_2010_top_nanox.png")
    frame(length + 1).save(path)
    print(path)
    frame, length = story_frames(2, "服が変わる", "1995年 GAP上陸/1998年ごろ ユニクロのフリースが大ブーム/2003年 発熱する肌着/2008年 H&M 銀座に上陸",
                                 fashion_scene_elements(), False)
    path = os.path.join(out, "scene_fast_fashion.png")
    frame(length + 1).save(path)
    print(path)
    frame, length = story_frames(3, "第3の洗剤", "2014年 ジェルボールが登場。粉・液体に続く「第3の洗剤」(P&G「アリエール ジェルボール」など)",
                                 gel_scene_elements(), False)
    path = os.path.join(out, "scene_2014_gelball.png")
    frame(length + 1).save(path)
    print(path)


if __name__ == "__main__":
    main()
