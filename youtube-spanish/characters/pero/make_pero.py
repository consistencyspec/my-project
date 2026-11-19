"""ペロ（けむくじゃらのチワワ）の SVG を作る。毛の房はプログラムで少しずつ不ぞろいにして、自然に見せる。

使い方: python3 characters/pero/make_pero.py   → characters/pero/expressions/*.svg を作り直す
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "expressions"
INK, FUR, LIGHT, DARK, PINK = "#2a1a12", "#e9b97a", "#f7e3c6", "#c8955a", "#f2878a"


def tufts(cx, cy, rx, ry, a0, a1, n, depth, seed, inward=0.0):
    """楕円のふちに沿って、とがった毛の房をつなげた輪郭。a0〜a1 は角度（度）。"""
    rnd = random.Random(seed)
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        r = 1 - inward * rnd.random()
        pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ang = math.atan2(my - cy, mx - cx) + rnd.uniform(-0.25, 0.25)
        k = depth * rnd.uniform(0.7, 1.3)
        tx, ty = mx + k * math.cos(ang), my + k * math.sin(ang)
        d += f" Q{(x0 + tx) / 2:.1f} {(y0 + ty) / 2:.1f} {tx:.1f} {ty:.1f} Q{(x1 + tx) / 2:.1f} {(y1 + ty) / 2:.1f} {x1:.1f} {y1:.1f}"
    return d


def closed(d, cx, cy):
    return d + f" L{cx} {cy} Z"


def strands(cx, cy, rx, ry, a0, a1, n, length, seed):
    """毛並みの線（短い曲線）を、ふちの少し内側に並べる。"""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        t = math.radians(a0 + (a1 - a0) * (i + 0.5) / n + rnd.uniform(-4, 4))
        x, y = cx + rx * 0.82 * math.cos(t), cy + ry * 0.82 * math.sin(t)
        ex, ey = x + length * math.cos(t), y + length * math.sin(t)
        qx, qy = (x + ex) / 2 + 3 * math.sin(t), (y + ey) / 2 - 3 * math.cos(t)
        out.append(f"M{x:.1f} {y:.1f} Q{qx:.1f} {qy:.1f} {ex:.1f} {ey:.1f}")
    return " ".join(out)


def ear(side, seed):
    """長い飾り毛のついた「蝶の羽」のような耳。side=-1 左 / 1 右。"""
    s = side
    base = [(150 + s * 50, 112), (150 + s * 94, 38), (150 + s * 28, 92)]
    rnd = random.Random(seed)
    # 外側のふちに飾り毛（房）を並べる
    (x0, y0), (x1, y1) = base[0], base[1]
    d = f"M{x0} {y0}"
    n = 6
    for i in range(n):
        ax, ay = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        bx, by = x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (i + 1) / n
        nx, ny = -(by - ay), (bx - ax)
        L = math.hypot(nx, ny)
        k = rnd.uniform(14, 22)
        tx, ty = (ax + bx) / 2 - s * k * nx / L * -1, (ay + by) / 2 - s * k * ny / L * -1
        if s < 0:
            tx, ty = (ax + bx) / 2 - k * nx / L, (ay + by) / 2 - k * ny / L
        else:
            tx, ty = (ax + bx) / 2 + k * nx / L, (ay + by) / 2 + k * ny / L
        d += f" Q{tx:.1f} {ty:.1f} {bx:.1f} {by:.1f}"
    d += f" Q{150 + s * 60} {52} {base[2][0]} {base[2][1]} Z"
    inner = f"M{150 + s * 52} {102} L{150 + s * 84} {54} Q{150 + s * 56} {66} {150 + s * 36} {92} Z"
    return d, inner


def base_svg():
    eL, eLi = ear(-1, 1)
    eR, eRi = ear(1, 2)
    head = tufts(150, 142, 66, 58, 0, 360, 26, 14, 3, inward=0.06) + " Z"  # 一周しているので、そのまま閉じる
    # ほっぺの大きな飾り毛（左右に張り出す）
    ruff_l = tufts(108, 176, 44, 34, 95, 265, 7, 15, 11) + " L118 170 Z"
    ruff_r = tufts(192, 176, 44, 34, -85, 85, 7, 15, 12) + " L182 170 Z"
    chest = tufts(150, 240, 70, 46, 180, 360, 9, 10, 4)
    bib = closed(tufts(150, 232, 34, 30, 0, 180, 6, 8, 5), 150, 222)
    bangs = tufts(150, 104, 40, 18, 200, 340, 6, 12, 6) + " Q150 112 " + f"{150 - 40 * math.cos(math.radians(20)):.1f} {104 + 18 * math.sin(math.radians(200)):.1f} Z"
    beard_l = closed(tufts(124, 178, 18, 14, 90, 250, 4, 7, 7), 130, 172)
    beard_r = closed(tufts(176, 178, 18, 14, -70, 90, 4, 7, 8), 170, 172)
    fur = strands(150, 142, 66, 58, 0, 360, 34, 11, 9)
    return f'''<g id="body" stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
    <path d="{chest} L220 272 L80 272 Z" fill="{FUR}"/>
    <path d="{bib}" fill="{LIGHT}" stroke="none"/>
    <path d="M104 214 Q150 242 196 214 L150 258 Z" fill="#d7263d"/>
    <path d="M120 228 Q150 246 180 228" fill="none" stroke="#2a9d8f" stroke-width="5"/>
    <path d="{eL}" fill="{FUR}"/><path d="{eLi}" fill="{PINK}" stroke="none"/>
    <path d="{eR}" fill="{FUR}"/><path d="{eRi}" fill="{PINK}" stroke="none"/>
    <path d="{ruff_l}" fill="{FUR}"/>
    <path d="{ruff_r}" fill="{FUR}"/>
    <path d="{head}" fill="{FUR}"/>
    <path d="{fur}" fill="none" stroke="{DARK}" stroke-width="2.5"/>
    <path d="{bangs}" fill="{DARK}" stroke-width="3"/>
    <path d="{beard_l}" fill="{LIGHT}" stroke-width="3"/>
    <path d="{beard_r}" fill="{LIGHT}" stroke-width="3"/>
    <ellipse cx="150" cy="170" rx="31" ry="22" fill="{LIGHT}"/>
    <ellipse cx="150" cy="157" rx="9" ry="6" fill="{INK}"/>
    <ellipse cx="147" cy="155" rx="3" ry="1.5" fill="#fff" stroke="none"/>
  </g>'''


FACES = {
    "01_normal": '''
  <ellipse cx="120" cy="134" rx="15" ry="17" fill="#2a1a12"/>
  <ellipse cx="180" cy="134" rx="15" ry="17" fill="#2a1a12"/>
  <circle cx="115" cy="127" r="5" fill="#fff" stroke="none"/><circle cx="175" cy="127" r="5" fill="#fff" stroke="none"/>
  <circle cx="124" cy="141" r="2.5" fill="#fff" stroke="none"/><circle cx="184" cy="141" r="2.5" fill="#fff" stroke="none"/>
  <path d="M150 163 Q150 172 140 175 M150 163 Q150 172 160 175" fill="none" stroke-width="3"/>
''',
    "02_happy": '''
  <path d="M106 138 Q120 122 134 138 M166 138 Q180 122 194 138" fill="none" stroke-width="6"/>
  <path d="M136 172 Q150 182 164 172 Q160 192 150 192 Q140 192 136 172 Z" fill="#9e2b3a"/>
  <path d="M142 182 Q150 202 158 182 Z" fill="#f2878a" stroke-width="3"/>
  <path d="M150 163 L150 172" stroke-width="3"/>
  <path d="M236 92 l3 8 l8 3 l-8 3 l-3 8 l-3 -8 l-8 -3 l8 -3 Z M60 100 l2 6 l6 2 l-6 2 l-2 6 l-2 -6 l-6 -2 l6 -2 Z" fill="#f5b700" stroke-width="2.5"/>
''',
    "03_buruburu": '''
  <ellipse cx="120" cy="134" rx="16" ry="18" fill="#fff"/>
  <ellipse cx="180" cy="134" rx="16" ry="18" fill="#fff"/>
  <circle cx="120" cy="136" r="5" fill="#2a1a12" stroke="none"/><circle cx="180" cy="136" r="5" fill="#2a1a12" stroke="none"/>
  <path d="M138 176 q4 -4 8 0 q4 4 8 0 q4 -4 8 0" fill="none" stroke-width="3"/>
  <path d="M150 163 L150 170" stroke-width="3"/>
  <path d="M52 150 q-6 -6 0 -12 q6 -6 0 -12 M40 160 q-6 -6 0 -12 q6 -6 0 -12 M248 150 q6 -6 0 -12 q-6 -6 0 -12 M260 160 q6 -6 0 -12 q-6 -6 0 -12" fill="none" stroke-width="3"/>
  <path d="M214 112 Q220 122 214 128 Q208 122 214 112 Z" fill="#8fd3ff" stroke-width="2.5"/>
''',
}


def main():
    OUT.mkdir(exist_ok=True)
    body = base_svg()
    for name, face in FACES.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="30 28 240 236" width="960" height="944">
<defs>
  {body}
  <g id="cheeks" fill="{PINK}" opacity=".6" stroke="none"><ellipse cx="104" cy="164" rx="10" ry="6"/><ellipse cx="196" cy="164" rx="10" ry="6"/></g>
</defs>
<use xlink:href="#body"/><use xlink:href="#cheeks"/>
<g stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">{face}</g>
</svg>
'''
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
    print("できました:", ", ".join(FACES))


if __name__ == "__main__":
    main()
