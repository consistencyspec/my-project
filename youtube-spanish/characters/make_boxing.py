"""ボクシングの絵：トレーニング着のオラポン君（横向き）と、ジムのマノロ会長（横向き）。

使い方:
  python3 characters/make_boxing.py   → olapon/boxing/（構え・ジャブ・ストレート・ガッツポーズ・ポコッ）
                                         manolo/side.svg、manolo/preview.png
アニメにするのは anime/gym_training.py（この中の関数を使う）。

どちらも右向きで描く。会長は画面では左右反転して、オラポン君と向き合わせる。
縮尺は今までの絵と同じ（オラポン君の顔の円は半径70、地面は y=408）。
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_walk_side as ws  # noqa: E402

HERE = Path(__file__).resolve().parent
INK = ws.INK
S = ws.S
SKIN, RED, TEAL, YELLOW = ws.SKIN, ws.RED, ws.TEAL, ws.PONCHO
GROUND = 408
HIP = (150, 326)
LEG_LEN = 80


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def arm_path(shoulder, hand, bend, color, width=13, inner=7):
    """肩から手までの腕（ひじは bend だけ下に曲がる）。"""
    mx, my = (shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2 + bend
    d = f"M{shoulder[0]:.1f} {shoulder[1]:.1f} Q{mx:.1f} {my:.1f} {hand[0]:.1f} {hand[1]:.1f}"
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{inner}" stroke-linecap="round"/>')


# ================================================================ オラポン君（ボクサー）
# 手（グローブ）の位置：構え・のばした・ばんざい
O_SHOULDER = {"far": (146, 214), "near": (158, 220)}
O_GUARD = {"far": (234, 176), "near": (214, 204)}
O_PUNCH = {"far": (314, 206), "near": (318, 222)}
# 「やった！」のガッツポーズ（グローブを胸の前で上げる。大きな頭に腕が重ならないように）
O_UP = {"far": (262, 192), "near": (246, 212)}


def glove(c, shade=False, angle=0.0):
    x, y = c
    red = "#a81c30" if shade else RED
    return (f'<g transform="rotate({angle:.1f} {x:.1f} {y:.1f})" {S}>'
            f'<rect x="{x - 30:.1f}" y="{y - 11:.1f}" width="14" height="22" rx="4" fill="#fff"/>'
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="20" ry="18" fill="{red}"/>'
            f'<path d="M{x - 4:.1f} {y + 4:.1f} Q{x + 6:.1f} {y + 2:.1f} {x + 8:.1f} {y - 8:.1f}" fill="none" stroke-width="3"/>'
            f'<ellipse cx="{x - 6:.1f}" cy="{y - 8:.1f}" rx="6" ry="3" fill="#fff" opacity=".6" stroke="none"/>'
            f'</g>')


def box_leg(angle, shade):
    x, y = HIP
    skin = "#e5b48f" if shade else SKIN
    shoe = "#a81c30" if shade else RED
    return (f'<g transform="rotate({angle:.2f} {x} {y})"><g {S}>'
            f'<path d="M{x - 11} {y} L{x - 11} {y + 60} L{x + 11} {y + 60} L{x + 11} {y} Z" fill="{skin}"/>'
            f'<g transform="rotate({-angle:.2f} {x} {y + 64})">'
            f'<path d="M{x - 14} {y + 52} L{x + 12} {y + 52} L{x + 14} {y + 64} Q{x + 34} {y + 66} {x + 36} {y + 76} '
            f'Q{x + 36} {y + 82} {x + 28} {y + 82} L{x - 14} {y + 82} Z" fill="{shoe}"/>'
            f'<path d="M{x - 13} {y + 74} L{x + 34} {y + 74}" stroke="#fff" stroke-width="3"/>'
            f'</g></g></g>')


def box_torso():
    return (f'<g {S}>'
            # トランクス
            f'<path d="M102 266 Q150 280 198 266 L206 336 Q178 344 156 336 L150 318 L144 336 Q122 344 96 336 Z" fill="{TEAL}"/>'
            f'<path d="M102 272 Q150 286 198 272" fill="none" stroke="#fff" stroke-width="5"/>'
            # タンクトップ（ポンチョと同じしま）
            f'<path d="M116 198 Q150 186 186 198 L200 270 Q150 284 100 270 Z" fill="{YELLOW}"/>'
            f'<path d="M108 230 Q150 244 194 230" fill="none" stroke="{RED}" stroke-width="7"/>'
            f'<path d="M104 250 Q150 264 198 250" fill="none" stroke="{TEAL}" stroke-width="5"/>'
            f'</g>')


def olapon(lead=0.0, rear=0.0, up=0.0, mouth="normal", bounce=0.0, stars=0.0):
    """ボクサーのオラポン君（右向き）の中身（<svg> なし）。
    lead: ジャブ（奥の手）をのばす 0〜1、rear: ストレート（手前の手）0〜1、up: ガッツポーズ 0〜1。
    mouth: normal / strain（がんばる顔）/ open。stars: 頭のまわりの星（ポコッとたたかれた）。"""
    stance = 15
    drop = LEG_LEN * (1 - math.cos(math.radians(stance)))
    shift = 6 * lead + 12 * rear                 # 打つとき体が前に出る
    lean = 3 * lead + 6 * rear - 4 * up

    def hand(side, ext):
        g = O_GUARD[side]
        g = lerp(g, O_UP[side], up)
        return lerp(g, O_PUNCH[side], ext)

    def sh(side):
        x, y = O_SHOULDER[side]
        return (x + shift, y)

    far_h, near_h = hand("far", lead), hand("near", rear)
    far_h = (far_h[0] + shift * (1 - lead), far_h[1])
    near_h = (near_h[0] + shift * (1 - rear), near_h[1])
    upper = (f'<g transform="translate({shift:.1f} 0) rotate({lean:.1f} 150 326)">'
             f'{box_torso()}{ws.head(mouth)}</g>')
    star = ""
    if stars > 0:
        for k in range(3):
            a = stars * 6 + k * 2.1
            sx, sy = 150 + shift + 80 * math.cos(a), 40 + 18 * math.sin(a)
            star += (f'<path d="M{sx:.1f} {sy - 12:.1f} L{sx + 4:.1f} {sy - 4:.1f} L{sx + 12:.1f} {sy:.1f} L{sx + 4:.1f} {sy + 4:.1f} '
                     f'L{sx:.1f} {sy + 12:.1f} L{sx - 4:.1f} {sy + 4:.1f} L{sx - 12:.1f} {sy:.1f} L{sx - 4:.1f} {sy - 4:.1f} Z" '
                     f'fill="{YELLOW}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    body = (f'<g>{arm_path(sh("far"), far_h, 18 * (1 - lead), "#e5b48f")}{glove(far_h, True)}</g>'
            f'{box_leg(-stance, True)}{box_leg(stance, False)}'
            f'{upper}'
            f'<g>{arm_path(sh("near"), near_h, 20 * (1 - rear), SKIN)}{glove(near_h)}</g>'
            f'{star}')
    shadow = f'<ellipse cx="160" cy="{GROUND - 1}" rx="80" ry="8" fill="#000" opacity=".18"/>'
    return shadow + f'<g transform="translate(0 {drop - bounce:.2f})">{body}</g>'


# ================================================================ マノロ会長
M_SKIN = "#efc19c"
M_JACKET, M_PANTS, WHITE = "#2a9d8f", "#2f3b63", "#f7f4ec"
M_SHOULDER = {"far": (150, 226), "near": (162, 232)}
M_MITT = {"far": (250, 214), "near": (244, 244)}


def mitt(c, shade=False):
    x, y = c
    dark = "#2b2628" if shade else "#3b3536"
    return (f'<g {S}>'
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="15" ry="23" fill="{dark}"/>'
            f'<ellipse cx="{x + 5:.1f}" cy="{y:.1f}" rx="7" ry="12" fill="{RED}" stroke-width="3"/>'
            f'<circle cx="{x + 6:.1f}" cy="{y:.1f}" r="3" fill="#fff" stroke="none"/>'
            f'</g>')


def manolo_head(mouth="closed"):
    m_open = (f'<ellipse cx="210" cy="190" rx="10" ry="8" fill="#7a1f2e"/>' if mouth == "open" else "")
    return (f'<g {S}>'
            # 後ろのふわふわの白髪
            f'<path d="M104 120 Q86 128 92 146 Q80 158 94 172 Q88 188 108 192 Q116 200 128 194 L132 128 Z" fill="{WHITE}"/>'
            f'<circle cx="150" cy="150" r="58" fill="{M_SKIN}"/>'
            f'<path d="M110 112 Q150 96 190 110" fill="none" stroke-width="2.5"/>'
            f'<path d="M106 124 Q150 108 194 122" fill="none" stroke-width="2.5"/>'
            # 耳
            f'<ellipse cx="128" cy="156" rx="10" ry="13" fill="{M_SKIN}"/>'
            f'<path d="M130 150 Q123 156 130 162" fill="none" stroke-width="3"/>'
            # 白いもじゃもじゃのまゆ・きびしい目
            f'<path d="M166 124 q10 -14 30 -6 q-6 2 -6 8 q-6 -6 -12 -2 q-6 -4 -12 0 Z" fill="{WHITE}" stroke-width="3"/>'
            f'<ellipse cx="186" cy="142" rx="5" ry="6" fill="{INK}"/>'
            f'<path d="M174 134 L198 138" fill="none" stroke-width="5"/>'
            # 大きな丸い鼻
            f'<circle cx="206" cy="160" r="13" fill="#f0a07a"/>'
            f'{m_open}'
            # 白いカイゼルひげ
            f'<path d="M178 176 Q194 164 208 176 Q222 164 238 172 Q246 184 232 182 Q220 190 208 182 '
            f'Q194 192 182 186 Q168 186 178 176 Z" fill="{WHITE}" stroke-width="3"/>'
            f'</g>')


def manolo(mitt_far=None, mitt_near=None, recoil=0.0, mouth="closed", lean=0.0, near_bend=18):
    """マノロ会長（右向き）の中身。recoil: ミットを打たれて押される 0〜1。"""
    mf = mitt_far or M_MITT["far"]
    mn = mitt_near or M_MITT["near"]
    mf = (mf[0] - 14 * recoil, mf[1])
    mn = (mn[0] - 14 * recoil, mn[1])
    lean_all = lean - 4 * recoil
    legs = (f'<g {S}>'
            f'<path d="M126 326 L120 392 L144 392 L148 326 Z" fill="#253050"/>'
            f'<path d="M152 326 L160 392 L184 392 L176 326 Z" fill="{M_PANTS}"/>'
            f'<path d="M114 392 L146 392 Q150 400 148 408 L110 408 Q106 398 114 392 Z" fill="#ddd"/>'
            f'<path d="M156 392 L186 392 Q206 396 206 408 L154 408 Z" fill="#fff"/>'
            f'</g>')
    body = (f'<g {S}>'
            f'<path d="M112 216 Q150 202 188 216 Q224 252 216 300 Q204 334 150 336 Q102 334 94 300 Q90 252 112 216 Z" fill="{M_JACKET}"/>'
            f'<path d="M190 222 Q204 280 196 326" fill="none" stroke-width="3"/>'
            f'<path d="M98 300 Q150 316 214 296" fill="none" stroke="{WHITE}" stroke-width="6"/>'
            # 首のタオルと笛
            f'<path d="M124 212 Q156 228 190 212 Q192 226 186 232 Q156 244 120 226 Z" fill="{WHITE}"/>'
            f'<path d="M184 226 L198 262" fill="none" stroke="{RED}" stroke-width="3"/>'
            f'<rect x="192" y="260" width="16" height="10" rx="4" fill="{YELLOW}" stroke-width="3"/>'
            f'</g>')
    far_arm = arm_path(M_SHOULDER["far"], (mf[0] - 12, mf[1] + 6), 16, "#23857a", 15, 9) + mitt(mf, True)
    near_arm = (arm_path(M_SHOULDER["near"], (mn[0] - 12, mn[1] + 6), near_bend, M_JACKET, 15, 9)
                + f'<path d="M{M_SHOULDER["near"][0]} {M_SHOULDER["near"][1] + 6} L{(M_SHOULDER["near"][0] + mn[0]) / 2:.1f} {(M_SHOULDER["near"][1] + mn[1]) / 2 + 14:.1f}" '
                  f'stroke="{WHITE}" stroke-width="2.5" fill="none"/>'
                + mitt(mn))
    shadow = f'<ellipse cx="156" cy="{GROUND - 1}" rx="70" ry="8" fill="#000" opacity=".18"/>'
    return (shadow + f'<g transform="rotate({lean_all:.2f} 150 {GROUND})">'
            f'{far_arm}{legs}{body}{manolo_head(mouth)}{near_arm}</g>')


def svg(inner, view=(30, 28, 330, 392)):
    x, y, w, h = view
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{round(960 * w / 240)}" height="{round(960 * h / 240)}">\n{inner}\n</svg>\n')


def make():
    od = HERE / "olapon" / "boxing"
    od.mkdir(parents=True, exist_ok=True)
    poses = {"01_kamae": {}, "02_jab": {"lead": 1}, "03_straight": {"rear": 1, "mouth": "strain"},
             "04_guts": {"up": 1, "mouth": "open"}, "05_poko": {"mouth": "strain", "stars": 0.3}}
    for name, kw in poses.items():
        (od / f"{name}.svg").write_text(svg(olapon(**kw)), encoding="utf-8")
    md = HERE / "manolo"
    md.mkdir(parents=True, exist_ok=True)
    (md / "side.svg").write_text(svg(manolo(), (30, 28, 240, 392)), encoding="utf-8")
    (md / "side_shout.svg").write_text(svg(manolo(mouth="open"), (30, 28, 240, 392)), encoding="utf-8")
    print("olapon/boxing/ と manolo/ を作りました")
    return od, md


def previews(od, md):
    import io

    import cairosvg
    from PIL import Image, ImageDraw

    files = sorted(od.glob("*.svg"))
    ims = [Image.open(io.BytesIO(cairosvg.svg2png(url=str(f), output_width=440))).convert("RGBA") for f in files]
    sheet = Image.new("RGB", (440 * len(ims), ims[0].height + 30), "#fff8ec")
    d = ImageDraw.Draw(sheet)
    for i, (f, im) in enumerate(zip(files, ims)):
        sheet.paste(im, (440 * i, 30), im)
        d.text((440 * i + 12, 8), f.stem, fill=INK)
    sheet.save(od / "preview.png")
    ms = [Image.open(io.BytesIO(cairosvg.svg2png(url=str(md / n), output_width=420))).convert("RGBA")
          for n in ("side.svg", "side_shout.svg")]
    sheet = Image.new("RGB", (420 * 2, ms[0].height), "#fff8ec")
    for i, im in enumerate(ms):
        sheet.paste(im, (420 * i, 0), im)
    sheet.save(md / "preview.png")


if __name__ == "__main__":
    o, m = make()
    if "--preview" in sys.argv:
        previews(o, m)
