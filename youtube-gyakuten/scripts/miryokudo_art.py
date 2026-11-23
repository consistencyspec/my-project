"""魅力度ランキングの回のイラスト(丸みのある線画。線の太さをそろえ、色は少しだけ塗る)。

どれも (d, cx, cy, s) で、(cx, cy) が絵のまん中、s がだいたいの幅。
  .venv/bin/python scripts/miryokudo_art.py  -> output/miryokudo_story/art_preview.png(一覧)
"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import INK, LW, PANEL, SUB, WHITE, line, text  # noqa: E402

SEA = (120, 180, 230)
SEA_DARK = (70, 130, 200)
GRAY = (170, 174, 184)
GRAY_DARK = (120, 124, 136)
RED = (214, 60, 52)
GOLD = (232, 190, 92)
GREEN = (80, 170, 100)
PINE = (60, 130, 80)
SKIN = (250, 222, 196)
NAVY = (54, 64, 96)
SNOW = (255, 255, 255)
BROWN = (150, 100, 60)


def waves(d, x0, x1, y, amp, color=SEA_DARK, w=6):
    pts, n = [], 40
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y + math.sin(i / n * math.pi * 6) * amp))
    d.line(pts, fill=color, width=w, joint="curve")


# ---------- 長崎 ----------
def ryoma(d, cx, cy, s):
    """坂本龍馬ふうの人(まげ・はかま・ブーツ)。"""
    h = s * 1.4
    top = cy - h / 2
    hr = s * 0.2
    hx, hy = cx, top + hr + s * 0.05
    # まげ(後ろでしばった髪)
    d.rounded_rectangle([hx - hr * 0.25, hy - hr * 1.45, hx + hr * 0.25, hy - hr * 0.85], radius=8, fill=INK)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=SKIN, outline=INK, width=LW)
    # ぼさぼさの髪
    d.chord([hx - hr * 1.05, hy - hr * 1.1, hx + hr * 1.05, hy + hr * 0.6], 180, 360, fill=INK)
    for dx in (-0.35, 0.35):
        d.ellipse([hx + dx * hr - 5, hy + hr * 0.15 - 5, hx + dx * hr + 5, hy + hr * 0.15 + 5], fill=INK)
    # 着物(紺)と白いえり
    bt = hy + hr + s * 0.03
    bw = s * 0.36
    d.rounded_rectangle([cx - bw, bt, cx + bw, bt + h * 0.42], radius=bw * 0.5, fill=NAVY, outline=INK, width=LW)
    d.polygon([(cx - bw * 0.45, bt + 4), (cx, bt + h * 0.2), (cx + bw * 0.45, bt + 4)], fill=WHITE)
    d.line([(cx - bw * 0.45, bt + 4), (cx, bt + h * 0.2), (cx + bw * 0.45, bt + 4)], fill=INK, width=6)
    # ふところに手(懐手)
    d.ellipse([cx + bw * 0.05, bt + h * 0.2, cx + bw * 0.45, bt + h * 0.3], fill=SKIN, outline=INK, width=5)
    # はかま
    ht = bt + h * 0.38
    d.polygon([(cx - bw * 0.95, ht), (cx + bw * 0.95, ht), (cx + bw * 1.15, ht + h * 0.28), (cx - bw * 1.15, ht + h * 0.28)],
              fill=GRAY_DARK, outline=INK, width=LW)
    d.line([(cx, ht + 10), (cx, ht + h * 0.28)], fill=INK, width=5)
    # ブーツ
    by = ht + h * 0.28
    for dx in (-0.55, 0.15):
        d.rounded_rectangle([cx + dx * bw * 1.4, by - 4, cx + (dx + 0.45) * bw * 1.4, by + h * 0.1], radius=10, fill=BROWN,
                            outline=INK, width=6)


def gunkanjima(d, cx, cy, s):
    """海に浮かぶ軍艦島(船の形の島に、四角い建物がならぶ)。"""
    w = s
    base = cy + s * 0.12
    # 建物
    blds = [(-0.42, 0.22, 0.16), (-0.25, 0.35, 0.14), (-0.1, 0.28, 0.12), (0.03, 0.42, 0.15), (0.2, 0.3, 0.13),
            (0.33, 0.2, 0.1)]
    for x, hh, ww in blds:
        x0, x1 = cx + x * w, cx + (x + ww) * w
        y0 = base - hh * w
        d.rectangle([x0, y0, x1, base], fill=GRAY, outline=INK, width=5)
        for yy in range(int(y0 + 14), int(base - 8), 20):
            for xx in range(int(x0 + 10), int(x1 - 8), 18):
                d.rectangle([xx, yy, xx + 7, yy + 8], fill=GRAY_DARK)
    # 島(岸壁)
    d.polygon([(cx - w * 0.55, base), (cx + w * 0.5, base), (cx + w * 0.62, base - w * 0.06), (cx + w * 0.5, base + w * 0.12),
               (cx - w * 0.5, base + w * 0.12)], fill=GRAY_DARK, outline=INK, width=LW)
    # 海
    d.rounded_rectangle([cx - w * 0.7, base + w * 0.1, cx + w * 0.7, base + w * 0.28], radius=20, fill=SEA)
    waves(d, cx - w * 0.62, cx + w * 0.62, base + w * 0.19, 6)


def church(d, cx, cy, s):
    """十字架のある教会。"""
    w = s * 0.7
    base = cy + s * 0.45
    d.rectangle([cx - w / 2, base - w * 0.6, cx + w / 2, base], fill=PANEL, outline=INK, width=LW)
    d.polygon([(cx - w / 2 - 10, base - w * 0.6), (cx, base - w * 1.0), (cx + w / 2 + 10, base - w * 0.6)], fill=RED,
              outline=INK, width=LW)
    # 塔
    tw = w * 0.28
    d.rectangle([cx - tw / 2, base - w * 1.25, cx + tw / 2, base - w * 0.8], fill=PANEL, outline=INK, width=LW)
    d.polygon([(cx - tw / 2 - 8, base - w * 1.25), (cx, base - w * 1.5), (cx + tw / 2 + 8, base - w * 1.25)], fill=RED,
              outline=INK, width=6)
    line(d, [(cx, base - w * 1.5), (cx, base - w * 1.75)], INK, 8)
    line(d, [(cx - w * 0.08, base - w * 1.66), (cx + w * 0.08, base - w * 1.66)], INK, 8)
    # 丸窓とドア
    d.ellipse([cx - w * 0.1, base - w * 0.52, cx + w * 0.1, base - w * 0.32], fill=(150, 200, 240), outline=INK, width=5)
    d.rounded_rectangle([cx - w * 0.12, base - w * 0.25, cx + w * 0.12, base], radius=14, fill=BROWN, outline=INK, width=5)


# ---------- 新幹線 ----------
def shinkansen(d, cx, cy, s, top=(40, 90, 170), stripe=(196, 120, 70), body=(250, 248, 240)):
    """新幹線の横から見た絵。北陸=上が青・銅色の線、九州=赤い線など。"""
    w, h = s, s * 0.34
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    nose = w * 0.36
    pts = [(x0, y0 + h * 0.1), (x1 - nose, y0), (x1 - nose * 0.5, y0 + h * 0.25), (x1 - nose * 0.1, y0 + h * 0.62),
           (x1, y1 - h * 0.1), (x1 - 10, y1), (x0, y1)]
    d.polygon(pts, fill=body)
    # 上の色
    d.polygon([(x0, y0 + h * 0.1), (x1 - nose, y0), (x1 - nose * 0.55, y0 + h * 0.2), (x0, y0 + h * 0.36)], fill=top)
    # 線
    d.polygon([(x0, y0 + h * 0.4), (x1 - nose * 0.48, y0 + h * 0.24), (x1 - nose * 0.4, y0 + h * 0.32),
               (x0, y0 + h * 0.48)], fill=stripe)
    d.polygon(pts, outline=INK, width=LW)
    # 窓
    for i in range(7):
        x = x0 + w * 0.05 + i * w * 0.075
        d.rounded_rectangle([x, y0 + h * 0.55, x + w * 0.045, y0 + h * 0.72], radius=5, fill=(70, 90, 130))
    # 前の窓
    d.polygon([(x1 - nose * 0.9, y0 + h * 0.06), (x1 - nose * 0.55, y0 + h * 0.2), (x1 - nose * 0.75, y0 + h * 0.22)],
              fill=(70, 90, 130))
    # 線路
    line(d, [(x0 - 20, y1 + 16), (x1 + 20, y1 + 16)], INK, 6)
    for i in range(9):
        x = x0 + i * w / 8
        d.line([(x, y1 + 16), (x - 12, y1 + 30)], fill=SUB, width=5)


def hokuriku(d, cx, cy, s):
    shinkansen(d, cx, cy, s, top=(40, 90, 170), stripe=(196, 120, 70))


def kyushu(d, cx, cy, s):
    shinkansen(d, cx, cy, s, top=(250, 248, 240), stripe=RED)


# ---------- 石川 ----------
def kotoji(d, cx, cy, s):
    """兼六園の徽軫灯籠(足が2本の石灯籠)と池、松。"""
    base = cy + s * 0.35
    # 池
    d.ellipse([cx - s * 0.6, base - s * 0.08, cx + s * 0.55, base + s * 0.18], fill=SEA)
    waves(d, cx - s * 0.45, cx + s * 0.4, base + s * 0.05, 4, w=5)
    # 松
    px = cx + s * 0.38
    d.line([(px, base - s * 0.05), (px - s * 0.05, base - s * 0.6)], fill=BROWN, width=12)
    for dy, ww in ((-0.62, 0.22), (-0.45, 0.28), (-0.28, 0.3)):
        d.ellipse([px - s * ww, base + s * dy - s * 0.07, px + s * ww * 0.7, base + s * dy + s * 0.07], fill=PINE,
                  outline=INK, width=5)
    # 灯籠(長い足は池の中、短い足は岸の石の上)
    lx = cx - s * 0.12
    top_y = base - s * 0.55
    d.polygon([(lx - s * 0.3, top_y + s * 0.08), (lx, top_y - s * 0.06), (lx + s * 0.3, top_y + s * 0.08)], fill=GRAY,
              outline=INK, width=LW)
    d.rounded_rectangle([lx - s * 0.12, top_y + s * 0.08, lx + s * 0.12, top_y + s * 0.2], radius=6, fill=GRAY_DARK,
                        outline=INK, width=6)
    d.rectangle([lx - s * 0.22, top_y + s * 0.2, lx + s * 0.22, top_y + s * 0.25], fill=GRAY, outline=INK, width=6)
    line(d, [(lx - s * 0.15, top_y + s * 0.25), (lx - s * 0.2, base + s * 0.05)], INK, 12)
    line(d, [(lx + s * 0.15, top_y + s * 0.25), (lx + s * 0.18, base - s * 0.15)], INK, 12)
    d.ellipse([lx + s * 0.06, base - s * 0.2, lx + s * 0.32, base - s * 0.08], fill=GRAY, outline=INK, width=6)


# ---------- 奈良 ----------
def deer(d, cx, cy, s):
    """鹿。"""
    body = (200, 140, 80)
    bx0, by0, bx1, by1 = cx - s * 0.32, cy - s * 0.05, cx + s * 0.22, cy + s * 0.2
    for x in (bx0 + s * 0.06, bx0 + s * 0.16, bx1 - s * 0.16, bx1 - s * 0.06):
        line(d, [(x, by1 - 10), (x, cy + s * 0.45)], INK, 9)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=s * 0.12, fill=body, outline=INK, width=LW)
    for x, y in ((-0.18, 0.03), (-0.05, 0.09), (0.07, 0.03)):
        d.ellipse([cx + x * s - 6, cy + y * s - 6, cx + x * s + 6, cy + y * s + 6], fill=WHITE)
    # 首と頭
    d.polygon([(bx1 - s * 0.12, by0 + 10), (bx1 - s * 0.02, by0 - s * 0.25), (bx1 + s * 0.08, by0 - s * 0.22),
               (bx1, by0 + 20)], fill=body, outline=INK, width=6)
    hx, hy = bx1 + s * 0.06, by0 - s * 0.28
    d.ellipse([hx - s * 0.08, hy - s * 0.07, hx + s * 0.14, hy + s * 0.08], fill=body, outline=INK, width=LW)
    d.ellipse([hx + 2, hy - 8, hx + 14, hy + 4], fill=INK)
    # 角
    for sx in (-1, 1):
        ax = hx + sx * s * 0.03
        line(d, [(ax, hy - s * 0.06), (ax + sx * s * 0.06, hy - s * 0.22)], BROWN, 7)
        line(d, [(ax + sx * s * 0.035, hy - s * 0.14), (ax + sx * s * 0.1, hy - s * 0.17)], BROWN, 6)


def palace(d, cx, cy, s):
    """朱色の柱の宮殿(平城宮の大極殿ふう)。"""
    w = s
    base = cy + s * 0.25
    d.rectangle([cx - w * 0.5, base, cx + w * 0.5, base + s * 0.06], fill=GRAY, outline=INK, width=6)
    d.rectangle([cx - w * 0.4, base - s * 0.25, cx + w * 0.4, base], fill=PANEL, outline=INK, width=6)
    for i in range(7):
        x = cx - w * 0.36 + i * w * 0.12
        d.rectangle([x - 6, base - s * 0.25, x + 6, base], fill=RED)
    d.polygon([(cx - w * 0.55, base - s * 0.25), (cx - w * 0.3, base - s * 0.48), (cx + w * 0.3, base - s * 0.48),
               (cx + w * 0.55, base - s * 0.25)], fill=(70, 80, 90), outline=INK, width=LW)
    for sx in (-1, 1):
        d.ellipse([cx + sx * w * 0.3 - 10, base - s * 0.56, cx + sx * w * 0.3 + 10, base - s * 0.46], fill=GOLD,
                  outline=INK, width=4)


# ---------- 東京 ----------
def torch(d, cx, cy, s):
    """聖火のトーチ。"""
    d.polygon([(cx - s * 0.12, cy - s * 0.1), (cx + s * 0.12, cy - s * 0.1), (cx + s * 0.04, cy + s * 0.5),
               (cx - s * 0.04, cy + s * 0.5)], fill=GOLD, outline=INK, width=LW)
    d.rounded_rectangle([cx - s * 0.16, cy - s * 0.16, cx + s * 0.16, cy - s * 0.08], radius=6, fill=GRAY, outline=INK,
                        width=6)
    d.polygon([(cx - s * 0.14, cy - s * 0.17), (cx - s * 0.18, cy - s * 0.38), (cx - s * 0.06, cy - s * 0.3),
               (cx, cy - s * 0.55), (cx + s * 0.07, cy - s * 0.32), (cx + s * 0.17, cy - s * 0.4), (cx + s * 0.14, cy - s * 0.17)],
              fill=(250, 140, 40), outline=INK, width=6)
    d.polygon([(cx - s * 0.06, cy - s * 0.17), (cx, cy - s * 0.36), (cx + s * 0.06, cy - s * 0.17)], fill=(255, 220, 80))


def tower(d, cx, cy, s):
    """赤と白の電波塔(東京タワーふう)。"""
    h = s * 1.3
    base, top = cy + h / 2, cy - h / 2
    for i in range(6):
        y0 = top + h * (0.12 + i * 0.147)
        y1 = y0 + h * 0.147
        k0, k1 = (y0 - top) / h, (y1 - top) / h
        hw0, hw1 = s * 0.05 + s * 0.4 * k0 ** 1.6, s * 0.05 + s * 0.4 * k1 ** 1.6
        d.polygon([(cx - hw0, y0), (cx + hw0, y0), (cx + hw1, y1), (cx - hw1, y1)], fill=RED if i % 2 == 0 else WHITE,
                  outline=INK, width=5)
    line(d, [(cx, top), (cx, top + h * 0.12)], INK, 7)
    d.rectangle([cx - s * 0.16, top + h * 0.5, cx + s * 0.16, top + h * 0.55], fill=GRAY, outline=INK, width=5)


# ---------- 新型コロナ ----------
def virus(d, cx, cy, s, fill=(120, 190, 120)):
    r = s * 0.3
    for i in range(12):
        a = i / 12 * math.tau
        x0, y0 = cx + math.cos(a) * r, cy + math.sin(a) * r
        x1, y1 = cx + math.cos(a) * r * 1.45, cy + math.sin(a) * r * 1.45
        line(d, [(x0, y0), (x1, y1)], INK, 8)
        d.ellipse([x1 - s * 0.06, y1 - s * 0.06, x1 + s * 0.06, y1 + s * 0.06], fill=(220, 80, 80), outline=INK, width=5)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=INK, width=LW)
    for dx, dy, rr in ((-0.35, -0.2, 0.18), (0.3, 0.1, 0.14), (-0.05, 0.4, 0.12)):
        d.ellipse([cx + dx * r - rr * r, cy + dy * r - rr * r, cx + dx * r + rr * r, cy + dy * r + rr * r], fill=(90, 160, 90))


def mask(d, cx, cy, s):
    w, h = s * 0.7, s * 0.42
    for sx in (-1, 1):
        d.arc([cx + sx * w * 0.5 - s * 0.15, cy - h * 0.45, cx + sx * w * 0.5 + s * 0.15, cy + h * 0.45],
              -90 if sx > 0 else 90, 90 if sx > 0 else 270, fill=INK, width=6)
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h * 0.35, fill=WHITE, outline=INK, width=LW)
    for k in (-0.18, 0, 0.18):
        d.line([(cx - w * 0.38, cy + k * h), (cx + w * 0.38, cy + k * h)], fill=(200, 205, 215), width=5)


# ---------- 沖縄 ----------
def shuri(d, cx, cy, s, fire=False):
    """赤い城(首里城ふう)。fire=True で炎。"""
    w = s
    base = cy + s * 0.3
    d.rectangle([cx - w * 0.55, base, cx + w * 0.55, base + s * 0.08], fill=GRAY, outline=INK, width=6)
    d.rectangle([cx - w * 0.42, base - s * 0.3, cx + w * 0.42, base], fill=RED, outline=INK, width=LW)
    for i in range(5):
        x = cx - w * 0.32 + i * w * 0.16
        d.rectangle([x - w * 0.04, base - s * 0.22, x + w * 0.04, base - s * 0.04], fill=(140, 30, 30))
    d.polygon([(cx - w * 0.52, base - s * 0.3), (cx - w * 0.32, base - s * 0.45), (cx + w * 0.32, base - s * 0.45),
               (cx + w * 0.52, base - s * 0.3)], fill=RED, outline=INK, width=LW)
    d.polygon([(cx - w * 0.3, base - s * 0.45), (cx, base - s * 0.62), (cx + w * 0.3, base - s * 0.45)], fill=RED,
              outline=INK, width=LW)
    d.ellipse([cx - 14, base - s * 0.58, cx + 14, base - s * 0.5], fill=GOLD, outline=INK, width=4)
    if fire:
        for fx, fh in ((-0.3, 0.35), (0.05, 0.5), (0.35, 0.3)):
            x = cx + fx * w
            y = base - s * 0.5
            d.polygon([(x - s * 0.1, y + s * 0.1), (x - s * 0.06, y - fh * s * 0.5), (x, y - fh * s),
                       (x + s * 0.06, y - fh * s * 0.5), (x + s * 0.1, y + s * 0.1)], fill=(250, 140, 40), outline=INK, width=5)


# ---------- 静岡 ----------
def fuji(d, cx, cy, s):
    w = s
    base = cy + s * 0.3
    d.polygon([(cx - w * 0.55, base), (cx - w * 0.12, base - s * 0.5), (cx + w * 0.12, base - s * 0.5), (cx + w * 0.55, base)],
              fill=(90, 120, 190), outline=INK, width=LW)
    d.polygon([(cx - w * 0.12, base - s * 0.5), (cx + w * 0.12, base - s * 0.5), (cx + w * 0.24, base - s * 0.36),
               (cx + w * 0.12, base - s * 0.3), (cx, base - s * 0.37), (cx - w * 0.1, base - s * 0.29), (cx - w * 0.24, base - s * 0.36)],
              fill=SNOW, outline=INK, width=6)
    # 茶畑
    for i in range(3):
        y = base + s * 0.04 + i * s * 0.07
        d.rounded_rectangle([cx - w * 0.55 + i * 20, y, cx + w * 0.55 - i * 20, y + s * 0.05], radius=14, fill=GREEN,
                            outline=INK, width=4)


def kabuto(d, cx, cy, s):
    """かぶと(戦国武将)。"""
    d.chord([cx - s * 0.35, cy - s * 0.3, cx + s * 0.35, cy + s * 0.35], 180, 360, fill=NAVY, outline=INK, width=LW)
    # しころ(首を守る部分)
    for i in range(3):
        y = cy + s * 0.02 + i * s * 0.08
        hw = s * (0.38 + i * 0.05)
        d.rounded_rectangle([cx - hw, y, cx + hw, y + s * 0.08], radius=8, fill=NAVY, outline=INK, width=5)
    # 前立て(金の飾り)
    d.polygon([(cx, cy - s * 0.1), (cx - s * 0.32, cy - s * 0.5), (cx - s * 0.18, cy - s * 0.18)], fill=GOLD, outline=INK, width=5)
    d.polygon([(cx, cy - s * 0.1), (cx + s * 0.32, cy - s * 0.5), (cx + s * 0.18, cy - s * 0.18)], fill=GOLD, outline=INK, width=5)
    d.ellipse([cx - s * 0.07, cy - s * 0.17, cx + s * 0.07, cy - s * 0.03], fill=GOLD, outline=INK, width=5)


# ---------- 神奈川・兵庫 ----------
def ferris(d, cx, cy, s):
    """観覧車。"""
    r = s * 0.38
    line(d, [(cx, cy), (cx - r * 0.6, cy + r * 1.25)], INK, 9)
    line(d, [(cx, cy), (cx + r * 0.6, cy + r * 1.25)], INK, 9)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=LW)
    cols = [RED, GOLD, SEA_DARK, GREEN]
    for i in range(12):
        a = i / 12 * math.tau
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.line([(cx, cy), (x, y)], fill=SUB, width=3)
        d.rounded_rectangle([x - s * 0.045, y - s * 0.02, x + s * 0.045, y + s * 0.07], radius=6, fill=cols[i % 4],
                            outline=INK, width=4)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=INK)
    line(d, [(cx - r * 1.1, cy + r * 1.27), (cx + r * 1.1, cy + r * 1.27)], INK, 7)


def house(d, cx, cy, s):
    w = s * 0.6
    base = cy + s * 0.35
    d.rectangle([cx - w / 2, base - w * 0.6, cx + w / 2, base], fill=PANEL, outline=INK, width=LW)
    d.polygon([(cx - w / 2 - 20, base - w * 0.55), (cx, base - w * 1.05), (cx + w / 2 + 20, base - w * 0.55)], fill=(240, 128, 40),
              outline=INK, width=LW)
    d.rounded_rectangle([cx - w * 0.12, base - w * 0.32, cx + w * 0.12, base], radius=10, fill=BROWN, outline=INK, width=5)
    d.rectangle([cx + w * 0.2, base - w * 0.45, cx + w * 0.4, base - w * 0.25], fill=(150, 200, 240), outline=INK, width=5)


def medal(d, cx, cy, s, label="1位", color=GOLD):
    d.polygon([(cx - s * 0.2, cy - s * 0.5), (cx - s * 0.05, cy - s * 0.05), (cx + s * 0.05, cy - s * 0.05),
               (cx + s * 0.2, cy - s * 0.5)], fill=(62, 120, 220), outline=INK, width=6)
    r = s * 0.28
    d.ellipse([cx - r, cy - r * 0.2, cx + r, cy + r * 1.8], fill=color, outline=INK, width=LW)
    text(d, (cx, cy + r * 0.8), label, int(r * 0.75), INK, anchor="mm")


def ship(d, cx, cy, s):
    """船(フェリー)。"""
    w = s
    base = cy + s * 0.1
    d.rectangle([cx - w * 0.22, base - s * 0.3, cx + w * 0.18, base - s * 0.14], fill=PANEL, outline=INK, width=6)
    d.rectangle([cx + w * 0.02, base - s * 0.42, cx + w * 0.12, base - s * 0.3], fill=RED, outline=INK, width=6)
    for i in range(4):
        x = cx - w * 0.18 + i * w * 0.08
        d.ellipse([x, base - s * 0.26, x + s * 0.05, base - s * 0.2], fill=(70, 90, 130))
    d.polygon([(cx - w * 0.45, base - s * 0.14), (cx + w * 0.45, base - s * 0.14), (cx + w * 0.32, base + s * 0.05),
               (cx - w * 0.38, base + s * 0.05)], fill=(62, 120, 220), outline=INK, width=LW)
    d.rounded_rectangle([cx - w * 0.55, base + s * 0.02, cx + w * 0.55, base + s * 0.16], radius=16, fill=SEA)
    waves(d, cx - w * 0.5, cx + w * 0.5, base + s * 0.09, 5, w=5)


def expo_globe(d, cx, cy, s):
    """万博(地球と「EXPO」の帯)。"""
    r = s * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 226, 250), outline=INK, width=LW)
    d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], outline=INK, width=5)
    d.line([(cx - r, cy), (cx + r, cy)], fill=INK, width=5)
    d.polygon([(cx - r * 0.6, cy - r * 0.3), (cx - r * 0.1, cy - r * 0.55), (cx, cy - r * 0.1), (cx - r * 0.4, cy + r * 0.15)],
              fill=GREEN)
    d.polygon([(cx + r * 0.2, cy + r * 0.1), (cx + r * 0.65, cy - r * 0.05), (cx + r * 0.5, cy + r * 0.5)], fill=GREEN)
    d.rounded_rectangle([cx - r * 1.2, cy + r * 0.55, cx + r * 1.2, cy + r * 1.05], radius=20, fill=RED, outline=INK, width=6)
    text(d, (cx, cy + r * 0.8), "EXPO", int(r * 0.42), WHITE, anchor="mm")


def g20(d, cx, cy, s):
    """サミット(机と旗)。"""
    cols = [RED, (62, 120, 220), GREEN, GOLD, (150, 95, 200)]
    for i in range(5):
        x = cx - s * 0.4 + i * s * 0.2
        line(d, [(x, cy - s * 0.35), (x, cy + s * 0.05)], INK, 5)
        d.rectangle([x, cy - s * 0.35, x + s * 0.14, cy - s * 0.25], fill=cols[i], outline=INK, width=4)
    d.rounded_rectangle([cx - s * 0.55, cy + s * 0.05, cx + s * 0.55, cy + s * 0.18], radius=10, fill=BROWN, outline=INK,
                        width=6)
    text(d, (cx, cy + s * 0.33), "G20", int(s * 0.16), INK, anchor="mm")


# ---------- 長野 ----------
def alps(d, cx, cy, s):
    base = cy + s * 0.25
    for dx, hh, col in ((-0.3, 0.45, (110, 140, 190)), (0.25, 0.55, (90, 120, 180)), (0.0, 0.35, (130, 160, 200))):
        x = cx + dx * s
        d.polygon([(x - s * 0.35, base), (x, base - hh * s), (x + s * 0.35, base)], fill=col, outline=INK, width=LW)
        d.polygon([(x - s * 0.1, base - hh * s + s * 0.13), (x, base - hh * s), (x + s * 0.1, base - hh * s + s * 0.13),
                   (x, base - hh * s + s * 0.09)], fill=SNOW)
    # りんご
    ax, ay = cx + s * 0.42, base + s * 0.05
    d.ellipse([ax - s * 0.1, ay - s * 0.1, ax + s * 0.1, ay + s * 0.1], fill=RED, outline=INK, width=6)
    line(d, [(ax, ay - s * 0.1), (ax + 4, ay - s * 0.16)], INK, 5)


# ---------- 大河ドラマ ----------
def taiga(d, cx, cy, s, title):
    """テレビに大河ドラマの題名。"""
    d.rounded_rectangle([cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.35], radius=20, fill=(60, 72, 104), outline=INK,
                        width=LW)
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.31, cx + s * 0.5, cy + s * 0.26], radius=12, fill=(250, 244, 230))
    line(d, [(cx - s * 0.25, cy + s * 0.48), (cx + s * 0.25, cy + s * 0.48)], INK, LW)
    line(d, [(cx, cy + s * 0.36), (cx, cy + s * 0.48)], INK, LW)
    text(d, (cx, cy - s * 0.18), "大河ドラマ", int(s * 0.09), SUB, anchor="mm")
    fs = int(min(s * 0.2, s * 0.2 * (s * 0.85) / max(1, d.textlength(title, font=_font(int(s * 0.2))))))
    text(d, (cx, cy + s * 0.02), title, fs, INK, anchor="mm")


def _font(size):
    from frames import font
    return font(size)


ALL = [ryoma, gunkanjima, church, hokuriku, kyushu, kotoji, deer, palace, torch, tower, virus, mask,
       lambda d, x, y, s: shuri(d, x, y, s, fire=True), fuji, kabuto, ferris, house, medal, ship, expo_globe, g20, alps,
       lambda d, x, y, s: taiga(d, x, y, s, "龍馬伝")]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "miryokudo_story")
    os.makedirs(out, exist_ok=True)
    cols = 6
    im = Image.new("RGB", (cols * 330, ((len(ALL) + cols - 1) // cols) * 360), PANEL)
    d = ImageDraw.Draw(im)
    for i, f in enumerate(ALL):
        f(d, (i % cols) * 330 + 165, (i // cols) * 360 + 180, 240)
    im.save(os.path.join(out, "art_preview.png"))
    print(os.path.join(out, "art_preview.png"))
