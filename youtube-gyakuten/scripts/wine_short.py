"""赤ワインは体にいい？ のショート動画(縦 1080x1920・約50秒)。egg_short.py と同じ作り。

1979→1991→2002 で「いい派」が78議席まで勝つ流れを見せ、その後の落とし穴・WHOの発表・最終結果は隠して「続きは本編で」と誘導する。
  .venv/bin/python scripts/wine_short.py   -> output/wine_short/wine_short.mp4
声と読み方の設定は赤ワインの本編(wine_story.py)と同じ。笑い声・はしゃいだ声は使わない。
"""
import os
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coffee_story as cs  # noqa: E402  (声の作り方)
import wine_story  # noqa: E402,F401  (赤ワインの本編の読み方の設定:数字は辞書で読む・飲む国・78議席・2002年 など)
from egg_war import wine  # noqa: E402
import narrate  # noqa: E402,F401
from frames import (BAD, CURTAIN, CURTAIN_DARK, GOOD, INK, PANEL, STAGE, STAGE_LIGHT, SUB, TRIM, WHITE,  # noqa: E402
                    font, text)
from motion import angle_at, out_back, out_cubic, reverse_stamp, seats_motion, seg  # noqa: E402
from PIL import Image as _Image  # noqa: E402

cs.VOICE_FIX[:0] = [("1979年、ワインを", "センキュウヒャク、ナナジュウキュウネン、ワインを"), ("秘密は赤ワイン", "秘密は、赤ワイン")]   # 本編で決めた候補D

W, H = 1080, 1920
FPS = 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "wine_short")
COVER_SEC = 0.5   # 冒頭にサムネイルを出す秒数
FINAL = 50   # 最後の場面:議席は互角の形で見せ、数は「？」で隠す
LEAD, TAIL = 0.2, 0.35

# 場面:(見出し, 年のチップ, パネルの文, [(議席が動き始める割合, 前, 後)], ナレーション)
SCENES = [
    ("赤ワインは\n体にいい？", None, None, [], 50,
     "「赤ワインは体にいい」。そう信じて、グラスを傾けていませんか？ 実はこの話、研究のたびにひっくり返ってきたんです。"),
    ("1979年", "1979年", "18か国の比較\nワインの国は心臓病が少ない", [(0.4, 50, 53)], None,
     "1979年、ワインをよく飲む国ほど、心臓病で亡くなる人が少ない、という研究が出ます。"),
    ("1991年", "1991年", "フレンチ・パラドックス\n秘密は赤ワイン？", [(0.15, 53, 56), (0.55, 56, 62)], None,
     "1991年には、脂っこい食事でも心臓病が少ないフランス人の秘密は赤ワイン、という説が大ブームに。"),
    ("2002年", "2002年", "研究のまとめ\nワインで心臓病が-32%", [(0.1, 62, 68), (0.45, 68, 78)], None,
     "2002年には、研究のまとめでも、ワインを飲む人は心臓病が少ないと出て、いい派が78議席の圧勝です。"),
    ("その後", None, "研究の落とし穴が\n次々と見つかる", [(0.1, 78, 72), (0.3, 72, 62), (0.5, 62, 52)], None,
     "ところがその後、研究の落とし穴が、次々と見つかります。そして2023年、WHOがある発表をします。"),
    ("最終結果は？", None, "WHOの発表と最終結果は\n本編で", [], FINAL,
     "WHOの発表の中身と、最終結果は、本編で。"),
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
        if d.textlength(cur + ch, font=font(size)) > width and cur and ch not in "、。！？」":   # 句読点は行頭に置かない
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
        lay = _Image.new("RGBA", im.size, (0, 0, 0, 0))
        wine(ImageDraw.Draw(lay), W / 2, 470, 300, color=WHITE)
        im.paste(lay, (0, 0), lay)
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
        text(d, (x, cy + 80), "？" if seats_static == FINAL and panel_text else str(n), 110, WHITE, anchor="ma")
    for start, b, a_ in flips:
        if (b < 50 < a_) or (a_ < 50 < b):
            ts = LEAD + start * voice_len
            reverse_stamp(d, cx, cy - R * 0.62, 95, seg(t, ts + 0.8, ts + 1.2))
    # 最後の場面:「当選確実」のハンコ+本編への誘導
    if seats_static == FINAL and panel_text:   # 最後の場面だけ(冒頭も50議席なので区別する)
        kk = seg(t, 0.4, 0.8)
        if kk > 0:
            sc = 1.5 - 0.5 * out_back(kk)
            r = 140 * sc
            sx, sy = cx, cy - 90
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(27, 36, 58), outline=(220, 60, 60), width=max(4, int(12 * sc)))
            text(d, (sx, sy - 30 * sc), "最終結果", int(54 * sc), (220, 60, 60), anchor="mm")
            text(d, (sx, sy + 40 * sc), "は本編で", int(36 * sc), WHITE, anchor="mm")
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


def cover(path):
    """ショート用の縦サムネイル(1080x1920)。scripts/wine_short_cover.py と同じ絵。"""
    import wine_short_cover
    return wine_short_cover.cover(path)


def main():
    if "--cover" in sys.argv:
        os.makedirs(os.path.join(OUT, "..", "thumbnails"), exist_ok=True)
        print(cover(os.path.join(OUT, "..", "thumbnails", "wine_short.png")))
        return
    global BASE
    os.makedirs(OUT, exist_ok=True)
    BASE = vstage()
    tmp = os.path.join(OUT, "_frames")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    audio, n = [], 0
    # 冒頭0.5秒:縦サムネイル(表紙に選べるように。音なし)
    cov = os.path.join(OUT, "_cover.png")
    cover(cov)
    for _ in range(int(COVER_SEC * FPS)):
        shutil.copy(cov, os.path.join(tmp, f"{n:05d}.png"))
        n += 1
    audio.append(np.zeros(int(round(int(COVER_SEC * FPS) / FPS * 24000)), dtype="float32"))
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
    out = os.path.join(OUT, "wine_short.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"), "-i", wav,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(tmp)
    print("done:", out, f"{n / FPS:.1f}秒")


if __name__ == "__main__":
    sys.exit(main())
