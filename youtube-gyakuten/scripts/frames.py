"""逆転劇場：研究まとめカードと議席グラフの画面を作る(試作)。

見た目の方針(参考：方眼紙の背景、太い明朝の黒文字、赤の強調、黒のピクトグラム)
  python3 scripts/frames.py            -> output/frames/*.png と seats.mp4
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (243, 240, 232)
GRID = (226, 222, 212)
INK = (24, 24, 24)
RED = (200, 32, 30)
NAVY = (52, 62, 74)
GOLD = (201, 162, 39)
GRAY = (130, 130, 130)
GOOD, BAD = RED, NAVY  # いい派=赤、悪い派=紺

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "frames")
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(size, serif=True):
    return ImageFont.truetype(SERIF if serif else SANS, size, index=0)


def canvas():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=GRID, width=1)
    return im, d


# ---------- ピクトグラム ----------
def person(d, cx, top, h, color=INK, dress=None):
    """トイレの案内表示のような人のピクトグラム。dress を渡すとスカート型(色つき)。"""
    u = h / 10
    d.ellipse([cx - 1.1 * u, top, cx + 1.1 * u, top + 2.2 * u], fill=color)
    bt = top + 2.6 * u
    if dress:
        d.polygon([(cx - 1.4 * u, bt), (cx + 1.4 * u, bt), (cx + 2.2 * u, bt + 4.4 * u),
                   (cx - 2.2 * u, bt + 4.4 * u)], fill=dress, outline=color, width=max(2, int(u / 4)))
        legs_top = bt + 4.4 * u
    else:
        d.rounded_rectangle([cx - 1.5 * u, bt, cx + 1.5 * u, bt + 4 * u], radius=u * 0.6, fill=color)
        legs_top = bt + 3.6 * u
    # 腕
    d.rounded_rectangle([cx - 2.3 * u, bt + 0.1 * u, cx - 1.7 * u, bt + 3.6 * u], radius=u * 0.3, fill=color)
    d.rounded_rectangle([cx + 1.7 * u, bt + 0.1 * u, cx + 2.3 * u, bt + 3.6 * u], radius=u * 0.3, fill=color)
    # 脚
    d.rounded_rectangle([cx - 1.2 * u, legs_top, cx - 0.2 * u, top + h], radius=u * 0.4, fill=color)
    d.rounded_rectangle([cx + 0.2 * u, legs_top, cx + 1.2 * u, top + h], radius=u * 0.4, fill=color)


def cup(d, x, y, s, color=INK, steam=True):
    """コーヒーカップ。(x, y)=左上、s=幅。"""
    d.rounded_rectangle([x, y + 0.35 * s, x + 0.8 * s, y + 1.05 * s], radius=s * 0.12, fill=color)
    w = max(3, int(s * 0.09))
    d.arc([x + 0.6 * s, y + 0.48 * s, x + 1.02 * s, y + 0.86 * s], -90, 90, fill=color, width=w)
    d.rounded_rectangle([x - 0.1 * s, y + 1.08 * s, x + 0.95 * s, y + 1.16 * s], radius=s * 0.04, fill=color)
    if steam:
        for i in range(3):
            sx = x + 0.18 * s + i * 0.22 * s
            d.arc([sx - 0.06 * s, y, sx + 0.08 * s, y + 0.15 * s], 90, 270, fill=color, width=max(2, w // 2))
            d.arc([sx - 0.06 * s, y + 0.13 * s, sx + 0.08 * s, y + 0.28 * s], 270, 90, fill=color, width=max(2, w // 2))


def gauge(d, cx, cy, r, color=INK, needle=0.85):
    """血圧計(メーター)。needle=0〜1。"""
    w = max(4, int(r * 0.12))
    d.arc([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=color, width=w)
    d.arc([cx - r, cy - r, cx + r, cy + r], 180 + 180 * 0.7, 360, fill=RED, width=w)
    a = math.pi * (1 - needle)
    d.line([(cx, cy), (cx + 0.85 * r * math.cos(a), cy - 0.85 * r * math.sin(a))], fill=color, width=w)
    d.ellipse([cx - w, cy - w, cx + w, cy + w], fill=color)


def text(d, xy, s, size, fill=INK, serif=True, anchor="la"):
    d.text(xy, s, font=font(size, serif), fill=fill, anchor=anchor)


def mixed_line(d, x, y, parts, size):
    """[(文字, 色), ...] を1行に並べる。"""
    f = font(size)
    for s, c in parts:
        d.text((x, y), s, font=f, fill=c)
        x += d.textlength(s, font=f)
    return x


# ---------- 議席グラフ ----------
def seat_positions(n=100, rows=5, r0=0.42, r1=1.0):
    radii = [r0 + (r1 - r0) * i / (rows - 1) for i in range(rows)]
    total = sum(radii)
    counts = [round(n * r / total) for r in radii]
    counts[-1] += n - sum(counts)
    seats = []
    for r, c in zip(radii, counts):
        for k in range(c):
            a = math.pi * (1 - k / (c - 1)) if c > 1 else math.pi / 2
            seats.append((a, r))
    seats.sort(key=lambda t: -t[0])  # 左(いい派)から右へ
    return seats


SEATS = seat_positions()


def hemicycle(d, cx, cy, R, good, flip_to=None, progress=1.0):
    """good=いい派の議席数。flip_to と progress で、席が順に色を変えるアニメーション。"""
    dot = R * 0.055
    target = good if flip_to is None else flip_to
    lo, hi = sorted((good, target))
    changing = list(range(lo, hi))
    done = int(len(changing) * progress)
    for i, (a, r) in enumerate(SEATS):
        x, y = cx + R * r * math.cos(a), cy - R * r * math.sin(a)
        if i < lo:
            c = GOOD
        elif i >= hi:
            c = BAD
        else:
            j = i - lo if target > good else hi - 1 - i
            flipped = j < done
            c = (GOOD if target > good else BAD) if flipped else (BAD if target > good else GOOD)
        d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=c)
    # 過半数ライン
    d.line([(cx, cy - R * 1.08), (cx, cy - R * 0.36)], fill=GOLD, width=4)
    text(d, (cx, cy - R * 0.33), "過半数", int(R * 0.08), GOLD, serif=False, anchor="ma")


def seat_numbers(d, cx, cy, R, good):
    text(d, (cx - R * 0.72, cy + R * 0.06), "いい派", int(R * 0.12), GOOD, anchor="ma")
    text(d, (cx - R * 0.72, cy + R * 0.2), f"{good}", int(R * 0.3), GOOD, anchor="ma")
    text(d, (cx + R * 0.72, cy + R * 0.06), "悪い派", int(R * 0.12), BAD, anchor="ma")
    text(d, (cx + R * 0.72, cy + R * 0.2), f"{100 - good}", int(R * 0.3), BAD, anchor="ma")


# ---------- 画面 ----------
def study_card(path, year, country, kind, title_lines, facts, picto, before, after, delta_label, source):
    im, d = canvas()
    # 上の帯：年・国・研究の種類
    d.rectangle([80, 70, 80 + 230, 150], fill=INK)
    text(d, (195, 110), year, 64, BG, anchor="mm")
    text(d, (340, 110), country, 52, INK, anchor="lm")
    tag_w = d.textlength(kind, font=font(36, False)) + 40
    d.rounded_rectangle([80, 175, 80 + tag_w, 230], radius=10, outline=INK, width=3)
    text(d, (100, 202), kind, 36, INK, serif=False, anchor="lm")
    # 見出し
    y = 270
    for parts in title_lines:
        mixed_line(d, 80, y, parts, 110)
        y += 140
    # ピクトグラム
    picto(d)
    # 研究データ
    y0 = 860
    d.line([(80, y0 - 20), (1100, y0 - 20)], fill=INK, width=3)
    x = 80
    for label, value in facts:
        text(d, (x, y0), label, 32, GRAY, serif=False)
        text(d, (x, y0 + 40), value, 56, INK)
        x += 340
    text(d, (80, 1030), source, 24, GRAY, serif=False)
    # 右：議席
    cx, cy, R = 1520, 690, 330
    hemicycle(d, cx, cy, R, after)
    seat_numbers(d, cx, cy, R, after)
    color = GOOD if after > before else BAD
    bw = d.textlength(delta_label, font=font(54)) + 60
    d.rounded_rectangle([cx - bw / 2, 220, cx + bw / 2, 300], radius=40, fill=color)
    text(d, (cx, 260), delta_label, 54, BG, anchor="mm")
    im.save(path)


def parliament(path, year, headline, good, flip_to=None, progress=1.0, show_numbers=True):
    im, d = canvas()
    d.rectangle([0, 0, W, 120], fill=INK)
    text(d, (80, 60), "速報", 64, RED, anchor="lm")
    text(d, (280, 60), f"{year}  {headline}", 56, BG, anchor="lm")
    cx, cy, R = W / 2, 800, 600
    hemicycle(d, cx, cy, R, good, flip_to, progress)
    shown = good if flip_to is None else round(good + (flip_to - good) * progress)
    if show_numbers:
        for x, label, n, c in ((cx - R * 0.7, "いい派", shown, GOOD), (cx + R * 0.7, "悪い派", 100 - shown, BAD)):
            text(d, (x, cy + 40), label, 56, c, anchor="ma")
            text(d, (x, cy + 100), str(n), 120, c, anchor="ma")
    im.save(path)


def picto_uk(d):
    # 8杯のカップ → 人(金色)
    for i in range(8):
        cup(d, 90 + (i % 4) * 120, 600 + (i // 4) * 120, 90, steam=False)
    text(d, (590, 700), "→", 90, INK, anchor="mm")
    person(d, 760, 570, 250, dress=GOLD, color=INK)
    text(d, (880, 700), "長生き", 72, RED, anchor="lm")


def picto_japan(d):
    gauge(d, 200, 740, 120, needle=0.88)
    text(d, (200, 760), "160/100以上", 32, INK, serif=False, anchor="ma")
    text(d, (365, 700), "+", 90, INK, anchor="mm")
    cup(d, 420, 610, 90, steam=False)
    cup(d, 535, 610, 90, steam=False)
    text(d, (705, 700), "→", 90, INK, anchor="mm")
    person(d, 820, 580, 230, color=NAVY)
    text(d, (890, 640), "×2", 110, RED, anchor="la")


def main():
    os.makedirs(OUT, exist_ok=True)
    study_card(
        os.path.join(OUT, "card_2018_uk.png"), "2018", "イギリス", "約50万人の追跡調査",
        [[("1日", INK), ("8杯以上", RED), ("でも", INK)], [("死亡リスクは", INK), ("低い", RED)]],
        [("対象", "約50万人"), ("期間", "10年"), ("種類", "観察研究")],
        picto_uk, 51, 57, "いい派 +6議席",
        "出典：Loftfield et al., JAMA Internal Medicine 2018(UK Biobank)")
    study_card(
        os.path.join(OUT, "card_2022_japan.png"), "2022", "日本", "約1.9万人の追跡調査",
        [[("血圧が高い人は", INK)], [("1日2杯", RED), ("で死亡", INK), ("2倍", RED)]],
        [("対象", "約1.9万人"), ("年齢", "40〜79歳"), ("緑茶", "差なし")],
        picto_japan, 69, 66, "悪い派 +3議席",
        "出典：Teramoto et al., Journal of the American Heart Association 2022(JACC研究)")
    parliament(os.path.join(OUT, "parliament_2018.png"), "2018.3", "裁判所「がんの警告表示が必要」", 51)

    # 議席がパタパタ変わる短い動画(2018.3 の 66→51)
    tmp = os.path.join(OUT, "_anim")
    os.makedirs(tmp, exist_ok=True)
    fps, n = 30, 45
    for f in range(n + 30):
        p = min(1.0, f / n)
        p = 1 - (1 - p) ** 2  # 終わりをゆっくり
        parliament(os.path.join(tmp, f"{f:04d}.png"), "2018.3", "裁判所「がんの警告表示が必要」", 66, 51, p)
    mp4 = os.path.join(OUT, "seats_2018.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                    os.path.join(tmp, "%04d.png"), "-pix_fmt", "yuv420p", "-c:v", "libx264", mp4], check=True)
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)
    print("done:", OUT)


if __name__ == "__main__":
    sys.exit(main())
