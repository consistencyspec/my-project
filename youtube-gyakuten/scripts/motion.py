"""逆転劇場：動きのある画面(カードが順に出る・席が弾んでひっくり返る・天秤が傾く)。"""
import math

from PIL import Image, ImageDraw

from frames import (
    BAD, GOOD, INK, PANEL, SEATS, SUB, TRIM, W, H, WHITE, font, mixed_line, panel, stage, text,
)

REVERSE_RED = (230, 60, 60)


# ---------- イージング ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, t0, t1):
    """t が t0→t1 の間で 0→1。"""
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def out_elastic(x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 2 ** (-9 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def with_alpha(layer, a):
    if a >= 1:
        return layer
    out = layer.copy()
    out.putalpha(out.getchannel("A").point(lambda v: int(v * a)))
    return out


def blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---------- 天秤 ----------
def tilt_of(good):
    """いい派が多いほど左(オレンジ)が下がる。角度(度)。"""
    return clamp((good - 50) * 0.9, -24, 24)


def balance(d, cx, base_y, R, angle):
    pivot = (cx, base_y - R * 0.2)
    L = R * 0.21
    # 台と柱
    d.rounded_rectangle([cx - R * 0.09, base_y - R * 0.035, cx + R * 0.09, base_y], radius=6, fill=TRIM)
    d.line([(cx, base_y - R * 0.03), pivot], fill=TRIM, width=max(4, int(R * 0.022)))
    a = math.radians(angle)
    ends = [(pivot[0] - L * math.cos(a), pivot[1] + L * math.sin(a)),
            (pivot[0] + L * math.cos(a), pivot[1] - L * math.sin(a))]
    d.line(ends, fill=TRIM, width=max(5, int(R * 0.028)))
    for (ex, ey), c in zip(ends, (GOOD, BAD)):
        drop = R * 0.07
        d.line([(ex, ey), (ex - R * 0.05, ey + drop)], fill=TRIM, width=3)
        d.line([(ex, ey), (ex + R * 0.05, ey + drop)], fill=TRIM, width=3)
        d.pieslice([ex - R * 0.07, ey + drop - R * 0.045, ex + R * 0.07, ey + drop + R * 0.05], 0, 180, fill=c)
    d.ellipse([pivot[0] - R * 0.025, pivot[1] - R * 0.025, pivot[0] + R * 0.025, pivot[1] + R * 0.025], fill=TRIM)


# ---------- 議席(動き) ----------
def seats_motion(d, cx, cy, R, before, after, p, angle=None):
    """p=0→1 で席が順にひっくり返る。ひっくり返った席はポンと弾む。"""
    s0 = R * 0.05
    lo, hi = sorted((before, after))
    n = hi - lo
    to = GOOD if after > before else BAD
    frm = BAD if to == GOOD else GOOD
    for i, (a, r) in enumerate(SEATS):
        x, y = cx + R * r * math.cos(a), cy - R * r * math.sin(a)
        s = s0
        if i < lo:
            c = GOOD
        elif i >= hi:
            c = BAD
        else:
            j = i - lo if after > before else hi - 1 - i
            local = p * (n + 2) - j
            if local >= 0:
                c = to
                s = s0 * (1 + 0.7 * max(0.0, 1 - local / 2.5))
            else:
                c = frm
        d.rounded_rectangle([x - s, y - s, x + s, y + s], radius=s * 0.45, fill=c)
    d.line([(cx, cy - R * 1.08), (cx, cy - R * 0.39)], fill=TRIM, width=4)
    text(d, (cx, cy + R * 0.03), "過半数", int(R * 0.075), TRIM, heavy=False, anchor="ma")
    if angle is None:
        angle = tilt_of(before + (after - before) * p)
    balance(d, cx, cy, R, angle)


def angle_at(before, after, q):
    return tilt_of(before) + (tilt_of(after) - tilt_of(before)) * out_elastic(q)


def numbers(d, cx, cy, R, good, big=None, pop=0.0):
    for k, (x, label, n, c) in enumerate(((cx - R * 0.72, "いい派", good, GOOD), (cx + R * 0.72, "悪い派", 100 - good, BAD))):
        text(d, (x, cy + R * 0.06), label, int(R * 0.12), c, anchor="ma")
        size = int(R * 0.3 * (1 + (0.25 * pop if big == k else 0)))
        text(d, (x, cy + R * 0.2), str(n), size, WHITE, anchor="ma")


def reversed_majority(before, after):
    """負けていた側が過半数を取ったとき(50対50からの変化は逆転に数えない)。"""
    return (before < 50 < after) or (after < 50 < before)


def reverse_stamp(d, cx, cy, size, k):
    """「逆転!」のスタンプ。k=0→1 で大きく出てから縮む。"""
    if k <= 0:
        return
    sc = out_back(k, 2.4)
    s = size * sc
    d.rounded_rectangle([cx - s * 1.5, cy - s * 0.62, cx + s * 1.5, cy + s * 0.62], radius=s * 0.3,
                        fill=REVERSE_RED, outline=WHITE, width=max(3, int(s * 0.07)))
    text(d, (cx, cy), "逆転！", max(10, int(s * 0.8)), WHITE, anchor="mm")


# ---------- 研究カード(動き) ----------
class Card:
    """研究カード。frame(t) でその時刻の画面を返す。"""
    ANIM_END = 3.8  # これ以降は止まった絵

    def __init__(self, year, country, kind, title_lines, facts, picto, before, after, delta_label, source):
        self.before, self.after, self.delta_label = before, after, delta_label
        self.base = stage()[0].convert("RGBA")
        # パネル(年・国・種類まで)
        self.panel = blank()
        d = ImageDraw.Draw(self.panel)
        panel(d, (90, 130, 1130, 1000))
        yw = max(190, d.textlength(year, font=font(46)) + 60)
        d.rounded_rectangle([140, 175, 140 + yw, 245], radius=35, fill=INK)
        text(d, (140 + yw / 2, 210), year, 46, WHITE, anchor="mm")
        text(d, (165 + yw, 210), country, 46, INK, anchor="lm")
        kw = d.textlength(kind, font=font(32, False)) + 48
        d.rounded_rectangle([1080 - kw, 180, 1080, 240], radius=30, outline=SUB, width=3)
        text(d, (1080 - kw / 2, 210), kind, 32, SUB, heavy=False, anchor="mm")
        # 見出し(1行ずつ)
        self.titles = []
        y = 280
        for parts in title_lines:
            lay = blank()
            dd = ImageDraw.Draw(lay)
            wid = sum(dd.textlength(t, font=font(92)) for t, _ in parts)
            mixed_line(dd, 140, y, parts, int(min(92, 92 * 940 / wid)))
            self.titles.append(lay)
            y += 122
        # ピクトグラム
        self.picto = blank()
        picto(ImageDraw.Draw(self.picto))
        self.picto_box = (110, 555, 1110, 815)
        self.picto_crop = self.picto.crop(self.picto_box)
        # 研究データ・出典
        self.facts = blank()
        d = ImageDraw.Draw(self.facts)
        y0 = 840
        d.line([(140, y0 - 18), (1080, y0 - 18)], fill=(222, 218, 210), width=3)
        x = 140
        for label, value in facts:
            text(d, (x, y0), label, 28, SUB, heavy=False)
            vs = int(min(48, 48 * 290 / d.textlength(value, font=font(48))))
            text(d, (x, y0 + 36 + (48 - vs) // 2), value, vs, INK)
            x += 320
        text(d, (140, 1020), source, 24, (170, 176, 192), heavy=False)

    def frame(self, t):
        im = self.base.copy()
        # パネルが左からすべり込む
        k = out_cubic(seg(t, 0.0, 0.45))
        dx = int((1 - k) * -1250)
        im.alpha_composite(self.panel, (dx, 0)) if dx > -W else None
        if dx == 0:
            for i, lay in enumerate(self.titles):
                a = out_cubic(seg(t, 0.4 + i * 0.18, 0.75 + i * 0.18))
                if a > 0:
                    im.alpha_composite(with_alpha(lay, a), (0, int((1 - a) * 30)))
            a = seg(t, 0.85, 1.3)
            if a > 0:
                sc = 0.6 + 0.4 * out_back(a)
                bw, bh = self.picto_crop.size
                pic = self.picto_crop.resize((max(1, int(bw * sc)), max(1, int(bh * sc))), Image.BICUBIC)
                pic = with_alpha(pic, min(1.0, a * 2))
                cxp = (self.picto_box[0] + self.picto_box[2]) // 2
                cyp = (self.picto_box[1] + self.picto_box[3]) // 2
                im.alpha_composite(pic, (cxp - pic.size[0] // 2, cyp - pic.size[1] // 2))
            a = out_cubic(seg(t, 1.3, 1.7))
            if a > 0:
                im.alpha_composite(with_alpha(self.facts, a))
        # 右：議席(フェードイン → バッジ → ひっくり返る+天秤が傾く)
        a = seg(t, 0.2, 0.7)
        if a > 0:
            right = blank()
            d = ImageDraw.Draw(right)
            cx, cy, R = 1530, 700, 320
            p = out_cubic(seg(t, 2.2, 3.1))
            q = seg(t, 2.2, 3.8)
            good = round(self.before + (self.after - self.before) * p)
            seats_motion(d, cx, cy, R, self.before, self.after, p, angle_at(self.before, self.after, q))
            win = 0 if self.after > self.before else 1
            numbers(d, cx, cy, R, good, big=win, pop=math.sin(math.pi * seg(t, 2.2, 3.3)))
            b = seg(t, 1.6, 2.1)
            if b > 0:
                color = GOOD if self.after > self.before else BAD
                sc = out_back(b)
                fs = max(8, int(50 * sc))
                bw = d.textlength(self.delta_label, font=font(fs)) + 70 * sc
                d.rounded_rectangle([cx - bw / 2, 270 - 40 * sc, cx + bw / 2, 270 + 40 * sc], radius=40 * sc, fill=color)
                text(d, (cx, 268), self.delta_label, fs, WHITE, anchor="mm")
            if reversed_majority(self.before, self.after):
                reverse_stamp(d, cx, cy - R * 0.62, 70, seg(t, 3.0, 3.4))
            im.alpha_composite(with_alpha(right, a))
        return im.convert("RGB")


# ---------- 議会の全画面(動き) ----------
def parliament_frame(year, headline, before, after, t, flip=(0.5, 1.6), settle=2.4, tag="開票速報"):
    im, d = stage()
    tw = d.textlength(tag, font=font(48)) + 60
    k = out_back(seg(t, 0.0, 0.35))
    d.rounded_rectangle([90, 158 - 38 * k, 90 + tw, 158 + 38 * k], radius=38, fill=GOOD)
    if k > 0.3:
        text(d, (90 + tw / 2, 158), tag, int(48 * min(1, k)), WHITE, anchor="mm")
    a = out_cubic(seg(t, 0.15, 0.5))
    text(d, (120 + tw - (1 - a) * 60, 158), f"{year}  {headline}".strip(), 52,
         tuple(int(v * a + s * (1 - a)) for v, s in zip(WHITE, (27, 36, 58))), anchor="lm")
    cx, cy, R = W / 2, 790, 550
    p = out_cubic(seg(t, *flip))
    q = seg(t, flip[0], settle)
    seats_motion(d, cx, cy, R, before, after, p, angle_at(before, after, q))
    good = round(before + (after - before) * p)
    win = 0 if after > before else 1
    for i, (x, label, n, c) in enumerate(((cx - R * 0.72, "いい派", good, GOOD), (cx + R * 0.72, "悪い派", 100 - good, BAD))):
        text(d, (x, cy + 30), label, 52, c, anchor="ma")
        size = int(112 * (1 + (0.25 * math.sin(math.pi * seg(t, flip[0], flip[1] + 0.3)) if i == win else 0)))
        text(d, (x, cy + 76), str(n), size, WHITE, anchor="ma")
    if reversed_majority(before, after):
        reverse_stamp(d, cx, cy - R * 0.68, 110, seg(t, flip[1], flip[1] + 0.4))
    return im
