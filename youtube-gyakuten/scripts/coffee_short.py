"""コーヒー10年戦争のショート動画(縦 1080x1920・約50秒)。

議席が何度もひっくり返る流れを1本にまとめ、最後に「続きは本編で」と誘導する。
  .venv/bin/python scripts/coffee_short.py   -> output/coffee_short/coffee_short.mp4
声は本編と同じ(MiniMax・声4・読み方のルールも本編と同じ)。
"""
import os
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coffee_story as cs  # noqa: E402  (本編の読み方の設定・声の作り方を使う)
from frames import (BAD, CURTAIN, CURTAIN_DARK, GOOD, INK, PANEL, STAGE, STAGE_LIGHT, SUB, TRIM, WHITE,  # noqa: E402
                    font, mug, text)
from motion import angle_at, out_back, out_cubic, reverse_stamp, seats_motion, seg  # noqa: E402

W, H = 1080, 1920
FPS = 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "coffee_short")
LEAD, TAIL = 0.2, 0.35

# 場面:(見出し, 年のチップ, パネルの文, [(議席が動き始める割合, 前, 後)], ナレーション)
SCENES = [
    ("コーヒーは\n体にいい？悪い？", None, None, [], 50,
     "コーヒーって、体にいいの？悪いの？実は研究の世界では、30年以上も答えがひっくり返り続けているんです。"),
    ("1991年", "1991年", "WHOの機関\n「発がん性の疑い」", [(0.35, 50, 35)], None,
     "1991年、WHOの機関が、コーヒーに発がん性の疑いあり、と発表。悪い派が大きくリードします。"),
    ("2016年", "2016年", "見直したら\n疑いの正体はタバコ", [(0.45, 35, 53)], None,
     "ところが2016年。研究を見直すと、疑いの正体はタバコでした。いい派が逆転します！"),
    ("2018年", "2018年", "裁判所\n「がんの警告表示が必要」", [(0.05, 53, 66), (0.45, 66, 51)], None,
     "その後、大きな調査で差を広げますが、2018年、アメリカの裁判所が、がんの警告表示が必要と判断。51対49の大接戦に。"),
    ("2019年", "2019年", "州が\n「警告は不要」と決定", [(0.4, 51, 66)], None,
     "でも2019年、州が警告は不要と決定。いい派が一気に突き放します。"),
    ("2025年", "2025年", "最新の研究のまとめ\n1日3〜5杯で低リスク", [(0.3, 66, 76)], None,
     "そして2025年、最新の研究のまとめで、いい派が76議席。"),
    ("当選確実？", None, "まだ出せない\nその理由は…", [], 76,
     "ただし、当選確実はまだ出せません。その理由は、本編で。"),
]


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


BASE = None


def caption_chunks(narr):
    """字幕:句点ごとに区切る。"""
    parts = [p + "。" for p in narr.replace("！", "！。").replace("？", "？。").split("。") if p.strip()]
    return [p.replace("！。", "！").replace("？。", "？") for p in parts]


def wrap(d, s, size, width):
    lines, cur = [], ""
    for ch in s:
        if d.textlength(cur + ch, font=font(size)) > width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + ([cur] if cur else [])


def frame(scene, t, dur, voice_len):
    head, year, panel_text, flips, seats_static, narr = scene
    im = BASE.copy()
    d = ImageDraw.Draw(im)
    # 上:チャンネル名
    text(d, (W / 2, 140), "新常識クロニクル", 44, TRIM, anchor="mm")
    # 見出し(ポンと出る)
    k = out_back(seg(t, 0.0, 0.35))
    if k > 0:
        lines = head.split("\n")
        size = int((110 if len(lines) > 1 else 150) * (0.6 + 0.4 * k))
        for i, ln in enumerate(lines):
            text(d, (W / 2, 280 + i * 130 + (0 if len(lines) > 1 else 30)), ln, size, WHITE if i == 0 or len(lines) == 1 else GOOD, anchor="mm")
    # パネル(すべり込む)
    if panel_text:
        a = out_cubic(seg(t, 0.25, 0.6))
        dx = int((1 - a) * 900)
        x0, y0, x1, y1 = 90 + dx, 500, W - 90 + dx, 780
        d.rounded_rectangle([x0 + 8, y0 + 12, x1 + 8, y1 + 12], radius=40, fill=(14, 19, 32))
        d.rounded_rectangle([x0, y0, x1, y1], radius=40, fill=PANEL)
        for i, ln in enumerate(panel_text.split("\n")):
            size = int(min(70, 70 * 820 / max(1, d.textlength(ln, font=font(70)))))
            good_news = (flips[-1][2] > flips[0][1]) if flips else True
            text(d, ((x0 + x1) / 2, y0 + 85 + i * 105), ln, size, INK if i == 0 else (GOOD if good_news else BAD), anchor="mm")
    elif year is None and seats_static == 50:
        mug(d, W / 2 - 140, 470, 280)
    # 議席
    cx, cy, R = W / 2, 1290, 430
    good = seats_static if seats_static is not None else (flips[0][1] if flips else 50)
    before, after, p, q = good, good, 1.0, 1.0
    for start, b, a_ in flips:
        ts = LEAD + start * voice_len
        if t >= ts:
            before, after = b, a_
            p = out_cubic(seg(t, ts, ts + 0.9))
            q = seg(t, ts, ts + 1.6)
        elif before == after == good:
            before = after = b
    seats_motion(d, cx, cy, R, before, after, p, angle_at(before, after, q))
    shown = round(before + (after - before) * p)
    for x, lab, n, c in ((cx - R * 0.72, "いい派", shown, GOOD), (cx + R * 0.72, "悪い派", 100 - shown, BAD)):
        text(d, (x, cy + 25), lab, 50, c, anchor="ma")
        text(d, (x, cy + 80), str(n), 110, WHITE, anchor="ma")
    for start, b, a_ in flips:
        if (b < 50 < a_) or (a_ < 50 < b):
            ts = LEAD + start * voice_len
            reverse_stamp(d, cx, cy - R * 0.62, 95, seg(t, ts + 0.8, ts + 1.2))
    # 最後の場面:「当選確実」のハンコ+本編への誘導
    if seats_static == 76:
        kk = seg(t, 0.4, 0.8)
        if kk > 0:
            sc = 1.5 - 0.5 * out_back(kk)
            r = 140 * sc
            sx, sy = cx, cy - 90
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(27, 36, 58), outline=(220, 60, 60), width=max(4, int(12 * sc)))
            text(d, (sx, sy - 30 * sc), "当選確実", int(54 * sc), (220, 60, 60), anchor="mm")
            text(d, (sx, sy + 40 * sc), "まだ出せない", int(36 * sc), WHITE, anchor="mm")
        b = seg(t, 1.6, 2.0)
        if b > 0:
            s2 = 0.6 + 0.4 * out_back(b)
            d.rounded_rectangle([W / 2 - 300 * s2, 1690 - 60 * s2, W / 2 + 300 * s2, 1690 + 60 * s2], radius=60 * s2, fill=(220, 40, 40))
            text(d, (W / 2, 1690), "続きは本編で ▶", int(60 * s2), WHITE, anchor="mm")
        return im
    # 字幕(句点ごと・声の長さに合わせて切りかえ)
    chunks = caption_chunks(narr)
    total = sum(len(c) for c in chunks)
    acc, cur = 0, chunks[-1]
    for c in chunks:
        if t < LEAD + (acc + len(c)) / total * voice_len:
            cur = c
            break
        acc += len(c)
    lines = wrap(d, cur, 54, 900)
    y = 1700 - (len(lines) - 1) * 36
    for ln in lines:
        d.text((W / 2, y), ln, font=font(54), fill=WHITE, anchor="mm", stroke_width=8, stroke_fill=(14, 19, 32))
        y += 72
    return im


def main():
    global BASE
    os.makedirs(OUT, exist_ok=True)
    BASE = vstage()
    tmp = os.path.join(OUT, "_frames")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    audio, n = [], 0
    for i, sc in enumerate(SCENES):
        v = cs.voice_for(i, sc[5], os.path.join(OUT, "voice"))
        vl = len(v) / 24000
        dur = LEAD + vl + TAIL + (1.2 if i == len(SCENES) - 1 else 0)
        frames = int(round(dur * FPS))
        for f in range(frames):
            frame(sc, f / FPS, dur, vl).save(os.path.join(tmp, f"{n:05d}.png"))
            n += 1
        a = np.zeros(int(round(frames / FPS * 24000)), dtype="float32")
        a[int(LEAD * 24000): int(LEAD * 24000) + len(v)] = v[: len(a) - int(LEAD * 24000)]
        audio.append(a)
        print(f"{i + 1}/{len(SCENES)} {sc[0].splitlines()[0]} {dur:.1f}秒", flush=True)
    wav = os.path.join(OUT, "narration.wav")
    sf.write(wav, np.concatenate(audio), 24000)
    out = os.path.join(OUT, "coffee_short.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"), "-i", wav,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(tmp)
    print("done:", out, f"{n / FPS:.1f}秒")


if __name__ == "__main__":
    sys.exit(main())
