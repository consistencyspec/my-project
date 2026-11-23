"""ドローレス（ベベを抱っこ）とペロの「横向き」の絵と、横向きに歩くアニメーションを作る。

使い方:
  python3 characters/make_walk_side_family.py         → dolores/side/（立ち姿・歩き8コマ）、pero/side/（立ち姿・歩き6コマ）
  python3 characters/make_walk_side_family.py --demo  → output/anime/walk_side_family_demo.mp4（一家で家の前を歩く見本）
                                                        と各 side/preview.png

- どちらも右向き。左向きは画像を左右反転して使う
- 縮尺は正面の絵と同じ。ペロとベベは、正面の一家の絵と同じく画面では小さめ（ペロ 0.55倍）に置く
- ドローレス：ぽっちゃりの体でゆさゆさ歩く。フラメンコスカートは歩くたびに揺れ、すそから赤いヒールがのぞく。
  ベベは胸の前で抱っこ（おしゃぶりはいつも）
- ペロ：チワワのちょこちょこ歩き（対角の足を一緒に出すトコトコ歩き）。しっぽを振り、耳がはずむ。
  6コマを 24コマ/秒で（オラポン君より速い足どり）
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_walk_side as olapon_side  # noqa: E402

HERE = Path(__file__).resolve().parent
INK = "#2a1a12"
S = f'stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'
SKIN, RED, TEAL, YELLOW, CREAM = "#f6c9a8", "#d7263d", "#2a9d8f", "#f5b700", "#fbf6ec"
DOG, DOG_LIGHT, DOG_SHADE, PINK = "#e9b97a", "#f7e3c6", "#c9965a", "#f2878a"


def header(view):
    x, y, w, h = view
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="960" height="{round(960 * h / w)}">\n')


def scallops(x0, y0, x1, y1, n, depth=7):
    """すその飾り（x0,y0 から x1,y1 まで、n 個の波）。"""
    d = f"M{x0:.1f} {y0:.1f}"
    for i in range(n):
        xa = x0 + (x1 - x0) * (i + 0.5) / n
        ya = y0 + (y1 - y0) * (i + 0.5) / n + depth
        xb = x0 + (x1 - x0) * (i + 1) / n
        yb = y0 + (y1 - y0) * (i + 1) / n
        d += f" Q{xa:.1f} {ya:.1f} {xb:.1f} {yb:.1f}"
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>'


# ---------------------------------------------------------------- ドローレス
D_VIEW = (26, 28, 252, 420)   # 抱っこしたベベが前に出るので、少し横に広い
D_GROUND = 442
D_FRAMES, D_FPS = 8, 12
# オラポン君と並んで歩けるよう、1歩の幅をそろえる（靴が前後に動く幅 = 1歩）
D_STEP = olapon_side.STRIDE / 2
D_SWAY = 2.5          # 体の左右の揺れ（度）
D_BOB = 3
D_SKIRT = 5           # スカートのすそが揺れる角度（度）


def d_shoe(fx, lift, shade):
    red = "#a81c30" if shade else RED
    y = D_GROUND - lift
    return (f'<g {S}>'
            f'<path d="M{fx - 13:.1f} {y - 2:.1f} L{fx - 13:.1f} {y - 12:.1f} Q{fx + 2:.1f} {y - 18:.1f} {fx + 16:.1f} {y - 9:.1f} '
            f'Q{fx + 20:.1f} {y - 4:.1f} {fx + 16:.1f} {y:.1f} L{fx - 2:.1f} {y:.1f} Z" fill="{red}"/>'
            f'<path d="M{fx - 13:.1f} {y - 4:.1f} L{fx - 11:.1f} {y + 1:.1f}" stroke-width="5"/>'
            f'</g>')


def d_skirt(angle):
    """3段のフラメンコスカート。後ろ（左）が長い。angle だけすそを揺らす。"""
    tiers = [
        ("M86 318 Q150 332 214 318 L236 362 Q150 378 62 366 Z", (62, 366, 236, 362), 9),
        ("M62 366 Q150 378 236 362 L248 400 Q150 418 42 406 Z", (42, 406, 248, 400), 11),
        ("M42 406 Q150 418 248 400 L252 416 Q150 438 30 426 Z", (30, 426, 252, 416), 12),
    ]
    parts = []
    for d, (x0, y0, x1, y1), n in tiers:
        parts.append(f'<path d="{d}" fill="{RED}" {S}/>')
        parts.append(scallops(x0, y0, x1, y1, n))
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#fff"/>' for x, y in
                   [(100, 344), (140, 350), (180, 348), (220, 342), (70, 388), (112, 394), (156, 396), (200, 392), (236, 384)])
    return (f'<g transform="translate(0 318) skewX({angle:.2f}) translate(0 -318)">'
            + "".join(parts) + dots + '</g>')


def d_bodice():
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#fff"/>' for x, y in
                   [(96, 236), (128, 252), (170, 248), (208, 246), (92, 286), (130, 296), (176, 300), (216, 290)])
    return (f'<path d="M108 200 Q160 190 196 208 Q236 240 234 286 Q232 314 210 324 L90 324 '
            f'Q70 300 74 260 Q78 214 108 200 Z" fill="{RED}" {S}/>' + dots +
            f'<path d="M110 212 Q150 230 196 214" fill="none" stroke="{INK}" stroke-width="5"/>')


def d_head():
    return (f'<g {S}>'
            # おだんごと、赤いくし（ペイネータ）
            f'<path d="M76 70 Q90 30 128 46 Q112 50 104 62 Z" fill="{RED}"/>'
            f'<circle cx="92" cy="94" r="24" fill="{INK}"/>'
            # 二重あご
            f'<path d="M136 192 Q186 222 214 186 Q200 210 160 210 Z" fill="{SKIN}"/>'
            f'<ellipse cx="150" cy="140" rx="66" ry="62" fill="{SKIN}"/>'
            # 髪（頭の上と後ろ）
            f'<path d="M86 172 Q66 102 118 80 Q168 64 206 96 Q214 106 212 118 Q190 102 160 104 '
            f'Q140 106 138 124 Q118 122 112 140 Q108 164 118 186 Q98 186 86 172 Z" fill="{INK}"/>'
            f'<path d="M150 72 Q160 84 158 104" fill="none" stroke="#5a4a40" stroke-width="2.5"/>'
            # 耳とイヤリング
            f'<ellipse cx="128" cy="146" rx="9" ry="13" fill="{SKIN}"/>'
            f'<circle cx="128" cy="174" r="11" fill="none" stroke="{YELLOW}" stroke-width="5"/>'
            # バラ
            f'<circle cx="198" cy="94" r="11" fill="{RED}"/><path d="M198 94 m-4 0 a4 4 0 1 1 4 4" fill="none" stroke-width="2"/>'
            f'<path d="M186 100 q-8 4 -6 12 q8 -2 6 -12 Z" fill="#5cb85c" stroke-width="2"/>'
            # まゆ・半目（いじわるそうな目）
            f'<path d="M176 112 Q192 100 208 112" fill="none"/>'
            f'<ellipse cx="192" cy="134" rx="11" ry="8" fill="#fff"/>'
            f'<circle cx="198" cy="136" r="5.5" fill="{INK}" stroke="none"/>'
            f'<path d="M178 130 L206 130" stroke-width="6"/>'
            f'<path d="M206 130 l6 -5 M202 128 l3 -7" stroke-width="2.5"/>'
            # 鼻・ほっぺ・くちびる・ほくろ
            f'<path d="M214 136 Q230 150 216 158" fill="{SKIN}" stroke-width="3.5"/>'
            f'<ellipse cx="180" cy="164" rx="14" ry="8" fill="{PINK}" opacity=".55" stroke="none"/>'
            f'<path d="M198 176 Q209 171 218 176 Q209 184 198 176 Z" fill="#b5172f" stroke-width="3"/>'
            f'<circle cx="204" cy="188" r="2.5" fill="{INK}" stroke="none"/>'
            f'</g>')


def d_baby():
    """抱っこされたベベ（おくるみ、顔はこちら向き、おしゃぶり）。"""
    return (f'<g {S}>'
            f'<g transform="rotate(-24 220 268)">'
            f'<ellipse cx="216" cy="268" rx="36" ry="24" fill="{YELLOW}"/>'
            f'<path d="M196 252 Q200 268 196 286" fill="none" stroke="{RED}" stroke-width="6"/>'
            f'<path d="M208 248 Q212 268 208 290" fill="none" stroke="{TEAL}" stroke-width="4"/>'
            f'</g>'
            f'<circle cx="244" cy="238" r="27" fill="{YELLOW}"/>'
            f'<circle cx="245" cy="240" r="21" fill="{CREAM}" stroke="none"/>'
            f'<circle cx="245" cy="241" r="18" fill="{SKIN}"/>'
            f'<path d="M245 224 Q240 218 244 215 Q249 213 249 218" fill="none" stroke-width="3"/>'
            f'<ellipse cx="238" cy="238" rx="3.5" ry="4.5" fill="{INK}" stroke="none"/>'
            f'<ellipse cx="252" cy="238" rx="3.5" ry="4.5" fill="{INK}" stroke="none"/>'
            f'<circle cx="237" cy="236.5" r="1.4" fill="#fff" stroke="none"/><circle cx="251" cy="236.5" r="1.4" fill="#fff" stroke="none"/>'
            f'<ellipse cx="233" cy="246" rx="5" ry="3" fill="{PINK}" opacity=".8" stroke="none"/>'
            f'<ellipse cx="257" cy="246" rx="5" ry="3" fill="{PINK}" opacity=".8" stroke="none"/>'
            f'<ellipse cx="245" cy="249" rx="8" ry="4.5" fill="{TEAL}" stroke-width="2.5"/>'
            f'<circle cx="245" cy="255" r="3.5" fill="none" stroke="{YELLOW}" stroke-width="2.5"/>'
            f'</g>')


def d_arm():
    """手前の腕：ふくらんだ袖から、ベベの下にまわして抱っこ。"""
    arm = "M162 236 Q168 286 198 292 Q222 294 242 276"
    return (f'<g {S}>'
            f'<path d="{arm}" fill="none" stroke-width="18"/>'
            f'<path d="{arm}" fill="none" stroke="{SKIN}" stroke-width="11"/>'
            f'<ellipse cx="244" cy="274" rx="11" ry="9" fill="{SKIN}"/>'
            f'<circle cx="160" cy="228" r="18" fill="{RED}"/>'
            f'<circle cx="154" cy="224" r="4.5" fill="#fff" stroke="none"/><circle cx="166" cy="234" r="4.5" fill="#fff" stroke="none"/>'
            f'</g>')


def dolores_frame(i, walking=True):
    phi = 2 * math.pi * i / D_FRAMES
    s, c = (math.sin(phi), math.cos(phi)) if walking else (0.0, 0.0)
    near_x = 150 + D_STEP * s + 6       # 手前の靴（地面についている間、1歩で STRIDE だけ後ろへ）
    far_x = 150 - D_STEP * s - 6        # 奥の靴
    # 前に向かって動いている靴を少し持ち上げる
    lift_near = 5 * max(0.0, c) if walking else 0
    lift_far = 5 * max(0.0, -c) if walking else 0
    bob = D_BOB * abs(c) if walking else 0
    sway = D_SWAY * s if walking else 0
    skirt = -D_SKIRT * c if walking else 0
    shadow = f'<ellipse cx="146" cy="{D_GROUND - 1}" rx="96" ry="8" fill="#000" opacity=".18"/>'
    upper = (f'<g transform="translate(0 {-bob:.2f}) rotate({sway:.2f} 150 {D_GROUND})">'
             f'{d_skirt(skirt)}{d_bodice()}{d_head()}{d_baby()}{d_arm()}</g>')
    return (header(D_VIEW) + shadow + d_shoe(far_x, lift_far, True) + d_shoe(near_x, lift_near, False)
            + upper + '</svg>\n')


# ---------------------------------------------------------------- ペロ
P_VIEW = (30, 28, 240, 340)
P_GROUND = 366
P_FRAMES = 6          # 6コマを 24コマ/秒で（1歩 3コマ）
P_HIPS = {"back": (112, 304), "front": (178, 304)}
P_LEG = 56            # つけ根から足の裏まで
P_SWING = 30
P_LIFT = 7
P_STRIDE = 2 * P_LEG * math.sin(math.radians(P_SWING))


def p_leg(hip, angle, lift, shade):
    x, y = hip
    fur = DOG_SHADE if shade else DOG
    return (f'<g transform="translate(0 {-lift:.2f}) rotate({angle:.2f} {x} {y})" {S}>'
            f'<rect x="{x - 8}" y="{y - 6}" width="16" height="{P_LEG - 2}" rx="8" fill="{fur}"/>'
            f'<ellipse cx="{x + 3}" cy="{y + P_LEG - 5}" rx="12" ry="7" fill="{DOG_LIGHT}"/>'
            f'</g>')


def p_body(tail, ear):
    return (f'<g {S}>'
            # しっぽ（くるん）
            f'<g transform="rotate({tail:.2f} 98 286)">'
            f'<path d="M100 292 Q62 278 70 240 Q76 222 92 230 Q80 246 90 262 Q96 274 108 278 Z" fill="{DOG}"/>'
            f'</g>'
            # 奥の耳
            f'<path d="M200 186 L222 118 Q236 156 220 190 Z" fill="{DOG_SHADE}"/>'
            # 胴体とおなか
            f'<ellipse cx="144" cy="292" rx="56" ry="32" fill="{DOG}"/>'
            f'<path d="M110 312 Q144 326 182 312 Q170 322 144 324 Q120 322 110 312 Z" fill="{DOG_LIGHT}" stroke="none"/>'
            f'</g>')


def p_head(ear):
    return (f'<g {S}>'
            # 首のバンダナ
            f'<path d="M160 252 Q190 276 214 254 L196 300 Z" fill="{RED}"/>'
            f'<path d="M168 262 Q190 280 208 264" fill="none" stroke="{TEAL}" stroke-width="5"/>'
            # 頭
            f'<ellipse cx="200" cy="222" rx="50" ry="46" fill="{DOG}"/>'
            # 手前の大きな耳
            f'<g transform="rotate({ear:.2f} 176 196)">'
            f'<path d="M166 200 L144 120 Q186 136 196 186 Z" fill="{DOG}"/>'
            f'<path d="M168 190 L154 134 Q182 148 188 182 Z" fill="{PINK}" stroke="none"/>'
            f'</g>'
            # おでこの白い筋・マズル・鼻
            f'<path d="M214 178 Q224 176 232 182 L234 214 Q226 220 220 214 Z" fill="{DOG_LIGHT}" stroke="none"/>'
            f'<ellipse cx="238" cy="242" rx="22" ry="16" fill="{DOG_LIGHT}"/>'
            f'<ellipse cx="256" cy="234" rx="7" ry="5.5" fill="{INK}"/>'
            f'<ellipse cx="254" cy="232" rx="2.5" ry="1.4" fill="#fff" stroke="none"/>'
            f'<path d="M254 242 Q252 252 240 254" fill="none" stroke-width="3"/>'
            # 目（大きくうるうる）
            f'<ellipse cx="212" cy="212" rx="13" ry="15" fill="{INK}"/>'
            f'<circle cx="215" cy="205" r="4.5" fill="#fff" stroke="none"/>'
            f'<circle cx="208" cy="218" r="2.2" fill="#fff" stroke="none"/>'
            f'<ellipse cx="206" cy="242" rx="9" ry="5.5" fill="{PINK}" opacity=".6" stroke="none"/>'
            f'</g>')


def pero_frame(i, walking=True):
    phi = 2 * math.pi * i / P_FRAMES
    s, c = (math.sin(phi), math.cos(phi)) if walking else (0.0, 0.0)
    a = P_SWING * s
    # 対角の足を一緒に出す（手前の前足と奥の後ろ足／奥の前足と手前の後ろ足）
    lift_a = P_LIFT * max(0.0, c) if walking else 0     # -a 側（前へ出ていく組）
    lift_b = P_LIFT * max(0.0, -c) if walking else 0
    drop = P_LEG * (1 - math.cos(math.radians(a)))
    tail = 14 * math.sin(2 * phi) if walking else 0
    ear = -4 * abs(c) if walking else 0
    legs_far = (p_leg(P_HIPS["back"], -a, lift_a, True) + p_leg(P_HIPS["front"], a, lift_b, True))
    legs_near = (p_leg(P_HIPS["back"], a, lift_b, False) + p_leg(P_HIPS["front"], -a, lift_a, False))
    shadow = f'<ellipse cx="150" cy="{P_GROUND - 1}" rx="74" ry="7" fill="#000" opacity=".18"/>'
    return (header(P_VIEW) + shadow +
            f'<g transform="translate(0 {drop:.2f})">{legs_far}{p_body(tail, ear)}{legs_near}{p_head(ear)}</g>'
            '</svg>\n')


# ---------------------------------------------------------------- 書き出し
def make():
    out = {}
    d = HERE / "dolores" / "side"
    d.mkdir(parents=True, exist_ok=True)
    (d / "side.svg").write_text(dolores_frame(0, walking=False), encoding="utf-8")
    out["dolores"] = []
    for i in range(D_FRAMES):
        p = d / f"walk_{i + 1:02d}.svg"
        p.write_text(dolores_frame(i), encoding="utf-8")
        out["dolores"].append(p)
    p_dir = HERE / "pero" / "side"
    p_dir.mkdir(parents=True, exist_ok=True)
    (p_dir / "side.svg").write_text(pero_frame(0, walking=False), encoding="utf-8")
    out["pero"] = []
    for i in range(P_FRAMES):
        p = p_dir / f"walk_{i + 1:02d}.svg"
        p.write_text(pero_frame(i), encoding="utf-8")
        out["pero"].append(p)
    print(f"dolores/side/: 立ち姿と歩き{D_FRAMES}コマ、pero/side/: 立ち姿と歩き{P_FRAMES}コマを作りました")
    return out


def demo(paths):
    import io
    import subprocess

    import cairosvg
    from PIL import Image, ImageDraw

    W, H, VFPS = 1920, 1080, 24
    bg_path = HERE / "scenes" / "house_garden.png"
    if not bg_path.exists():
        cairosvg.svg2png(url=str(HERE / "scenes" / "house_garden.svg"), write_to=str(bg_path), output_width=W)
    bg = Image.open(bg_path).convert("RGB").resize((W, H))

    def png(path, width):
        return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=width))).convert("RGBA")

    k = 1.75                                         # 1単位 = 1.75px（大人 240単位 = 420px）
    pk = k * 0.55                                    # ペロは小さめ
    adult_w, pero_w = round(240 * k), round(240 * pk)
    olapon = [png(p, adult_w) for p in sorted((HERE / "olapon" / "side").glob("walk_*.svg"))]
    dol_w = round(D_VIEW[2] * k)
    dolores = [png(p, dol_w) for p in paths["dolores"]]
    pero = [png(p, pero_w) for p in paths["pero"]]

    # 一覧（立ち姿＋歩き）
    for who, frames, w in (("dolores", dolores, dol_w), ("pero", [png(p, adult_w) for p in paths["pero"]], adult_w)):
        stand = png(HERE / who / "side" / "side.svg", w)
        cols = 5 if len(frames) == 8 else 4
        rows = math.ceil(len(frames) / (cols - 1))
        pad = 30
        sheet = Image.new("RGB", (w * cols, (stand.height + pad) * rows + pad), "#fff8ec")
        dr = ImageDraw.Draw(sheet)
        sheet.paste(stand, (0, pad), stand)
        dr.text((12, 6), "standing", fill=INK)
        for i, im in enumerate(frames):
            x, y = (1 + i % (cols - 1)) * w, (i // (cols - 1)) * (im.height + pad) + pad
            sheet.paste(im, (x, y), im)
            dr.text((x + 12, y - 24), f"{i + 1}", fill=INK)
        sheet.save(HERE / who / "side" / "preview.png")

    # 速さ（px / 動画1フレーム）。すべらないよう、1歩の幅から計算
    v_adult = olapon_side.STRIDE * k / (olapon_side.FRAMES / 2) * olapon_side.FPS / VFPS
    # ペロも同じ速さで進む。足がすべらないよう、コマを進める速さを合わせる（短い足でちょこちょこ）
    pero_rate = v_adult / (P_STRIDE * pk / (P_FRAMES / 2))

    out = HERE.parent / "output" / "anime" / "walk_side_family_demo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(VFPS), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    ground_px = 1050

    def put(img, spr, cx, view, ground, kk):
        x = cx - (150 - view[0]) * kk
        y = ground_px - (ground - view[1]) * kk
        img.paste(spr, (int(x), int(y)), spr)

    # 並び順：ペロが先頭、オラポン君、少し後ろにドローレス
    x_pero, x_ola, x_dol = -60.0, -400.0, -820.0
    n = 0
    while x_dol < W + 260:
        img = bg.copy()
        put(img, dolores[(n * D_FPS // VFPS) % D_FRAMES], x_dol, D_VIEW, D_GROUND, k)
        put(img, olapon[(n * olapon_side.FPS // VFPS) % olapon_side.FRAMES], x_ola,
            olapon_side.VIEW, olapon_side.GROUND, k)
        put(img, pero[int(n * pero_rate) % P_FRAMES], x_pero, P_VIEW, P_GROUND, pk)
        ff.stdin.write(img.tobytes())
        x_dol += v_adult
        x_ola += v_adult
        x_pero += v_adult
        n += 1
    ff.stdin.close()
    ff.wait()
    print(f"見本: {out}（{n / VFPS:.1f}秒）")


if __name__ == "__main__":
    ps = make()
    if "--demo" in sys.argv:
        demo(ps)
