#!/usr/bin/env python3
"""チャンネルアイコンの候補を作る（800x800。YouTube では丸く切り抜かれる）。

使い方: python3 scripts/make_icons.py   → branding/icon_a.png 〜 icon_c.png と、見え方の比較 branding/icons_preview.png
色はサムネイルとそろえている（赤 #D62027・黄 #FFD600）。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "branding"
N = 800
RED, YELLOW, WHITE, INK = (214, 32, 39), (255, 214, 0), (255, 255, 255), (25, 25, 25)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size):
    return ImageFont.truetype(BOLD, size)


def centered_text(d, text, f, cy, fill):
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text(((N - (r - l)) / 2 - l, cy - (b - t) / 2 - t), text, font=f, fill=fill)


def bubble(d, box, fill, tail_left=True):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=(y1 - y0) // 2.6, fill=fill)
    if tail_left:
        d.polygon([(x0 + 70, y1 - 20), (x0 + 30, y1 + 70), (x0 + 160, y1 - 20)], fill=fill)
    else:
        d.polygon([(x1 - 70, y1 - 20), (x1 - 30, y1 + 70), (x1 - 160, y1 - 20)], fill=fill)


def icon_a():
    """会話のへや：2つの吹き出し（会話）"""
    img = Image.new("RGB", (N, N), RED)
    d = ImageDraw.Draw(img)
    bubble(d, (120, 170, 560, 420), YELLOW, tail_left=True)
    bubble(d, (260, 380, 690, 620), WHITE, tail_left=False)
    f = font(110)
    l, t, r, b = d.textbbox((0, 0), "¡Hola!", font=f)
    d.text((340 - (r - l) / 2 - l, 295 - (b - t) / 2 - t), "¡Hola!", font=f, fill=INK)
    l, t, r, b = d.textbbox((0, 0), "ES", font=font(140))
    d.text((475 - (r - l) / 2 - l, 500 - (b - t) / 2 - t), "ES", font=font(140), fill=RED)
    return img


def icon_a2():
    """会話のへや（小さくても読める版）：吹き出し2つに、スペイン語らしい「¿?」と「¡!」"""
    img = Image.new("RGB", (N, N), RED)
    d = ImageDraw.Draw(img)
    bubble(d, (110, 150, 500, 420), YELLOW, tail_left=True)
    bubble(d, (300, 380, 690, 650), WHITE, tail_left=False)
    f = font(210)
    for text, cx, cy, fill in (("¿?", 305, 285, INK), ("¡!", 495, 515, RED)):
        l, t, r, b = d.textbbox((0, 0), text, font=f)
        d.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), text, font=f, fill=fill)
    return img


def banner(icon, path):
    """チャンネルのバナー（2560x1440）。スマホでも切れない中央（1546x423）に文字を入れる。"""
    from thumbnail import heavy_font
    W, H = 2560, 1440
    img = Image.new("RGB", (W, H), RED)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1040, W, H), fill=(190, 25, 32))  # 下の濃い帯は、スマホで見える範囲（中央）より下に置く
    sx, sy, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423
    ic = icon.resize((330, 330), Image.LANCZOS)
    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, N, N), fill=255)
    img.paste(ic, (sx + 20, sy + (sh - 330) // 2), mask.resize((330, 330)))
    tx = sx + 400
    right = sx + sw - 20  # スマホでも切れない範囲の右端

    def fit(text, size):
        while heavy_font(size).getlength(text) > right - tx and size > 30:
            size -= 2
        return heavy_font(size)

    d.text((tx, sy + 40), "スペイン語 会話のへや", font=fit("スペイン語 会話のへや", 118), fill=WHITE)
    sub = "会話を聞いて覚える 中級リスニング"
    fs = fit(sub, 62)
    d.rounded_rectangle((tx, sy + 225, tx + fs.getlength(sub) + 52, sy + 320), radius=18, fill=YELLOW)
    d.text((tx + 26, sy + 236), sub, font=fs, fill=INK)
    line = "毎週更新・和訳と単語付き・聞き流しにも"
    d.text((tx, sy + 345), line, font=fit(line, 48), fill=WHITE)
    img.save(path)


def icon_b():
    """聞きべや：ヘッドホン＋ES"""
    img = Image.new("RGB", (N, N), RED)
    d = ImageDraw.Draw(img)
    d.arc((170, 150, 630, 610), start=180, end=360, fill=WHITE, width=56)
    d.rounded_rectangle((130, 360, 260, 600), radius=50, fill=WHITE)
    d.rounded_rectangle((540, 360, 670, 600), radius=50, fill=WHITE)
    centered_text(d, "ES", font(190), 480, YELLOW)
    return img


def icon_c():
    """なんて言う？：スペイン語らしい「¿?」"""
    img = Image.new("RGB", (N, N), YELLOW)
    d = ImageDraw.Draw(img)
    d.ellipse((90, 90, 710, 710), fill=RED)
    centered_text(d, "¿?", font(380), 400, WHITE)
    return img


def preview(icons):
    """丸く切り抜いたときの見え方を、大・中・小（コメント欄くらい）で並べる。"""
    sizes = [240, 96, 40]
    w = sum(sizes) + 60 * len(sizes)
    sheet = Image.new("RGB", (w, len(icons) * 300), (245, 245, 245))
    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, N, N), fill=255)
    for row, ic in enumerate(icons):
        x = 30
        for s in sizes:
            small = ic.resize((s, s), Image.LANCZOS)
            sheet.paste(small, (x, row * 300 + (300 - s) // 2), mask.resize((s, s)))
            x += s + 60
    return sheet


def main():
    OUT.mkdir(exist_ok=True)
    icons = {"icon_a": icon_a(), "icon_a2": icon_a2(), "icon_b": icon_b(), "icon_c": icon_c()}
    for name, img in icons.items():
        img.save(OUT / f"{name}.png")
    preview(list(icons.values())).save(OUT / "icons_preview.png")
    preview([icons["icon_a"], icons["icon_a2"]]).save(OUT / "icon_a_compare.png")
    banner(icons["icon_a2"], OUT / "banner.png")
    print("できました:", ", ".join(f"branding/{n}.png" for n in icons), "と branding/icons_preview.png")


if __name__ == "__main__":
    main()
