"""ボクシングジム「Gimnasio Manolo」の背景（1920x1080）を SVG で作る。

使い方: python3 characters/scenes/make_gym.py → characters/scenes/gym.svg と gym.png
- リングの中から見た図：手前はリングのマット、うしろにロープ、その向こうにジムの壁
- 壁にはジムの看板、スペイン語の標語「¡NUNCA TE RINDAS!」（決してあきらめるな）、サンドバッグ、時計、窓
- キャラクターと同じ絵柄（線 #2A1A12）
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
INK, RED, TEAL, YELLOW, CREAM = "#2a1a12", "#d7263d", "#2a9d8f", "#f5b700", "#fbf6ec"
S = f'stroke="{INK}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'


def gym():
    s = []
    # 壁と、腰の高さの板
    s.append(f'<rect x="0" y="0" width="1920" height="760" fill="#f1dfbf"/>')
    s.append(''.join(f'<path d="M{x} 0 L{x} 560" stroke="#e6cfa6" stroke-width="10"/>' for x in range(60, 1920, 160)))
    s.append(f'<rect x="-10" y="560" width="1940" height="200" fill="#8b5a2b" {S}/>')
    s.append(''.join(f'<path d="M{x} 566 L{x} 756" stroke="#734a22" stroke-width="5"/>' for x in range(40, 1920, 90)))
    # 窓（夕方前の光）
    s.append(f'<g {S}><rect x="1380" y="90" width="300" height="230" rx="10" fill="#bfe7f6"/>'
             f'<path d="M1530 90 L1530 320 M1380 205 L1680 205" fill="none"/>'
             f'<path d="M1410 180 l40 -60 M1560 290 l50 -70" stroke="#fff" stroke-width="10"/></g>')
    # ジムの看板
    s.append(f'<g {S}><rect x="560" y="70" width="800" height="150" rx="18" fill="{RED}"/>'
             f'<rect x="580" y="88" width="760" height="114" rx="12" fill="none" stroke="{YELLOW}" stroke-width="5"/></g>'
             f'<text x="960" y="170" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" '
             f'font-size="76" fill="#fff" stroke="{INK}" stroke-width="3" paint-order="stroke">GIMNASIO MANOLO</text>')
    # 標語
    s.append(f'<g {S}><path d="M640 262 L1280 262 L1260 300 L1280 338 L640 338 L660 300 Z" fill="{CREAM}"/></g>'
             f'<text x="960" y="316" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" '
             f'font-size="44" fill="{TEAL}">¡NUNCA TE RINDAS!</text>')
    # 時計
    s.append(f'<g {S}><circle cx="300" cy="150" r="70" fill="#fff"/>'
             f'<path d="M300 150 L300 102 M300 150 L336 168" fill="none" stroke-width="7"/>'
             f'<circle cx="300" cy="150" r="6" fill="{INK}"/></g>')
    # サンドバッグ（左）
    s.append(f'<g {S}><path d="M240 0 L240 300" fill="none" stroke-width="5"/>'
             f'<path d="M240 300 L200 330 M240 300 L280 330" fill="none" stroke-width="4"/>'
             f'<rect x="170" y="330" width="140" height="300" rx="50" fill="{RED}"/>'
             f'<path d="M172 390 L308 390 M172 570 L308 570" fill="none" stroke="{INK}" stroke-width="6"/>'
             f'<rect x="196" y="440" width="88" height="80" rx="12" fill="{YELLOW}"/></g>')
    # かべの試合ポスター（右）
    s.append(f'<g {S}><rect x="1720" y="340" width="150" height="200" rx="6" fill="{YELLOW}" transform="rotate(4 1795 440)"/></g>'
             f'<g transform="rotate(4 1795 440)"><circle cx="1795" cy="410" r="38" fill="{RED}" stroke="{INK}" stroke-width="5"/>'
             f'<text x="1795" y="500" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" font-size="30" fill="{INK}">¡PELEA!</text></g>')
    # ベンチと、タオル・水
    s.append(f'<g {S}><rect x="1380" y="500" width="300" height="34" rx="8" fill="#b77b45"/>'
             f'<path d="M1410 534 L1410 600 M1650 534 L1650 600" fill="none" stroke-width="10"/>'
             f'<rect x="1440" y="470" width="44" height="40" rx="6" fill="{TEAL}"/>'
             f'<path d="M1540 500 Q1560 470 1600 480 Q1610 500 1600 504 Z" fill="#fff"/></g>')
    # リングのマット（手前）
    s.append(f'<path d="M-10 760 L1930 760 L1930 1090 L-10 1090 Z" fill="#dfe8ee" {S}/>')
    s.append(f'<path d="M-10 1000 L1930 1000" stroke="#c7d3db" stroke-width="8"/>')
    # コーナーポストとロープ（うしろ）
    for x in (110, 1810):
        s.append(f'<g {S}><rect x="{x - 22}" y="420" width="44" height="360" rx="10" fill="#c9ccd2"/>'
                 f'<rect x="{x - 30}" y="410" width="60" height="40" rx="10" fill="{RED}"/></g>')
    for y, col in ((480, RED), (570, "#fff"), (660, TEAL)):
        s.append(f'<path d="M110 {y} Q960 {y + 14} 1810 {y}" fill="none" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>'
                 f'<path d="M110 {y} Q960 {y + 14} 1810 {y}" fill="none" stroke="{col}" stroke-width="9" stroke-linecap="round"/>')
    # 天井のライトの光
    s.append(f'<path d="M760 0 L1160 0 L1420 1080 L500 1080 Z" fill="#fff" opacity=".10"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">\n'
            + "\n".join(s) + "\n</svg>\n")


def main():
    (OUT / "gym.svg").write_text(gym(), encoding="utf-8")
    try:
        import cairosvg
        cairosvg.svg2png(url=str(OUT / "gym.svg"), write_to=str(OUT / "gym.png"), output_width=1920)
    except ImportError:
        pass
    print("できました: gym.svg, gym.png")


if __name__ == "__main__":
    main()
