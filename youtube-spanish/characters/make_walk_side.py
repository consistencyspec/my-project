"""オラポン君の「横向き」の絵と、横向きに歩くアニメーションを作る。

使い方:
  python3 characters/make_walk_side.py          → characters/olapon/side/side.svg（立ち姿・右向き）
                                                   characters/olapon/side/walk_01..08.svg（歩き8コマ・右向き）
  python3 characters/make_walk_side.py --demo   → output/anime/walk_side_demo.mp4 と olapon/side/preview.png

- 絵は右向き。左向きは画像を左右反転して使う（動画を作る側で反転する）
- 正面の絵と同じ縮尺（顔の円は半径70）なので、正面の絵と並べても大きさがそろう
- 歩き：足を前後に振り、前に出す足は少し持ち上げる。両足が開いたときに体が下がり、
  足がそろうときに上がる（足が地面から浮いたりめりこんだりしないよう計算）。
  腕は足と反対に振る。フリンジは後ろになびく
- 12コマ/秒で 1歩 約0.33秒。1歩で進む距離 STRIDE を使えば、すべらずに歩かせられる
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "olapon" / "side"
INK = "#2a1a12"
S = f'stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'
SKIN, PONCHO, RED, TEAL, PANTS, BOOT, HAT = "#f6c9a8", "#f5b700", "#d7263d", "#2a9d8f", "#5b6070", "#8b5a2b", "#e7c36a"

FRAMES, FPS = 8, 12
HIP = (150, 326)        # 足のつけ根（回転の中心）
LEG_LEN = 80            # つけ根から靴底まで
SWING = 24              # 足を振る角度（度）
FOOT_LIFT = 9           # 前に出す足を上げる高さ
ARM_SWING = 28          # 腕を振る角度（度）
LEAN = 3                # 前かがみ（度）
GROUND = 408            # 足を振っていないときの靴底の高さ
# 1歩で進む距離（顔の円の半径70 と同じ単位）
STRIDE = 2 * LEG_LEN * math.sin(math.radians(SWING))
VIEW = (30, 28, 240, 392)


def leg(shade=False, foot_angle=0.0):
    """右向きの足1本（つけ根が HIP）。shade=True は奥の足（少し暗く）。
    foot_angle で靴を足首のところで回す（足を振っても靴底が地面と平らになるように）。"""
    pants = "#474b58" if shade else PANTS
    boot = "#6e4622" if shade else BOOT
    x, y = HIP
    return (f'<g {S}>'
            f'<path d="M{x - 12} {y} L{x - 12} {y + 66} L{x + 12} {y + 66} L{x + 12} {y} Z" fill="{pants}"/>'
            f'<g transform="rotate({foot_angle:.2f} {x} {y + 64})">'
            f'<path d="M{x - 16} {y + 62} Q{x - 14} {y + 54} {x} {y + 54} L{x + 14} {y + 56} '
            f'Q{x + 34} {y + 60} {x + 38} {y + 72} Q{x + 40} {y + 82} {x + 30} {y + 82} '
            f'L{x - 14} {y + 82} Q{x - 20} {y + 76} {x - 16} {y + 62} Z" fill="{boot}"/>'
            f'</g></g>')


def fringe(x0, x1, y0, y1, n, dx):
    """ポンチョのすそ（x0,y0 → x1,y1 の線にそって）から下がるフリンジ。dx だけ後ろになびく。"""
    out = []
    for i in range(n):
        t = (i + 0.5) / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        out.append(f'<path d="M{x:.1f} {y:.1f} l{dx:.1f} 12" stroke="{RED}" stroke-width="4" stroke-linecap="round"/>')
    return "".join(out)


def body(fringe_dx):
    """ポンチョ（横から見た形）。前（右）が少し短く、後ろが長い。"""
    return (f'<g {S}>'
            f'<path d="M190 196 L212 262 L222 330 Q150 350 74 336 L86 262 L110 196 Q150 184 190 196 Z" fill="{PONCHO}"/>'
            f'<path d="M98 228 Q150 242 202 226" fill="none" stroke="{RED}" stroke-width="7"/>'
            f'<path d="M92 248 Q150 262 208 246" fill="none" stroke="{TEAL}" stroke-width="5"/>'
            f'<path d="M80 300 Q150 316 218 298" fill="none" stroke="{RED}" stroke-width="7"/>'
            f'<path d="M78 318 Q150 334 220 316" fill="none" stroke="{TEAL}" stroke-width="5"/>'
            f'<path d="M192 196 L200 214 L196 222 Z" fill="{RED}" stroke-width="3"/>'
            f'</g>'
            f'{fringe(78, 220, 337, 331, 12, fringe_dx)}')


def head(mouth="normal"):
    """横向きの顔（右向き）。耳は円の中央より少し後ろ、目・鼻・くちびるは右側。"""
    lips = {
        "normal": (f'<ellipse cx="210" cy="172" rx="15" ry="11" fill="#e2627a"/>'
                   f'<path d="M198 173 Q211 176 224 171" fill="none" stroke-width="3"/>'
                   f'<ellipse cx="208" cy="166" rx="5" ry="2.2" fill="#fff" stroke="none" opacity=".9"/>'),
        # がんばる口（くちびるをぎゅっと結ぶ）
        "strain": (f'<path d="M197 172 Q210 164 223 171 Q211 182 197 172 Z" fill="#e2627a"/>'
                   f'<path d="M199 172 l5 -2 l5 3 l5 -3 l5 2" fill="none" stroke-width="2.5"/>'),
        "open": (f'<ellipse cx="210" cy="174" rx="14" ry="14" fill="#e2627a"/>'
                 f'<ellipse cx="213" cy="176" rx="7" ry="8" fill="#7a1f2e" stroke="none"/>'),
    }[mouth]
    if mouth == "strain":
        # ぎゅっとつぶった目（＞）と、つり上がったまゆ、飛び散る汗
        eyes = ('<path d="M176 104 L202 114" fill="none" stroke-width="6"/>'
                '<path d="M182 122 L198 132 L182 142" fill="none" stroke-width="5"/>'
                '<g fill="#8fd3f4" stroke-width="2.5">'
                '<path d="M104 96 q-8 10 0 14 q8 -4 0 -14 Z"/><path d="M90 120 q-7 9 0 12 q7 -3 0 -12 Z"/>'
                '<path d="M214 92 q-7 9 0 12 q7 -3 0 -12 Z"/></g>')
    else:
        eyes = ('<path d="M176 108 Q188 102 200 108" fill="none" stroke-width="6"/>'
                f'<ellipse cx="190" cy="132" rx="10" ry="14" fill="{INK}"/>'
                '<circle cx="193" cy="126" r="4" fill="#fff" stroke="none"/>')
    return (f'<g {S}>'
            # 後ろ頭の髪（正面の絵の横の髪と同じ色）
            f'<circle cx="150" cy="132" r="70" fill="{SKIN}"/>'
            f'<path d="M86 112 Q90 96 104 90" fill="none" stroke-width="7" stroke="#3b3536"/>'
            f'<path d="M84 140 Q84 120 92 108" fill="none" stroke-width="7" stroke="#3b3536"/>'
            f'<path d="M104 82 Q150 64 196 82 M100 92 Q148 74 194 90 M110 72 Q150 58 186 70" fill="none" stroke-width="2.5"/>'
            # 耳
            f'<ellipse cx="124" cy="138" rx="12" ry="16" fill="{SKIN}"/>'
            f'<path d="M126 130 Q118 138 126 146" fill="none" stroke-width="3"/>'
            # まゆ・目
            f'{eyes}'
            # 鼻（顔の輪郭から少し出る）
            f'<path d="M217 138 Q232 147 219 156" fill="{SKIN}" stroke-width="3.5"/>'
            # ほっぺ・ひげ
            f'<ellipse cx="180" cy="158" rx="13" ry="8" fill="#f2878a" opacity=".75" stroke="none"/>'
            f'<g fill="{INK}" opacity=".5" stroke="none"><circle cx="160" cy="188" r="1.6"/><circle cx="170" cy="191" r="1.6"/>'
            f'<circle cx="180" cy="189" r="1.6"/><circle cx="186" cy="183" r="1.6"/></g>'
            f'{lips}'
            f'</g>'
            # ソンブレロ（横から見ても同じ形。少し後ろに）
            f'<g stroke="{INK}" stroke-width="4" stroke-linejoin="round">'
            f'<ellipse cx="146" cy="66" rx="44" ry="8" fill="{HAT}"/>'
            f'<path d="M130 65 Q132 40 146 38 Q160 40 162 65 Z" fill="{HAT}"/>'
            f'<path d="M131 58 L161 58" stroke="{RED}" stroke-width="5"/>'
            f'</g>')


def arm(angle):
    """手前の腕。肩（150,226）から下にのび、angle 度だけ前後に振る。"""
    return (f'<g transform="rotate({angle:.2f} 150 226)" {S}>'
            f'<path d="M150 226 Q152 252 150 276" fill="none" stroke-width="13"/>'
            f'<path d="M150 226 Q152 252 150 276" fill="none" stroke="{PONCHO}" stroke-width="7"/>'
            f'<ellipse cx="150" cy="284" rx="12" ry="12" fill="{SKIN}"/>'
            f'</g>')


def header():
    x, y, w, h = VIEW
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="960" height="{round(960 * h / w)}">\n')


def frame(i, mouth="normal", walking=True):
    phi = 2 * math.pi * i / FRAMES
    s, c = (math.sin(phi), math.cos(phi)) if walking else (0.0, 0.0)
    a_near, a_far = -SWING * s, SWING * s              # マイナス = 足が前（右）
    # 前に向かって振っている足を持ち上げる
    lift_near = FOOT_LIFT * max(0.0, c) if walking else 0
    lift_far = FOOT_LIFT * max(0.0, -c) if walking else 0
    # 足を開くと靴底が上がる分、体を下げて地面につける
    drop = LEG_LEN * (1 - math.cos(math.radians(SWING * s)))
    hx, hy = HIP

    def placed_leg(angle, lift, shade):
        return (f'<g transform="translate(0 {-lift:.2f}) rotate({angle:.2f} {hx} {hy})">{leg(shade, -angle)}</g>')

    shadow = f'<ellipse cx="152" cy="{GROUND - 1}" rx="64" ry="7" fill="#000" opacity=".18"/>'
    fr_dx = -4 - 2 * abs(c) if walking else -1
    figure = (placed_leg(a_far, lift_far, True) + placed_leg(a_near, lift_near, False) +
              body(fr_dx) + head(mouth) + arm(ARM_SWING * s if walking else 4))
    lean = LEAN if walking else 0
    return (header() + shadow +
            f'<g transform="translate(0 {drop:.2f}) rotate({lean} 150 {GROUND})">{figure}</g></svg>\n')


def make():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "side.svg").write_text(frame(0, walking=False), encoding="utf-8")
    (OUT / "side_talk.svg").write_text(frame(0, "open", walking=False), encoding="utf-8")
    paths = []
    for i in range(FRAMES):
        p = OUT / f"walk_{i + 1:02d}.svg"
        p.write_text(frame(i), encoding="utf-8")
        paths.append(p)
    print(f"olapon/side/: 立ち姿2枚と歩き{FRAMES}コマを作りました（1歩 {STRIDE:.1f} 単位）")
    return paths


def demo(paths):
    """家の前を右へ歩く → 真ん中で正面を向いてドヤ顔 → 左向きに戻っていく。"""
    import io
    import subprocess

    import cairosvg
    from PIL import Image, ImageDraw, ImageOps

    W, H, VFPS = 1920, 1080, 24
    bg_path = HERE / "scenes" / "house_garden.png"
    if not bg_path.exists():
        cairosvg.svg2png(url=str(HERE / "scenes" / "house_garden.svg"), write_to=str(bg_path), output_width=W)
    bg = Image.open(bg_path).convert("RGB").resize((W, H))

    def png(path, width):
        return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=width))).convert("RGBA")

    width = 420                       # 240単位 → 420px
    k = width / VIEW[2]
    right = [png(p, width) for p in paths]
    left = [ImageOps.mirror(im) for im in right]
    stand = png(OUT / "side.svg", width)
    front = png(HERE / "olapon" / "fullbody" / "02_doya.svg", width)

    # 一覧
    pad = 30
    sheet = Image.new("RGB", (width * 5, right[0].height * 2 + pad * 2), "#fff8ec")
    d = ImageDraw.Draw(sheet)
    sheet.paste(stand, (0, pad), stand)
    d.text((12, 6), "standing", fill=INK)
    for i, im in enumerate(right):
        x, y = (1 + i % 4) * width, (i // 4) * (im.height + pad) + pad
        sheet.paste(im, (x, y), im)
        d.text((x + 12, y - 24), f"{i + 1}", fill=INK)
    sheet.save(OUT / "preview.png")

    # 1コマ（1/12秒）で進む距離：1歩（4コマ）で STRIDE
    speed = STRIDE * k / (FRAMES / 2) * FPS / VFPS      # px / 動画の1フレーム
    out = HERE.parent / "output" / "anime" / "walk_side_demo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(VFPS), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    ground_px = 1050
    foot_off = (GROUND - VIEW[1]) * k                  # 画像の上から靴底まで
    # キャラの中心（x=150単位）が画像の左から何pxか
    cx_off = (150 - VIEW[0]) * k

    def put(img, spr, cx, mirrored=False):
        off = (width - cx_off) if mirrored else cx_off
        img.paste(spr, (int(cx - off), int(ground_px - foot_off)), spr)

    def write(img):
        ff.stdin.write(img.tobytes())

    cx, n = -150.0, 0
    while cx < W / 2:                                 # 右へ歩く
        img = bg.copy(); put(img, right[(n * FPS // VFPS) % FRAMES], cx); write(img)
        cx += speed; n += 1
    for _ in range(6):                                # 立ち止まる
        img = bg.copy(); put(img, stand, cx); write(img)
    for _ in range(30):                               # 正面を向いてドヤ顔
        img = bg.copy(); put(img, front, cx); write(img)
    for _ in range(6):                                # 左を向く
        img = bg.copy(); put(img, ImageOps.mirror(stand), cx, True); write(img)
    n = 0
    while cx > -200:                                  # 左へ歩いて帰る
        img = bg.copy(); put(img, left[(n * FPS // VFPS) % FRAMES], cx, True); write(img)
        cx -= speed; n += 1
    ff.stdin.close()
    ff.wait()
    print(f"見本: {out}")


if __name__ == "__main__":
    ps = make()
    if "--demo" in sys.argv:
        demo(ps)
