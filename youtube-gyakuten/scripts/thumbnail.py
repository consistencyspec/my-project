"""新常識クロニクル：タイトル画面とサムネイルの共通テンプレート(全回この形で統一)。

形：舞台の背景/上に「新常識クロニクル」(金)/大きな題名(白)/副題(白)/2つの派のラベル(オレンジ vs 青)
動画のタイトル画面(1920x1080)とサムネイル(1280x720)は、同じ series_card() から作る。

  python3 scripts/thumbnail.py   -> output/thumbnails/coffee_war.png
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, TRIM, W, WHITE, font, stage, text  # noqa: E402

SERIES = "新常識クロニクル"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "thumbnails")


def series_card(title, subtitle, left="いい派", right="悪い派"):
    """1920x1080 のタイトル画面。題名・副題が長いときは自動で文字を小さくする。"""
    im, d = stage()
    text(d, (W / 2, 300), SERIES, 72, TRIM, anchor="mm")
    ts = int(min(170, 170 * 1640 / d.textlength(title, font=font(170))))
    text(d, (W / 2, 470), title, ts, WHITE, anchor="mm")
    ss = int(min(72, 72 * 1640 / d.textlength(subtitle, font=font(72))))
    text(d, (W / 2, 630), subtitle, ss, WHITE, anchor="mm")
    for cx, label, color in ((W / 2 - 230, left, GOOD), (W / 2 + 230, right, BAD)):
        lw = max(300, d.textlength(label, font=font(60)) + 80)
        d.rounded_rectangle([cx - lw / 2, 730, cx + lw / 2, 830], radius=50, fill=color)
        text(d, (cx, 780), label, 60, WHITE, anchor="mm")
    text(d, (W / 2, 780), "vs", 56, TRIM, anchor="mm")
    return im


def thumbnail(name, title, subtitle, left="いい派", right="悪い派"):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}.png")
    series_card(title, subtitle, left, right).resize((1280, 720), Image.LANCZOS).save(path)
    return path


# 回ごとの設定(新しい回はここに足す)
EPISODES = {
    "coffee_war": ("コーヒー10年戦争", "「いい派」vs「悪い派」論争の行方"),
    "egg_war": ("卵は1日1個まで？", "「いい派」vs「悪い派」論争の行方"),
    "wine_war": ("赤ワインは体にいい？", "「いい派」vs「悪い派」論争の行方"),
}

if __name__ == "__main__":
    for name, args in EPISODES.items():
        print(thumbnail(name, *args))
