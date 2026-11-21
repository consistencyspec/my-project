"""オラポン一家の「家と庭」の背景（16:9、1920x1080）を SVG で作る。

使い方: python3 characters/scenes/make_house.py   → characters/scenes/house_garden.svg
キャラクターと同じ絵柄（濃い茶色の太い線 #2A1A12、同じ色の組み合わせ）にそろえている。
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "house_garden.svg"
INK = "#2a1a12"
W, H = 1920, 1080
rnd = random.Random(7)
parts = []


def add(s):
    parts.append(s)


def flower(x, y, r=11, color="#d7263d"):
    petals = "".join(
        f'<circle cx="{x + r * 0.7 * math.cos(a):.1f}" cy="{y + r * 0.7 * math.sin(a):.1f}" r="{r * 0.55:.1f}" fill="{color}"/>'
        for a in [i * 2 * math.pi / 5 for i in range(5)])
    return f'<g stroke="{INK}" stroke-width="2.5">{petals}<circle cx="{x}" cy="{y}" r="{r * 0.35:.1f}" fill="#f5b700"/></g>'


def leaf(x, y, ang, s=14, color="#5cb85c"):
    return (f'<path d="M{x} {y} q{s * 0.6} {-s * 0.5} {s} 0 q{-s * 0.4} {s * 0.5} {-s} 0 Z" fill="{color}" '
            f'stroke="{INK}" stroke-width="2.5" transform="rotate({ang} {x} {y})"/>')


def window(cx, top, w=150, h=190):
    x0, x1 = cx - w / 2, cx + w / 2
    s = f'<g stroke="{INK}" stroke-width="5" stroke-linejoin="round">'
    # よろい戸（青緑）
    s += f'<rect x="{x0 - 62}" y="{top + 20}" width="56" height="{h - 20}" rx="6" fill="#2a9d8f"/>'
    s += f'<rect x="{x1 + 6}" y="{top + 20}" width="56" height="{h - 20}" rx="6" fill="#2a9d8f"/>'
    for i in range(6):
        yy = top + 40 + i * (h - 40) / 6
        s += f'<path d="M{x0 - 54} {yy} L{x0 - 14} {yy} M{x1 + 14} {yy} L{x1 + 54} {yy}" stroke-width="3"/>'
    # アーチ窓
    s += f'<path d="M{x0} {top + h} L{x0} {top + w / 2} A{w / 2} {w / 2} 0 0 1 {x1} {top + w / 2} L{x1} {top + h} Z" fill="#cfeefa"/>'
    s += f'<path d="M{cx} {top} L{cx} {top + h} M{x0} {top + w / 2 + 30} L{x1} {top + w / 2 + 30}" stroke-width="4"/>'
    s += f'<path d="M{x0 + 22} {top + w / 2 + 6} q14 -34 40 -44" fill="none" stroke="#fff" stroke-width="6" opacity=".8"/>'
    # 花のプランター
    s += f'<rect x="{x0 - 16}" y="{top + h - 6}" width="{w + 32}" height="40" rx="6" fill="#c8553d"/>'
    s += '</g>'
    for i in range(7):
        fx = x0 - 6 + i * (w + 12) / 6
        s += leaf(fx - 8, top + h - 14, rnd.randint(-160, -20))
        s += flower(fx, top + h - 22 - rnd.randint(0, 14), 13, rnd.choice(["#d7263d", "#ff6f91", "#d7263d"]))
    return s


def pot(x, y):
    s = f'<g stroke="{INK}" stroke-width="4"><path d="M{x} {y - 70} L{x} {y - 10}" stroke-width="3"/>'
    s += f'<path d="M{x - 26} {y - 10} L{x + 26} {y - 10} L{x + 18} {y + 30} L{x - 18} {y + 30} Z" fill="#3d6fb6"/>'
    s += f'<path d="M{x - 22} {y + 6} L{x + 22} {y + 6}" stroke="#fff" stroke-width="4"/></g>'
    for i in range(3):
        s += leaf(x - 18 + i * 14, y - 14, rnd.randint(-170, -10), 16)
    for i in range(3):
        s += flower(x - 14 + i * 14, y - 24 - (i % 2) * 10, 10)
    return s


def build():
    # 空
    add('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#7fc8ec"/><stop offset="1" stop-color="#e3f6fd"/></linearGradient></defs>')
    add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    add(f'<g stroke="{INK}" stroke-width="5"><circle cx="1720" cy="150" r="78" fill="#f5b700"/></g>')
    for i in range(12):
        a = i * math.pi / 6
        add(f'<path d="M{1720 + 100 * math.cos(a):.0f} {150 + 100 * math.sin(a):.0f} L{1720 + 130 * math.cos(a):.0f} {150 + 130 * math.sin(a):.0f}" '
            f'stroke="#f5b700" stroke-width="10" stroke-linecap="round"/>')
    for cx, cy, sc in ((300, 170, 1.0), (980, 110, 0.8)):
        add(f'<g stroke="{INK}" stroke-width="5" fill="#fff" transform="translate({cx} {cy}) scale({sc})">'
            '<path d="M-110 30 Q-120 -10 -80 -14 Q-70 -60 -20 -50 Q10 -80 50 -50 Q100 -60 104 -10 Q130 0 116 30 Z"/></g>')
    # 遠くの丘
    add(f'<path d="M0 720 Q260 600 520 690 Q760 600 1040 680 Q1320 590 1600 670 Q1780 620 1920 660 L1920 1080 L0 1080 Z" fill="#9ccc80" stroke="{INK}" stroke-width="5"/>')
    # 庭の芝生
    add(f'<path d="M0 790 Q960 760 1920 790 L1920 1080 L0 1080 Z" fill="#7dbb5a" stroke="{INK}" stroke-width="5"/>')
    for i in range(40):
        x, y = rnd.randint(20, 1900), rnd.randint(830, 1060)
        add(f'<path d="M{x} {y} l-6 -14 M{x} {y} l0 -18 M{x} {y} l6 -14" stroke="#4f8f3a" stroke-width="4" stroke-linecap="round"/>')

    # 家の本体（白い漆喰の壁）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        '<rect x="520" y="380" width="880" height="430" fill="#fbf6ec"/>'
        '<path d="M520 780 L1400 780" stroke-width="4"/></g>')
    # ブーゲンビリア（左の壁をはう）
    for i in range(26):
        x = 530 + rnd.randint(0, 70)
        y = 400 + i * 14 + rnd.randint(-6, 6)
        add(leaf(x, y, rnd.randint(0, 360), 14))
        if i % 2 == 0:
            add(f'<circle cx="{x + 10}" cy="{y}" r="9" fill="#c2185b" stroke="{INK}" stroke-width="2.5"/>')
    # 屋根（テラコッタの瓦）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        '<rect x="1190" y="200" width="70" height="110" fill="#fbf6ec"/><rect x="1180" y="186" width="90" height="24" fill="#c8553d"/>'
        '<path d="M460 400 L620 250 L1300 250 L1460 400 Z" fill="#c8553d"/></g>')
    for i in range(1, 22):
        x0 = 460 + i * 1000 / 22
        x1 = 620 + i * 680 / 22
        add(f'<path d="M{x0:.0f} 400 L{x1:.0f} 250" stroke="#9e3c28" stroke-width="4"/>')
    for row in range(1, 4):
        y = 250 + row * 150 / 4
        xl = 620 - (y - 250) * 160 / 150
        xr = 1300 + (y - 250) * 160 / 150
        d = f"M{xl:.0f} {y:.0f}"
        n = 22
        for k in range(n):
            xa = xl + (xr - xl) * (k + 1) / n
            d += f" q{(xr - xl) / n / 2:.1f} 12 {(xr - xl) / n:.1f} 0"
        add(f'<path d="{d}" fill="none" stroke="#9e3c28" stroke-width="4"/>')
    add(f'<path d="M450 404 L1470 404" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>')

    # 窓（左右）
    add(window(720, 450))
    add(window(1200, 450))
    # 玄関（アーチのドア）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        '<path d="M870 812 L870 620 A90 90 0 0 1 1050 620 L1050 812 Z" fill="#f2e3c9"/>'
        '<path d="M888 812 L888 624 A72 72 0 0 1 1032 624 L1032 812 Z" fill="#8b5a2b"/>'
        '<path d="M960 552 L960 812" stroke-width="4"/>'
        '<path d="M906 660 L942 660 M978 660 L1014 660 M906 740 L942 740 M978 740 L1014 740" stroke="#6b4320" stroke-width="5"/>'
        '<circle cx="944" cy="712" r="7" fill="#f5b700"/><circle cx="976" cy="712" r="7" fill="#f5b700"/></g>')
    # 表札「Casa de Olapón」
    add(f'<g stroke="{INK}" stroke-width="5"><rect x="790" y="452" width="340" height="62" rx="12" fill="#f5b700"/>'
        f'<path d="M840 452 L852 422 M1080 452 L1068 422" stroke-width="4"/></g>')
    add(f'<text x="960" y="495" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" '
        f'font-size="32" fill="{INK}">Casa de Olapón</text>')
    # 壁にかけた青い植木鉢（アンダルシア風）
    for x in (640, 800, 1120, 1280):
        add(pot(x, 740))
    # 玄関から伸びるタイルの小道
    add(f'<path d="M880 812 L1040 812 L1180 1080 L740 1080 Z" fill="#e2a06a" stroke="{INK}" stroke-width="5"/>')
    for i in range(1, 6):
        y = 812 + i * 268 / 6
        xl = 880 - (y - 812) * 140 / 268
        xr = 1040 + (y - 812) * 140 / 268
        add(f'<path d="M{xl:.0f} {y:.0f} L{xr:.0f} {y:.0f}" stroke="#b9774a" stroke-width="4"/>')
    for t in (0.33, 0.66):
        add(f'<path d="M{880 + 160 * t:.0f} 812 L{740 + 440 * t:.0f} 1080" stroke="#b9774a" stroke-width="4"/>')

    # サボテン（左）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round" fill="#3f9b57">'
        '<rect x="230" y="560" width="70" height="300" rx="35"/>'
        '<path d="M230 700 L190 700 Q160 700 160 670 L160 600 Q160 580 180 580 Q200 580 200 600 L200 660 L230 660"/>'
        '<path d="M300 650 L340 650 Q370 650 370 620 L370 560 Q370 540 350 540 Q330 540 330 560 L330 610 L300 610"/></g>')
    for i in range(14):
        x, y = 240 + rnd.randint(0, 50), 580 + rnd.randint(0, 260)
        add(f'<path d="M{x} {y} l6 -4" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
    add(flower(265, 556, 14, "#ff6f91"))
    # アガベ（左下）
    for a in range(-80, 81, 20):
        add(f'<path d="M110 960 Q{110 + 70 * math.sin(math.radians(a)):.0f} {960 - 60:.0f} {110 + 130 * math.sin(math.radians(a)):.0f} {960 - 120 * math.cos(math.radians(a)):.0f} '
            f'Q{110 + 40 * math.sin(math.radians(a)):.0f} {930:.0f} 110 960 Z" fill="#6aa58a" stroke="{INK}" stroke-width="4"/>')
    # レモンの木（右）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        '<path d="M1640 870 L1650 640 Q1652 620 1664 640 L1676 870 Z" fill="#8b5a2b"/>'
        '<path d="M1530 640 Q1500 560 1560 520 Q1560 440 1650 440 Q1730 420 1770 490 Q1840 510 1820 590 Q1830 660 1750 670 Q1700 700 1640 670 Q1560 690 1530 640 Z" fill="#4f9a45"/></g>')
    for _ in range(12):
        x, y = rnd.randint(1560, 1790), rnd.randint(480, 650)
        add(f'<ellipse cx="{x}" cy="{y}" rx="13" ry="10" fill="#ffe14d" stroke="{INK}" stroke-width="3"/>')
    # ペロの犬小屋（右下）
    add(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        '<rect x="1430" y="860" width="230" height="170" fill="#f7e3c6"/>'
        '<path d="M1410 870 L1545 770 L1680 870 Z" fill="#d7263d"/>'
        '<path d="M1500 1030 L1500 955 A45 45 0 0 1 1590 955 L1590 1030 Z" fill="#2a1a12"/>'
        '<rect x="1490" y="880" width="110" height="38" rx="8" fill="#f5b700" stroke-width="4"/>'
        '<path d="M1430 950 L1660 950" stroke="#2a9d8f" stroke-width="6"/></g>')
    add(f'<text x="1545" y="909" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" '
        f'font-size="26" fill="{INK}">PERO</text>')
    add(f'<ellipse cx="1385" cy="1030" rx="34" ry="12" fill="#3d6fb6" stroke="{INK}" stroke-width="4"/>'
        f'<path d="M1360 1022 Q1385 1014 1410 1022" fill="none" stroke="#fff" stroke-width="3"/>')
    # 低い白い塀（両端）
    for x0, x1 in ((0, 200), (1740, 1920)):
        add(f'<rect x="{x0}" y="820" width="{x1 - x0}" height="70" fill="#fbf6ec" stroke="{INK}" stroke-width="5"/>'
            f'<rect x="{x0}" y="806" width="{x1 - x0}" height="18" fill="#c8553d" stroke="{INK}" stroke-width="5"/>')


def main():
    build()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
           + "\n".join(parts) + "\n</svg>\n")
    OUT.write_text(svg, encoding="utf-8")
    print("できました:", OUT)


if __name__ == "__main__":
    main()
