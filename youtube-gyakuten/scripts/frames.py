"""逆転劇場：研究まとめカードと議席グラフの画面を作る(試作 v2)。

見た目の方針(チャンネル名の「劇場」に合わせる)
- 背景：紺の舞台＋上に赤い幕＋スポットライト
- カード：白い角丸のパネル。文字は太いゴシック
- ピクトグラム：丸みのある線画(線の太さをそろえ、1色だけ塗る)
- 色：いい派=オレンジ、悪い派=青

  python3 scripts/frames.py            -> output/frames/*.png と seats_2018.mp4
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
STAGE = (27, 36, 58)        # 舞台の紺
STAGE_LIGHT = (58, 72, 108)  # スポットライトの色
CURTAIN = (176, 38, 48)
CURTAIN_DARK = (128, 24, 34)
TRIM = (232, 190, 92)
PANEL = (250, 248, 244)
INK = (30, 36, 52)
SUB = (120, 126, 140)
GOOD = (240, 128, 40)   # いい派=オレンジ
BAD = (62, 120, 220)    # 悪い派=青
WHITE = (255, 255, 255)
# 2つの派の名前(左=オレンジ、右=青)。回のスクリプトで LBL[:] = ["お気持ち派", "定額派"] のように中身だけ差しかえる
LBL = ["いい派", "悪い派"]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "frames")
BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(size, heavy=True):
    return ImageFont.truetype(BLACK if heavy else BOLD, size, index=0)


def text(d, xy, s, size, fill=INK, heavy=True, anchor="la"):
    d.text(xy, s, font=font(size, heavy), fill=fill, anchor=anchor)


def mixed_line(d, x, y, parts, size):
    f = font(size)
    for s, c in parts:
        d.text((x, y), s, font=f, fill=c)
        x += d.textlength(s, font=f)
    return x


# ---------- 背景 ----------
def stage():
    im = Image.new("RGB", (W, H), STAGE)
    light = Image.new("L", (W, H), 0)
    ImageDraw.Draw(light).ellipse([W * 0.15, H * 0.05, W * 0.85, H * 1.25], fill=255)
    light = light.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new("RGB", (W, H), STAGE_LIGHT), im, light)
    d = ImageDraw.Draw(im)
    # 床のライン
    d.rectangle([0, H - 40, W, H], fill=(20, 27, 44))
    # 上の幕(ひだ+波形のすそ)
    d.rectangle([0, 0, W, 46], fill=CURTAIN)
    for x in range(0, W, 80):
        d.rectangle([x + 50, 0, x + 62, 46], fill=CURTAIN_DARK)
    for x in range(0, W + 80, 80):
        d.pieslice([x - 40, 6, x + 40, 86], 0, 180, fill=CURTAIN)
    for x in range(0, W + 80, 80):
        d.arc([x - 40, 6, x + 40, 86], 0, 180, fill=TRIM, width=4)
    # 左右の幕
    for side in (0, 1):
        x0 = 0 if side == 0 else W - 36
        d.rectangle([x0, 0, x0 + 36, H], fill=CURTAIN_DARK)
    return im, d


def panel(d, box, r=36):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 8, y0 + 12, x1 + 8, y1 + 12], radius=r, fill=(14, 19, 32))  # 影
    d.rounded_rectangle(box, radius=r, fill=PANEL)


# ---------- ピクトグラム(線画) ----------
LW = 9  # 線の太さ


def line(d, pts, color=INK, w=LW):
    d.line(pts, fill=color, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=color)


def bean(d, cx, top, h, fill=None, color=INK, w=LW):
    """丸い頭+まるっとした胴体の人(手足なし)。fill で胴体を塗る。"""
    hr = h * 0.17
    d.ellipse([cx - hr, top, cx + hr, top + 2 * hr], outline=color, width=w, fill=PANEL)
    bw = h * 0.36
    bt = top + 2 * hr + h * 0.06
    d.rounded_rectangle([cx - bw, bt, cx + bw, top + h], radius=bw * 0.9, outline=color, width=w,
                        fill=fill or PANEL)
    # 地面のライン
    line(d, [(cx - bw * 1.3, top + h + 12), (cx + bw * 1.3, top + h + 12)], color, max(4, w // 2))


CUP_LINE = (107, 58, 34)     # こげ茶の太いふち
CUP_BODY = (241, 231, 211)
CUP_SHADE = (226, 210, 182)
CUP_RIM = (250, 245, 234)
COFFEE = (104, 44, 22)
COFFEE_EDGE = (178, 112, 66)
SAUCER = (236, 208, 172)


def mug(d, x, y, s, color=None, fill=None, steam=True, w=None):
    """ソーサーつきのコーヒーカップ(こげ茶の太いふち・クリーム色・上から見たコーヒー)。(x, y)=左上、s=幅。"""
    lw = max(3, int(s * 0.055)) if w is None else max(3, int(min(w, s * 0.07)))
    # ソーサー
    d.ellipse([x - 0.1 * s, y + 0.88 * s, x + 0.98 * s, y + 1.12 * s], fill=SAUCER, outline=CUP_LINE, width=lw)
    # 取っ手
    d.ellipse([x + 0.6 * s, y + 0.44 * s, x + 1.0 * s, y + 0.8 * s], outline=CUP_LINE, width=int(lw * 2.6))
    d.ellipse([x + 0.6 * s + lw * 0.9, y + 0.44 * s + lw * 0.9, x + 1.0 * s - lw * 0.9, y + 0.8 * s - lw * 0.9],
              outline=CUP_BODY, width=max(2, int(lw * 0.8)))
    # 本体(楕円の下半分)と影
    d.chord([x, y - 0.1 * s, x + 0.82 * s, y + 0.98 * s], 0, 180, fill=CUP_BODY, outline=CUP_LINE, width=lw)
    d.chord([x + 0.36 * s, y + 0.06 * s, x + 0.82 * s - lw, y + 0.98 * s - lw], 0, 90, fill=CUP_SHADE)
    # 飲み口とコーヒー
    d.ellipse([x, y + 0.32 * s, x + 0.82 * s, y + 0.56 * s], fill=CUP_RIM, outline=CUP_LINE, width=lw)
    d.ellipse([x + 0.07 * s, y + 0.36 * s, x + 0.75 * s, y + 0.52 * s], fill=COFFEE_EDGE)
    d.ellipse([x + 0.08 * s, y + 0.365 * s, x + 0.74 * s, y + 0.53 * s], fill=COFFEE)
    d.rounded_rectangle([x + 0.5 * s, y + 0.39 * s, x + 0.6 * s, y + 0.415 * s], radius=s * 0.012, fill=(250, 240, 230))
    d.rounded_rectangle([x + 0.63 * s, y + 0.395 * s, x + 0.67 * s, y + 0.42 * s], radius=s * 0.012, fill=(250, 240, 230))
    if steam:
        for i in range(2):
            sx = x + 0.3 * s + i * 0.22 * s
            line(d, [(sx, y + 0.27 * s), (sx + 0.05 * s, y + 0.18 * s), (sx, y + 0.1 * s),
                     (sx + 0.05 * s, y + 0.02 * s)], CUP_LINE, max(3, lw - 1))


def meter(d, cx, cy, r, needle=0.85, color=INK, w=LW):
    d.arc([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=color, width=w)
    d.arc([cx - r + w * 1.6, cy - r + w * 1.6, cx + r - w * 1.6, cy + r - w * 1.6], 180 + 180 * 0.68, 360,
          fill=BAD, width=w + 2)
    a = math.pi * (1 - needle)
    line(d, [(cx, cy), (cx + 0.78 * r * math.cos(a), cy - 0.78 * r * math.sin(a))], color, w)
    d.ellipse([cx - w * 1.3, cy - w * 1.3, cx + w * 1.3, cy + w * 1.3], fill=color)
    line(d, [(cx - r - 10, cy + 14), (cx + r + 10, cy + 14)], color, max(4, w // 2))


def heart(d, cx, cy, s, fill=GOOD, color=INK, w=LW):
    r = s * 0.28
    d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=fill)
    d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=fill)
    d.polygon([(cx - 1.93 * r, cy + 0.35 * r), (cx + 1.93 * r, cy + 0.35 * r), (cx, cy + 2.3 * r)], fill=fill)


def arrow(d, x0, x1, y, color=INK, w=LW):
    line(d, [(x0, y), (x1, y)], color, w)
    line(d, [(x1 - 26, y - 22), (x1, y), (x1 - 26, y + 22)], color, w)


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
    """good=いい派の議席数。flip_to と progress で、席が順に色を変える。"""
    s = R * 0.05
    target = good if flip_to is None else flip_to
    lo, hi = sorted((good, target))
    done = int((hi - lo) * progress)
    for i, (a, r) in enumerate(SEATS):
        x, y = cx + R * r * math.cos(a), cy - R * r * math.sin(a)
        if i < lo:
            c = GOOD
        elif i >= hi:
            c = BAD
        else:
            j = i - lo if target > good else hi - 1 - i
            to = GOOD if target > good else BAD
            c = to if j < done else (BAD if to == GOOD else GOOD)
        d.rounded_rectangle([x - s, y - s, x + s, y + s], radius=s * 0.45, fill=c)  # 角丸の四角い席
    d.line([(cx, cy - R * 1.08), (cx, cy - R * 0.36)], fill=TRIM, width=4)
    text(d, (cx, cy - R * 0.33), "過半数", int(R * 0.08), TRIM, heavy=False, anchor="ma")


def seat_numbers(d, cx, cy, R, good):
    for x, label, n, c in ((cx - R * 0.72, LBL[0], good, GOOD), (cx + R * 0.72, LBL[1], 100 - good, BAD)):
        text(d, (x, cy + R * 0.06), label, int(R * 0.12), c, anchor="ma")
        text(d, (x, cy + R * 0.2), str(n), int(R * 0.3), WHITE, anchor="ma")


# ---------- 画面 ----------
def study_card(path, year, country, kind, title_lines, facts, picto, before, after, delta_label, source):
    im, d = stage()
    panel(d, (90, 130, 1130, 1000))
    # 年・国・種類(チップ)
    d.rounded_rectangle([140, 175, 330, 245], radius=35, fill=INK)
    text(d, (235, 210), year, 46, WHITE, anchor="mm")
    text(d, (355, 210), country, 46, INK, anchor="lm")
    kw = d.textlength(kind, font=font(32, False)) + 48
    d.rounded_rectangle([1080 - kw, 180, 1080, 240], radius=30, outline=SUB, width=3)
    text(d, (1080 - kw / 2, 210), kind, 32, SUB, heavy=False, anchor="mm")
    # 見出し
    y = 280
    for parts in title_lines:
        wid = sum(d.textlength(t, font=font(92)) for t, _ in parts)
        mixed_line(d, 140, y, parts, int(min(92, 92 * 940 / wid)))
        y += 122
    # ピクトグラム
    picto(d)
    # 研究データ
    y0 = 840
    d.line([(140, y0 - 18), (1080, y0 - 18)], fill=(222, 218, 210), width=3)
    x = 140
    for label, value in facts:
        text(d, (x, y0), label, 28, SUB, heavy=False)
        vs = int(min(48, 48 * 290 / d.textlength(value, font=font(48))))
        text(d, (x, y0 + 36 + (48 - vs) // 2), value, vs, INK)
        x += 320
    text(d, (140, 1020), source, 24, (170, 176, 192), heavy=False)
    # 右：議席
    cx, cy, R = 1530, 700, 320
    hemicycle(d, cx, cy, R, after)
    seat_numbers(d, cx, cy, R, after)
    color = GOOD if after > before else BAD
    bw = d.textlength(delta_label, font=font(50)) + 70
    d.rounded_rectangle([cx - bw / 2, 230, cx + bw / 2, 310], radius=40, fill=color)
    text(d, (cx, 268), delta_label, 50, WHITE, anchor="mm")
    im.save(path)


def parliament(path, year, headline, good, flip_to=None, progress=1.0):
    im, d = stage()
    tag = "開票速報"
    tw = d.textlength(tag, font=font(48)) + 60
    d.rounded_rectangle([90, 120, 90 + tw, 196], radius=38, fill=GOOD)
    text(d, (90 + tw / 2, 158), tag, 48, WHITE, anchor="mm")
    text(d, (120 + tw, 158), f"{year}  {headline}", 52, WHITE, anchor="lm")
    cx, cy, R = W / 2, 790, 550
    hemicycle(d, cx, cy, R, good, flip_to, progress)
    shown = good if flip_to is None else round(good + (flip_to - good) * progress)
    for x, label, n, c in ((cx - R * 0.72, LBL[0], shown, GOOD), (cx + R * 0.72, LBL[1], 100 - shown, BAD)):
        text(d, (x, cy + 30), label, 52, c, anchor="ma")
        text(d, (x, cy + 86), str(n), 112, WHITE, anchor="ma")
    im.save(path)


def picto_uk(d):
    for i in range(8):
        mug(d, 150 + (i % 4) * 112, 585 + (i // 4) * 118, 82, steam=False, w=7, fill=(255, 236, 214))
    arrow(d, 610, 690, 690)
    bean(d, 790, 575, 215, fill=GOOD)
    heart(d, 975, 610, 80)
    text(d, (975, 700), "長生き", 54, GOOD, anchor="ma")


def picto_japan(d):
    meter(d, 250, 740, 105, needle=0.88)
    text(d, (250, 770), "160/100以上", 28, INK, heavy=False, anchor="ma")
    text(d, (410, 700), "+", 80, INK, anchor="mm")
    mug(d, 460, 615, 92, fill=(255, 236, 214))
    mug(d, 580, 615, 92, fill=(255, 236, 214))
    arrow(d, 730, 810, 690)
    bean(d, 880, 585, 205, fill=BAD)
    text(d, (955, 655), "×2", 84, BAD, anchor="la")


def main():
    os.makedirs(OUT, exist_ok=True)
    study_card(
        os.path.join(OUT, "card_2018_uk.png"), "2018", "イギリス", "約50万人の追跡調査",
        [[("1日", INK), ("8杯以上", GOOD), ("でも", INK)], [("死亡リスクは", INK), ("低い", GOOD)]],
        [("対象", "約50万人"), ("期間", "10年"), ("種類", "観察研究")],
        picto_uk, 51, 57, "いい派 +6議席",
        "出典：Loftfield et al., JAMA Internal Medicine 2018(UK Biobank)")
    study_card(
        os.path.join(OUT, "card_2022_japan.png"), "2022", "日本", "約1.9万人の追跡調査",
        [[("血圧が高い人は", INK)], [("1日2杯", BAD), ("で死亡", INK), ("2倍", BAD)]],
        [("対象", "約1.9万人"), ("年齢", "40〜79歳"), ("緑茶", "差なし")],
        picto_japan, 69, 66, "悪い派 +3議席",
        "出典：Teramoto et al., Journal of the American Heart Association 2022(JACC研究)")
    parliament(os.path.join(OUT, "parliament_2018.png"), "2018.3", "裁判所「がんの警告表示が必要」", 51)

    # 議席が順に変わる短い動画(2018.3 の 66→51)
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
