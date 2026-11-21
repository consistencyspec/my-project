"""車を押して歩くオラポン君（横向き・右向き）を作る。

使い方:
  python3 characters/make_push.py          → characters/olapon/push/push_01..08.svg（押して歩く8コマ）
  python3 characters/make_push.py --demo   → output/anime/push_demo.mp4（田舎道…の代わりに家の前で車を押す見本）
                                             と olapon/push/preview.png

- 体（ポンチョから上）を前に傾け、両腕を前にのばして、車の後ろ（予備タイヤ）を押す
- 足は重そうに、ゆっくり大きく踏んばる（8コマを 8コマ/秒 → 1歩 0.5秒）
- 顔は「がんばる顔」（ぎゅっとつぶった目、結んだ口、飛び散る汗）
- 手の位置 HAND は全コマ同じ。車の押すところをそこに合わせて置けば、手が車から離れない
- 車は car/make_car.py の pushed=True（故障の×の目、タイヤが回る）
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_walk_side as ws  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "olapon" / "push"
FRAMES, FPS = 8, 8
SWING = 20            # 足の振り（度）。ふつうの歩きより少し小さく、ゆっくり
LEAN = 22             # 体の前かがみ（度）
BRACE = 12            # 踏んばるため、足を後ろに流す（度）
HEAD_BACK = 10        # 顔は前を見るよう、頭だけ少し起こす（度）
BOB = 2.5
HAND = (272, 262)     # 両手が車にふれる位置（オラポン君の単位）
VIEW = (40, 28, 270, 392)
STRIDE = 2 * ws.LEG_LEN * math.sin(math.radians(SWING))


def rot(p, center, deg):
    a = math.radians(deg)
    x, y = p[0] - center[0], p[1] - center[1]
    return (center[0] + x * math.cos(a) - y * math.sin(a), center[1] + x * math.sin(a) + y * math.cos(a))


def push_arm(shoulder, hand, shade):
    sx, sy = shoulder
    hx, hy = hand
    mx, my = (sx + hx) / 2, (sy + hy) / 2 + 6        # ひじが少し下がる
    sleeve = "#d9a000" if shade else ws.PONCHO
    skin = "#e5b48f" if shade else ws.SKIN
    d = f"M{sx:.1f} {sy:.1f} Q{mx:.1f} {my:.1f} {hx - 8:.1f} {hy:.1f}"
    return (f'<g {ws.S}>'
            f'<path d="{d}" fill="none" stroke-width="13"/>'
            f'<path d="{d}" fill="none" stroke="{sleeve}" stroke-width="7"/>'
            f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="10" ry="13" fill="{skin}"/>'
            f'<path d="M{hx + 4:.1f} {hy - 8:.1f} l0 16" fill="none" stroke-width="2"/>'
            f'</g>')


def frame(i):
    phi = 2 * math.pi * i / FRAMES
    s, c = math.sin(phi), math.cos(phi)
    a_near, a_far = BRACE - SWING * s, BRACE + SWING * s
    lift_near = 7 * max(0.0, c)
    lift_far = 7 * max(0.0, -c)
    # 地面についている（低い方の）足に合わせて体の高さを決める
    drop = ws.LEG_LEN * (1 - max(math.cos(math.radians(a_near)), math.cos(math.radians(a_far))))
    bob = BOB * abs(c)
    hx, hy = ws.HIP
    hip = (hx, hy - bob)

    def placed_leg(angle, lift, shade):
        return (f'<g transform="translate(0 {drop - bob - lift:.2f}) rotate({angle:.2f} {hx} {hy})">'
                f'{ws.leg(shade, -angle)}</g>')

    # 上半身（ポンチョ・頭）を、足のつけ根を中心に前へ傾ける
    neck = (150, 196)
    upper = (f'<g transform="translate(0 {drop - bob:.2f}) rotate({LEAN} {hx} {hy})">'
             f'{ws.body(-3 - 2 * abs(c))}'
             f'<g transform="rotate({-HEAD_BACK} {neck[0]} {neck[1]})">{ws.head("strain")}</g>'
             f'</g>')
    # 肩の位置（傾けたあと）
    shoulder_near = rot((158, 228), ws.HIP, LEAN)
    shoulder_near = (shoulder_near[0], shoulder_near[1] + drop - bob)
    shoulder_far = (shoulder_near[0] - 10, shoulder_near[1] - 2)
    hand_far = (HAND[0] - 4, HAND[1] - 12)
    shadow = f'<ellipse cx="170" cy="{ws.GROUND - 1}" rx="74" ry="7" fill="#000" opacity=".18"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEW[0]} {VIEW[1]} {VIEW[2]} {VIEW[3]}" '
            f'width="960" height="{round(960 * VIEW[3] / VIEW[2])}">\n'
            + shadow + push_arm(shoulder_far, hand_far, True)
            + placed_leg(a_far, lift_far, True) + placed_leg(a_near, lift_near, False)
            + upper + push_arm(shoulder_near, HAND, False) + '</svg>\n')


def make():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(FRAMES):
        p = OUT / f"push_{i + 1:02d}.svg"
        p.write_text(frame(i), encoding="utf-8")
        paths.append(p)
    print(f"olapon/push/: 押して歩く{FRAMES}コマを作りました（1歩 {STRIDE:.1f} 単位）")
    return paths


def demo(paths):
    import io
    import subprocess

    import cairosvg
    from PIL import Image, ImageDraw

    sys.path.insert(0, str(HERE / "car"))
    import make_car

    W, H, VFPS = 1920, 1080, 24
    bg = Image.open(HERE / "scenes" / "house_garden.png").convert("RGB").resize((W, H))
    k = 1.25                                  # オラポン君：1単位 = 1.25px
    ck = 1.3                                  # 車：1単位 = 1.3px
    ow = round(VIEW[2] * k)

    def png_file(path, width):
        return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=width))).convert("RGBA")

    def png_text(svg, width):
        return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=width))).convert("RGBA")

    frames = [png_file(p, ow) for p in paths]

    # 一覧
    pad = 30
    sheet = Image.new("RGB", (ow * 4, (frames[0].height + pad) * 2), "#fff8ec")
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(frames):
        x, y = (i % 4) * ow, (i // 4) * (im.height + pad) + pad
        sheet.paste(im, (x, y), im)
        d.text((x + 12, y - 24), f"{i + 1}", fill=ws.INK)
    sheet.save(OUT / "preview.png")

    ground_px = 1040
    car_vb_x, car_vb_w, car_ground = -40, 700, 372   # make_car の viewBox と、タイヤの接地点
    car_w = round(car_vb_w * ck)
    # 車の押すところ（予備タイヤの左はし）
    car_push = (58, 238)
    v = STRIDE * k / (FRAMES / 2) * FPS / VFPS       # px / 動画1フレーム

    out = HERE.parent / "output" / "anime" / "push_demo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(VFPS), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    x_ola = -260.0                                    # オラポン君の x=150 の画面位置
    n = 0
    total = int(14 * VFPS)
    while n < total:
        img = bg.copy()
        # 手の画面位置 → 車の位置
        hand_px = (x_ola + (HAND[0] - 150) * k, ground_px - (ws.GROUND - HAND[1]) * k)
        car_x = hand_px[0] - (car_push[0] - car_vb_x) * ck
        car_y = ground_px - car_ground * ck
        dist = (x_ola + 260) / ck                     # 車が進んだ距離（車の単位）
        car_img = png_text(make_car.car(pushed=True, wheel_turn=dist), car_w)
        img.paste(car_img, (int(car_x), int(car_y)), car_img)
        spr = frames[(n * FPS // VFPS) % FRAMES]
        img.paste(spr, (int(x_ola - (150 - VIEW[0]) * k), int(ground_px - (ws.GROUND - VIEW[1]) * k)), spr)
        ff.stdin.write(img.tobytes())
        x_ola += v
        n += 1
    ff.stdin.close()
    ff.wait()
    print(f"見本: {out}")


if __name__ == "__main__":
    ps = make()
    if "--demo" in sys.argv:
        demo(ps)
