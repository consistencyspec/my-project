"""赤ワインは体にいい？ のショート用の縦サムネイル(1080x1920)。卵のショート(egg_short.py の cover)と同じ組み方。

  .venv/bin/python scripts/wine_short_cover.py   -> output/thumbnails/wine_short.png
答え(最終結果)は出さない。「78議席あった いい派が…」で本編に誘う。
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, TRIM, WHITE, text  # noqa: E402
from egg_short import W, vstage  # noqa: E402
from egg_war import wine  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "thumbnails")


def cover(path):
    im = vstage()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 260), "新常識クロニクル", 64, TRIM, anchor="mm")
    text(d, (W / 2, 440), "赤ワインは", 150, WHITE, anchor="mm")
    text(d, (W / 2, 640), "体にいい？", 150, GOOD, anchor="mm")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    wine(ImageDraw.Draw(lay), W / 2, 760, 360, color=WHITE)
    im = im.convert("RGBA")
    im.alpha_composite(lay)
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    # 答えは出さずに「？」で誘う帯
    d.rounded_rectangle([90, 1210, W - 90, 1420], radius=40, fill=(220, 60, 60))
    text(d, (W / 2, 1270), "一時は78議席の圧勝", 64, WHITE, anchor="mm")
    text(d, (W / 2, 1365), "それが大逆転！？", 76, WHITE, anchor="mm")
    for cx, lab, c in ((W / 2 - 230, "いい派", GOOD), (W / 2 + 230, "悪い派", BAD)):
        d.rounded_rectangle([cx - 160, 1530, cx + 160, 1640], radius=55, fill=c)
        text(d, (cx, 1585), lab, 64, WHITE, anchor="mm")
    text(d, (W / 2, 1585), "vs", 60, TRIM, anchor="mm")
    im.save(path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(cover(os.path.join(OUT, "wine_short.png")))
