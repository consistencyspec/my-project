"""キャラクターの「下半身」を作り、今ある上半身（表情）と重ねて全身にする。

使い方: python3 characters/make_bodies.py
  → characters/<名前>/body.svg（下半身）と、characters/<名前>/fullbody/<表情>.svg（全身）を作る

しくみ:
- 上半身（expressions/*.svg）は viewBox "30 28 240 236"（下は y=264 で切れている）
- 下半身（body.svg）は同じ横幅・同じ縮尺で、y=264 より少し上から足元まで描く
- 全身 = 下半身の上に、上半身を y=264 で切って重ねたもの。つなぎ目は上半身に隠れる
- 表情やオラポン君の口パクは、上半身をそのまま差し替えるだけで全身でも使える
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
INK = "#2a1a12"
S = f'stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'

# 上半身を切る高さ。オラポン君は、ポンチョの下のふちの線が角で見えてしまうので少し上で切る
CLIP = {"olapon": 258, "dolores": 264, "bebe": 264, "pero": 264}

# 各キャラクターの全身の高さ（viewBox の下端）
BOTTOM = {"olapon": 420, "dolores": 444, "bebe": 340, "pero": 368}


def fringe(x0, x1, y, n, length, color):
    step = (x1 - x0) / n
    return "".join(f'<path d="M{x0 + step * (i + 0.5):.1f} {y} l0 {length}" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
                   for i in range(n))


# オラポン君の足（左・右）とポンチョ。make_walk.py でも使う
OLAPON_LEG_L = f'''
  <g {S}>
    <path d="M118 330 L116 392 L142 392 L142 330 Z" fill="#5b6070"/>
    <path d="M110 392 Q112 380 128 380 L144 380 L146 404 Q120 410 98 402 Q96 394 110 392 Z" fill="#8b5a2b"/>
  </g>'''
OLAPON_LEG_R = f'''
  <g {S}>
    <path d="M158 330 L158 392 L184 392 L182 330 Z" fill="#5b6070"/>
    <path d="M156 380 L172 380 Q188 380 190 392 Q204 394 202 402 Q180 410 154 404 Z" fill="#8b5a2b"/>
  </g>'''
OLAPON_PONCHO = f'''
  <g {S}>
    <path d="M74.2 252 L225.8 252 L230.8 264 L244 334 Q150 352 56 334 L69.2 264 Z" fill="#f5b700" stroke="none"/>
    <path d="M74.2 252 L69.2 264 L56 334 Q150 352 244 334 L230.8 264 L225.8 252" fill="none"/>
    <path d="M64 300 Q150 318 236 300" fill="none" stroke="#d7263d" stroke-width="7"/>
    <path d="M60 318 Q150 336 240 318" fill="none" stroke="#2a9d8f" stroke-width="5"/>
  </g>
  {fringe(62, 238, 340, 16, 12, "#d7263d")}
'''


BODIES = {
    # オラポン君：長いポンチョの下から、短い足とブーツ（足とポンチョは歩くアニメでも使うので別に定義）
    "olapon": OLAPON_LEG_L + OLAPON_LEG_R + OLAPON_PONCHO,
    # ドローレス：ぽっちゃりの胴から、何段もの飾りのフラメンコスカート、赤いヒール、腰に手
    "dolores": f'''
  <g {S}>
    <path d="M236 226 Q268 250 262 276 Q258 296 232 300" fill="none" stroke-width="16"/>
    <path d="M236 226 Q268 250 262 276 Q258 296 232 300" fill="none" stroke="#f6c9a8" stroke-width="9"/>
    <circle cx="230" cy="300" r="11" fill="#f6c9a8"/>
    <path d="M120 430 L116 440 L140 440 L142 430 Z M160 430 L158 440 L184 440 L180 430 Z" fill="#d7263d"/>
    <path d="M62.5 250 L237.5 250 L237.5 264 Q250 300 236 318 Q150 330 64 318 Q50 300 62.5 264 Z" fill="#d7263d" stroke="none"/>
    <path d="M62.5 264 Q50 300 64 318 Q150 330 236 318 Q250 300 237.5 264" fill="none"/>
    <path d="M64 316 Q150 330 236 316 L254 364 Q150 380 46 364 Z" fill="#d7263d"/>
    <path d="M46 364 Q150 380 254 364 L268 404 Q150 422 32 404 Z" fill="#d7263d"/>
    <path d="M32 404 Q150 422 268 404 L272 424 Q150 444 28 424 Z" fill="#d7263d"/>
  </g>
  <g fill="none" stroke="{INK}" stroke-width="5">
    <path d="M46 364 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q8 6 8 0"/>
    <path d="M32 404 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q6 5 6 0"/>
    <path d="M28 424 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q10 8 20 0 q4 4 4 0"/>
  </g>
  <g fill="#fff" stroke="none">
    <circle cx="88" cy="262" r="6"/><circle cx="98" cy="262" r="6"/><circle cx="202" cy="262" r="6"/><circle cx="150" cy="264" r="6"/>
    <circle cx="128" cy="272" r="6"/><circle cx="172" cy="272" r="6"/><circle cx="212" cy="236" r="6"/><circle cx="88" cy="236" r="6"/>
    <circle cx="96" cy="292" r="6"/><circle cx="150" cy="298" r="6"/><circle cx="204" cy="292" r="6"/>
    <circle cx="80" cy="344" r="6"/><circle cx="120" cy="350" r="6"/><circle cx="180" cy="350" r="6"/><circle cx="220" cy="344" r="6"/>
    <circle cx="66" cy="388" r="6"/><circle cx="110" cy="394" r="6"/><circle cx="150" cy="396" r="6"/><circle cx="190" cy="394" r="6"/><circle cx="234" cy="388" r="6"/>
  </g>
''',
    # ベベ：おくるみが丸くまとまり、下から小さな足（くつした）
    "bebe": f'''
  <g {S}>
    <ellipse cx="136" cy="326" rx="11" ry="8" fill="#fff"/>
    <ellipse cx="164" cy="326" rx="11" ry="8" fill="#fff"/>
    <path d="M90.7 250 L209.3 250 L209.3 264 Q218 290 194 314 Q150 336 106 314 Q82 290 90.7 264 Z" fill="#f5b700" stroke="none"/>
    <path d="M90.7 264 Q82 290 106 314 Q150 336 194 314 Q218 290 209.3 264" fill="none"/>
    <path d="M96 286 Q150 302 204 286" fill="none" stroke="#d7263d" stroke-width="6"/>
    <path d="M100 302 Q150 318 200 302" fill="none" stroke="#2a9d8f" stroke-width="4"/>
    <path d="M182 250 Q190 284 168 316" fill="none" stroke-width="3"/>
  </g>
''',
    # ペロ：おすわりしたチワワ。前足、うしろ足のふくらみ、くるんとしたしっぽ
    "pero": f'''
  <g {S}>
    <path d="M214 316 Q256 300 250 262 Q246 240 232 246 Q240 262 236 280 Q230 298 206 300 Z" fill="#e9b97a"/>
    <ellipse cx="96" cy="326" rx="30" ry="34" fill="#e9b97a"/>
    <ellipse cx="204" cy="326" rx="30" ry="34" fill="#e9b97a"/>
    <path d="M92.8 250 L207.2 250 L207.2 264 Q216 300 196 340 Q150 352 104 340 Q84 300 92.8 264 Z" fill="#e9b97a" stroke="none"/>
    <path d="M92.8 264 Q84 300 104 340 Q150 352 196 340 Q216 300 207.2 264" fill="none"/>
    <path d="M124 252 L176 252 Q174 304 150 318 Q126 304 124 252 Z" fill="#f7e3c6" stroke="none"/>
    <rect x="114" y="296" width="24" height="58" rx="12" fill="#e9b97a"/>
    <rect x="162" y="296" width="24" height="58" rx="12" fill="#e9b97a"/>
    <ellipse cx="124" cy="356" rx="17" ry="9" fill="#f7e3c6"/>
    <ellipse cx="176" cy="356" rx="17" ry="9" fill="#f7e3c6"/>
    <path d="M118 352 l0 7 M126 352 l0 7 M170 352 l0 7 M178 352 l0 7" stroke-width="2.5"/>
    <ellipse cx="78" cy="352" rx="18" ry="9" fill="#f7e3c6"/>
    <ellipse cx="222" cy="352" rx="18" ry="9" fill="#f7e3c6"/>
  </g>
''',
}


def inner(svg_text):
    """SVG の中身（外側の <svg> タグを除いた部分）。"""
    body = re.sub(r"^.*?<svg[^>]*>", "", svg_text, count=1, flags=re.S)
    return re.sub(r"</svg>\s*$", "", body.strip(), flags=re.S)


def header(bottom):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="30 28 240 {bottom - 28}" width="960" height="{round(960 * (bottom - 28) / 240)}">\n')


def main():
    for who, body in BODIES.items():
        d = HERE / who
        (d / "body.svg").write_text(header(BOTTOM[who]) + body + "</svg>\n", encoding="utf-8")
        out = d / "fullbody"
        out.mkdir(exist_ok=True)
        for src in sorted((d / "expressions").glob("*.svg")):
            upper = inner(src.read_text(encoding="utf-8"))
            svg = (header(BOTTOM[who]) + body +
                   f'<clipPath id="upper"><rect x="30" y="28" width="240" height="{CLIP[who] - 28}"/></clipPath>\n'
                   f'<g clip-path="url(#upper)">\n{upper}\n</g>\n</svg>\n')
            (out / src.name).write_text(svg, encoding="utf-8")
        print(f"{who}: body.svg と fullbody/ を作りました")


if __name__ == "__main__":
    main()
