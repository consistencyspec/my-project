"""オラポン君の「歩く」アニメーション（正面向きの、よちよち歩き）を作る。

使い方:
  python3 characters/make_walk.py            → characters/olapon/walk/<表情>/walk_01..08.svg
  python3 characters/make_walk.py --demo     → output/anime/walk_demo.mp4（家の前を歩いて横切る見本）
                                               と characters/olapon/walk_preview.png（8コマの一覧）

しくみ（1歩 = 4コマ、左右で 8コマ = 1サイクル）:
- 上げる方の足は、少し外に開きながら持ち上がる。もう片方の足は地面についたまま
- 体（ポンチョ＋上半身）は、足が上がっている間ふわっと上がり、ついている足の方に少し傾く
- ポンチョのフリンジは、体の揺れより少し遅れて揺れる
- 12コマ/秒で再生すると、1歩 約0.33秒
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_bodies import (BOTTOM, CLIP, OLAPON_LEG_L, OLAPON_LEG_R, S, fringe,  # noqa: E402
                         header, inner)

HERE = Path(__file__).resolve().parent
OLAPON = HERE / "olapon"
FRAMES = 8
FPS = 12          # アニメのコマの速さ（動画が 24fps なら 1コマを 2回ずつ出す）
LIFT = 16         # 足を上げる高さ
SPLAY = 7         # 足を外に開く角度（度）
BOB = 6           # 体が上がる高さ
TILT = 3.5        # 体の傾き（度）

PONCHO_SHAPE = f'''
  <g {S}>
    <path d="M74.2 252 L225.8 252 L230.8 264 L244 334 Q150 352 56 334 L69.2 264 Z" fill="#f5b700" stroke="none"/>
    <path d="M74.2 252 L69.2 264 L56 334 Q150 352 244 334 L230.8 264 L225.8 252" fill="none"/>
    <path d="M64 300 Q150 318 236 300" fill="none" stroke="#d7263d" stroke-width="7"/>
    <path d="M60 318 Q150 336 240 318" fill="none" stroke="#2a9d8f" stroke-width="5"/>
  </g>'''


def pose(i):
    """i コマ目の動き。左足 → 右足 の順に上げる。"""
    t = i / FRAMES
    s = math.sin(2 * math.pi * t)
    lift_l = max(0.0, s)           # 0..1
    lift_r = max(0.0, -s)
    return {
        "lift_l": lift_l, "lift_r": lift_r,
        "bob": BOB * abs(s),
        # 左足を上げている間は右足に体重 → 右に傾く
        "tilt": TILT * (lift_l - lift_r),
        # フリンジは少し遅れて、体と反対に揺れる
        "sway": -3.0 * math.sin(2 * math.pi * t - 0.9),
    }


def frame_svg(i, upper):
    p = pose(i)
    leg_l = (f'<g transform="translate(0 {-LIFT * p["lift_l"]:.2f}) '
             f'rotate({SPLAY * p["lift_l"]:.2f} 130 330)">{OLAPON_LEG_L}</g>')
    leg_r = (f'<g transform="translate(0 {-LIFT * p["lift_r"]:.2f}) '
             f'rotate({-SPLAY * p["lift_r"]:.2f} 170 330)">{OLAPON_LEG_R}</g>')
    # 地面の影：体が上がると少し小さく
    shadow_rx = 70 - p["bob"] * 1.5
    shadow = f'<ellipse cx="150" cy="406" rx="{shadow_rx:.1f}" ry="7" fill="#000" opacity=".18"/>'
    fr = f'<g transform="translate({p["sway"]:.2f} 0)">{fringe(62, 238, 340, 16, 12, "#d7263d")}</g>'
    body = (f'<g transform="translate(0 {-p["bob"]:.2f}) rotate({p["tilt"]:.2f} 150 340)">'
            f'{PONCHO_SHAPE}{fr}'
            f'<clipPath id="upper"><rect x="30" y="28" width="240" height="{CLIP["olapon"] - 28}"/></clipPath>'
            f'<g clip-path="url(#upper)">\n{upper}\n</g></g>')
    # 足は体より後ろ（ポンチョの下に隠れる）
    return header(BOTTOM["olapon"] + 4) + shadow + leg_l + leg_r + body + "</svg>\n"


def make_frames():
    out_all = {}
    for src in sorted((OLAPON / "expressions").glob("*.svg")):
        upper = inner(src.read_text(encoding="utf-8"))
        out = OLAPON / "walk" / src.stem
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(FRAMES):
            p = out / f"walk_{i + 1:02d}.svg"
            p.write_text(frame_svg(i, upper), encoding="utf-8")
            paths.append(p)
        out_all[src.stem] = paths
    print(f"olapon/walk/: {len(out_all)}表情 × {FRAMES}コマ を作りました")
    return out_all


def demo(frames):
    """家の前を、左から右へ歩いて横切る見本動画と、8コマの一覧。"""
    import io
    import subprocess

    import cairosvg
    from PIL import Image, ImageDraw

    root = HERE.parent
    W, H, VFPS = 1920, 1080, 24
    bg_path = HERE / "scenes" / "house_garden.png"
    if not bg_path.exists():
        cairosvg.svg2png(url=str(HERE / "scenes" / "house_garden.svg"), write_to=str(bg_path), output_width=W)
    bg = Image.open(bg_path).convert("RGB").resize((W, H))

    def png(path, width):
        return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=width))).convert("RGBA")

    width = 420
    normal = [png(p, width) for p in frames["01_normal"]]
    doya = [png(p, width) for p in frames["02_doya"]]

    # 一覧（8コマ）
    sheet = Image.new("RGB", (normal[0].width * 4, normal[0].height * 2 + 60), "#fff8ec")
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(normal):
        x, y = (i % 4) * im.width, (i // 4) * (im.height + 30) + 30
        sheet.paste(im, (x, y), im)
        d.text((x + 12, y - 24), f"{i + 1}", fill="#2a1a12")
    sheet.save(OLAPON / "walk_preview.png")

    # 動画：6秒で横切る → 真ん中で止まって決め顔 → また歩いて出ていく
    out = root / "output" / "anime" / "walk_demo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(VFPS), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    ground = 1050
    still = png(OLAPON / "fullbody" / "02_doya.svg", width)
    plan = [("walk", 4.0, -width, W / 2 - width / 2), ("stop", 1.5, None, None),
            ("walk", 3.0, W / 2 - width / 2, W + 20)]
    n = 0
    for kind, sec, x0, x1 in plan:
        for k in range(int(sec * VFPS)):
            img = bg.copy()
            if kind == "walk":
                x = x0 + (x1 - x0) * k / (sec * VFPS)
                spr = (normal if x1 < W else doya)[(n * FPS // VFPS) % FRAMES]
                n += 1
            else:
                spr = still
            img.paste(spr, (int(x), ground - spr.height), spr)
            ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"見本: {out}")


if __name__ == "__main__":
    fr = make_frames()
    if "--demo" in sys.argv:
        demo(fr)
