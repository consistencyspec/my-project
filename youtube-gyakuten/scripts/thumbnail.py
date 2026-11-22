"""コーヒー10年戦争のサムネイル(3案)。1920x1080 で描いて 1280x720 に縮める。

  python3 scripts/thumbnail.py   -> output/thumbnails/thumb_A.png 〜 thumb_C.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, TRIM, WHITE, font, mug, stage  # noqa: E402
from motion import reverse_stamp, seats_motion  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "thumbnails")
DARK = (20, 26, 44)


def big(d, xy, s, size, fill, anchor="la", stroke=14):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=DARK)


def mixed(d, x, y, parts, size, anchor_center=False, stroke=14):
    f = font(size)
    total = sum(d.textlength(s, font=f) for s, _ in parts)
    if anchor_center:
        x -= total / 2
    for s, c in parts:
        d.text((x, y), s, font=f, fill=c, stroke_width=stroke, stroke_fill=DARK)
        x += d.textlength(s, font=f)


def band(d, y, h, s, color, size=64):
    d.rectangle([0, y, 1920, y + h], fill=color)
    d.text((960, y + h / 2), s, font=font(size), fill=WHITE, anchor="mm")


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    im.resize((1280, 720), Image.LANCZOS).save(path)
    return path


def thumb_a():
    """コーヒー、体にいい？悪い？(カップ+天秤つき議席)"""
    im, d = stage()
    mug(d, 110, 300, 700)
    big(d, (960, 170), "コーヒーは", 150, WHITE)
    mixed(d, 960, 360, [("体に", WHITE), ("いい", GOOD), ("？", WHITE)], 170)
    mixed(d, 960, 580, [("悪い", BAD), ("？", WHITE)], 190)
    band(d, 900, 140, "研究30年の「逆転劇」を議席で見る", (176, 38, 48), 70)
    return save(im, "thumb_A.png")


def thumb_b():
    """議席と「逆転！」が主役"""
    im, d = stage()
    seats_motion(d, 960, 860, 640, 53, 53, 1.0)
    reverse_stamp(d, 960, 470, 190, 1.0)
    big(d, (960, 190), "コーヒー10年戦争", 130, WHITE, anchor="mm")
    mug(d, 80, 620, 330, steam=False)
    mug(d, 1510, 620, 330, steam=False)
    big(d, (230, 560), "いい派", 90, GOOD, anchor="mm")
    big(d, (1690, 560), "悪い派", 90, BAD, anchor="mm")
    return save(im, "thumb_B.png")


def thumb_c():
    """「発がん性」の正体はタバコだった?(意外性)"""
    im, d = stage()
    mug(d, 1330, 330, 520)
    d.rounded_rectangle([90, 150, 760, 290], radius=70, fill=BAD)
    d.text((425, 220), "WHOの「発がん性」", font=font(70), fill=WHITE, anchor="mm")
    big(d, (90, 340), "正体は", 160, WHITE)
    mixed(d, 90, 530, [("タバコ", GOOD), ("だった？", WHITE)], 180)
    band(d, 900, 140, "コーヒー論争30年 ── 新常識クロニクル", DARK, 64)
    return save(im, "thumb_C.png")


if __name__ == "__main__":
    for f in (thumb_a, thumb_b, thumb_c):
        print(f())
