"""赤ワインは体にいい？ のショート用の縦サムネイル(1080x1920)。卵のショート(egg_short.py の cover)と同じ組み方。

  .venv/bin/python scripts/wine_short_cover.py   -> output/thumbnails/wine_short.png
答え(最終結果)は出さない。「78議席あった いい派が…」で本編に誘う。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, CURTAIN, CURTAIN_DARK, GOOD, STAGE, STAGE_LIGHT, TRIM, WHITE, text  # noqa: E402
from egg_war import wine  # noqa: E402

W, H = 1080, 1920
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "thumbnails")


# egg_short を読み込むと卵の回の読み方の設定に変わるので、背景はここに写しておく(egg_short.vstage と同じ)
def vstage():
    """縦長の舞台(本編と同じ紺の舞台+赤い幕)。"""
    im = Image.new("RGB", (W, H), STAGE)
    light = Image.new("L", (W, H), 0)
    ImageDraw.Draw(light).ellipse([W * -0.1, H * 0.15, W * 1.1, H * 0.95], fill=255)
    light = light.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new("RGB", (W, H), STAGE_LIGHT), im, light)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 46], fill=CURTAIN)
    for x in range(0, W, 80):
        d.rectangle([x + 50, 0, x + 62, 46], fill=CURTAIN_DARK)
    for x in range(0, W + 80, 80):
        d.pieslice([x - 40, 6, x + 40, 86], 0, 180, fill=CURTAIN)
        d.arc([x - 40, 6, x + 40, 86], 0, 180, fill=TRIM, width=4)
    for x0 in (0, W - 30):
        d.rectangle([x0, 0, x0 + 30, H], fill=CURTAIN_DARK)
    return im


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
