"""オラポン一家のコミカルな車（横から見た図）を SVG で作る。

使い方: python3 characters/car/make_car.py   → characters/car/01_hashiru.svg（走る） / 02_enko.svg（故障）
キャラクターと同じ絵柄（濃い茶色の太い線 #2A1A12、同じ色の組み合わせ）。実在の車種はまねていない。
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
INK, YELLOW, RED, TEAL, STRAW, CREAM = "#2a1a12", "#f5b700", "#d7263d", "#2a9d8f", "#e7c36a", "#fbf6ec"
VB = "-40 0 700 420"


def wheel(cx, cy, r, hub, flat=False):
    if flat:  # パンクしたタイヤ：下がつぶれている
        tire = (f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy} L{cx + r + 6} {cy + r * 0.62} '
                f'Q{cx} {cy + r * 0.75} {cx - r - 6} {cy + r * 0.62} Z" fill="{INK}"/>')
    else:
        tire = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{INK}"/>'
    return (f'<g stroke="{INK}" stroke-width="6">{tire}'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.5}" fill="{hub}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.15}" fill="{INK}" stroke="none"/></g>')


def car(broken=False):
    s = []
    tilt = 'transform="rotate(-6 320 330)"' if broken else ""
    s.append(f'<g {tilt}>')
    # 排気ガスのけむり（後ろ）
    if not broken:
        for x, y, r in ((44, 300, 18), (20, 280, 24), (2, 252, 30)):
            s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#e6e6e6" stroke="{INK}" stroke-width="4"/>')
        s.append(f'<rect x="58" y="300" width="34" height="14" rx="5" fill="#888" stroke="{INK}" stroke-width="4"/>')
    # 予備タイヤ（後ろにしょっている）
    s.append(wheel(92, 238, 34, RED))
    # 車体（ずんぐりした丸い車）
    s.append(f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
             f'<path d="M96 318 Q78 318 80 290 Q84 240 140 222 Q190 140 330 136 Q440 136 486 214 '
             f'Q566 226 572 276 Q576 318 548 320 Z" fill="{YELLOW}"/></g>')
    # ポンチョ柄のしま
    s.append(f'<path d="M86 270 Q320 290 570 262" fill="none" stroke="{RED}" stroke-width="12"/>'
             f'<path d="M84 292 Q320 312 572 286" fill="none" stroke="{TEAL}" stroke-width="8"/>')
    # 窓（後ろと前）
    s.append(f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
             f'<path d="M166 222 Q206 162 300 158 L300 222 Z" fill="#cfeefa"/>'
             f'<path d="M322 158 Q414 160 452 222 L322 222 Z" fill="#cfeefa"/>'
             f'<path d="M190 210 q16 -30 40 -38 M348 210 q20 -28 46 -34" fill="none" stroke="#fff" stroke-width="7"/></g>')
    # ルームミラーのサイコロ
    s.append(f'<path d="M388 166 L388 186" stroke="{INK}" stroke-width="3"/>'
             f'<rect x="378" y="186" width="20" height="20" rx="4" fill="#fff" stroke="{INK}" stroke-width="3"/>'
             f'<circle cx="384" cy="192" r="2" fill="{INK}"/><circle cx="392" cy="200" r="2" fill="{INK}"/>')
    # ドアと花のステッカー
    s.append(f'<g stroke="{INK}" stroke-width="5" fill="none"><path d="M312 158 L312 312"/><path d="M300 236 L330 236" stroke-width="7"/></g>')
    for i, (dx, dy) in enumerate(((0, -12), (11, -4), (7, 10), (-7, 10), (-11, -4))):
        s.append(f'<circle cx="{236 + dx}" cy="{252 + dy}" r="9" fill="#ff6f91" stroke="{INK}" stroke-width="3"/>')
    s.append(f'<circle cx="236" cy="252" r="6" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>')
    # へこみと、ばんそうこう
    s.append(f'<path d="M150 252 q10 -8 20 0 q-10 8 -20 0" fill="none" stroke="{INK}" stroke-width="4"/>'
             f'<g transform="rotate(-25 456 252)"><rect x="430" y="244" width="52" height="16" rx="8" fill="#f6c9a8" stroke="{INK}" stroke-width="3"/>'
             f'<rect x="448" y="244" width="16" height="16" fill="#e8b48f" stroke="{INK}" stroke-width="3"/></g>')
    # トランクをしばったロープ
    s.append(f'<path d="M110 236 Q120 280 104 316 M120 232 Q134 280 120 318" fill="none" stroke="#b5835a" stroke-width="5"/>')
    # 前の顔：ヘッドライトの目と、ヒゲのバンパー
    if broken:
        s.append(f'<g stroke="{INK}" stroke-width="6"><circle cx="536" cy="252" r="22" fill="#fff"/>'
                 f'<path d="M524 240 L548 264 M548 240 L524 264" stroke-width="5"/></g>')
    else:
        s.append(f'<g stroke="{INK}" stroke-width="6"><circle cx="536" cy="252" r="22" fill="#fffbe0"/>'
                 f'<circle cx="542" cy="254" r="9" fill="{INK}" stroke="none"/><circle cx="538" cy="249" r="3.5" fill="#fff" stroke="none"/>'
                 f'<path d="M514 234 Q536 220 558 236" fill="none" stroke-width="5"/></g>')
    # 屋根にかぶった大きなソンブレロ
    s.append(f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
             f'<ellipse cx="320" cy="138" rx="206" ry="30" fill="{STRAW}"/>'
             f'<path d="M248 134 Q252 56 320 50 Q388 56 392 134 Z" fill="{STRAW}"/>'
             f'<path d="M252 116 Q320 128 388 116" fill="none" stroke="{RED}" stroke-width="13"/>'
             f'<path d="M262 132 l10 -10 l10 10 l10 -10 l10 10 l10 -10 l10 10 l10 -10 l10 10 l10 -10 l10 10 l10 -10 l10 10" fill="none" stroke="{TEAL}" stroke-width="4"/></g>')
    # アンテナと、てっぺんのトウガラシ
    s.append(f'<path d="M468 210 L500 96" stroke="{INK}" stroke-width="4"/>'
             f'<path d="M496 96 Q520 78 530 102 Q512 120 492 100 Z" fill="{RED}" stroke="{INK}" stroke-width="4"/>'
             f'<path d="M496 96 q-6 -8 2 -14" fill="none" stroke="#3f9b57" stroke-width="5"/>')
    # タイヤ（前は小さく、後ろは大きく。ふぞろい）
    s.append(wheel(176, 320, 52, "#2a9d8f"))
    s.append(wheel(470, 334, 36, "#d7263d", flat=broken))
    # ヒゲのバンパーと、ナンバープレート（タイヤより手前）
    s.append(f'<path d="M520 302 Q548 286 578 300 Q598 312 590 324 Q566 312 548 318 Q528 326 506 318 Q490 310 520 302 Z" '
             f'fill="#3b3536" stroke="{INK}" stroke-width="5"/>')
    s.append(f'<rect x="530" y="326" width="70" height="28" rx="5" fill="#fff" stroke="{INK}" stroke-width="4"/>'
             f'<text x="565" y="347" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" font-size="18" fill="{INK}">OLÉ</text>')
    s.append('</g>')
    # 走っている線 / 故障の湯気
    if broken:
        for x in (520, 556, 592):
            s.append(f'<path d="M{x} 210 q-14 -20 0 -40 q14 -20 0 -40" fill="none" stroke="#bbb" stroke-width="8" stroke-linecap="round"/>')
        s.append(f'<path d="M596 46 q9 1 10 -9 M620 46 q-9 1 -10 -9 M596 66 q9 -1 10 9 M620 66 q-9 -1 -10 9" fill="none" stroke="{RED}" stroke-width="6" stroke-linecap="round"/>')
    else:
        for y, x0, x1 in ((170, 600, 630), (220, 596, 634), (270, 604, 630)):
            s.append(f'<path d="M{x0} {y} L{x1} {y}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>')
    # 地面の影
    s.insert(0, f'<ellipse cx="330" cy="378" rx="270" ry="18" fill="{INK}" opacity=".15"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}" width="1400" height="840">\n' + "\n".join(s) + "\n</svg>\n"


def main():
    (OUT / "01_hashiru.svg").write_text(car(False), encoding="utf-8")
    (OUT / "02_enko.svg").write_text(car(True), encoding="utf-8")
    print("できました: 01_hashiru.svg, 02_enko.svg")


if __name__ == "__main__":
    main()
