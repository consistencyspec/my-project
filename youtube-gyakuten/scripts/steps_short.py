"""一日1万歩の呪縛 のショート動画(縦 1080x1920・約45秒)。wine_short.py と同じ作り。

1965年の万歩計 → 研究のまとめで「必要派」が73議席まで勝つ流れを見せ、
1万歩の本当の出どころ・本当に必要な歩数・最終結果は隠して「続きは本編で」と誘導する(本編の答えは出さない)。
  .venv/bin/python scripts/steps_short.py           -> output/steps_short/steps_short.mp4
  .venv/bin/python scripts/steps_short.py --cover   -> output/thumbnails/steps_short.png(縦サムネイル)
声と読み方の設定は本編(steps_story.py)と同じ(一日=イチニチ、1万歩=イチマンポ、年=ネン、必要派・不要派)。
笑い声・はしゃいだ声は使わない。声を作るたびに voice_check.extra_sound() で余計な音を調べ、あれば作り直す。
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
import steps_story  # noqa: E402,F401  (本編の読み方の設定)
import steps_war as sw  # noqa: E402
import voice_check  # noqa: E402
import narrate  # noqa: E402,F401
from frames import (BAD, CURTAIN, CURTAIN_DARK, GOOD, INK, PANEL, STAGE, STAGE_LIGHT, SUB, TRIM, WHITE,  # noqa: E402
                    font, text)
from motion import angle_at, out_back, out_cubic, reverse_stamp, seats_motion, seg  # noqa: E402
from PIL import Image as _Image  # noqa: E402

# 「必要派」の派を「は」と読ませる(本編の場面19と同じ辞書)
steps_story.SCENE_TONE["必要派が73議席"] = ["必要派/ひつようは"]
LABELS = ("必要派", "不要派")

W, H = 1080, 1920
FPS = 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "steps_short")
COVER_SEC = 0.5   # 冒頭にサムネイルを出す秒数
FINAL = 50   # 最後の場面:議席は互角の形で見せ、数は「？」で隠す
LEAD, TAIL = 0.2, 0.35

# 場面:(見出し, 年のチップ, パネルの文, [(議席が動き始める割合, 前, 後)], ナレーション)
SCENES = [
    ("一日1万歩の\n呪縛", None, None, [], 50,
     "「一日1万歩、歩きましょう」。毎日、歩数を気にしていませんか？ 実はこの1万歩、思わぬところから生まれた数字だったんです。"),
    ("1965年", "1965年", "万歩計の誕生\n合言葉は一日1万歩", [(0.4, 50, 53)], None,
     "1965年、日本で「万歩計」が発売されます。合言葉は、一日1万歩。"),
    ("研究のまとめ", None, "2004・2007年\n1万歩は大人の目安", [(0.15, 53, 63), (0.5, 63, 73)], None,
     "やがて研究者たちも、1万歩は健康な大人の目安、とまとめ、必要派が73議席の圧勝です。"),
    ("その後", None, "1万歩の根拠を調べた\n研究者が見たものは…", [(0.1, 73, 67), (0.45, 67, 61)], None,
     "ところが、1万歩の根拠を調べた研究者が、意外なものにたどり着きます。日本の国の目安も、のちに大きく変わりました。"),
    ("本当に必要なのは？", None, "1万歩の出どころと\n本当に必要な歩数は本編で", [], FINAL,
     "1万歩の本当の出どころと、本当に必要な歩数は、本編で。"),
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
        dl = ImageDraw.Draw(lay)
        sw.pedometer(dl, W / 2 - 170, 640, 270)
        sw.walker(dl, W / 2 + 190, 470, 330, fill=(255, 226, 196))
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
    for x, lab, n, c in ((cx - R * 0.72, LABELS[0], shown, GOOD), (cx + R * 0.72, LABELS[1], 100 - shown, BAD)):
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
    """ショート用の縦サムネイル(1080x1920)。赤ワインのショートと同じ組み方。答え(出どころ・必要な歩数)は出さない。"""
    im = vstage()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 260), "新常識クロニクル", 64, TRIM, anchor="mm")
    text(d, (W / 2, 440), "一日1万歩の", 140, WHITE, anchor="mm")
    text(d, (W / 2, 630), "呪縛", 170, GOOD, anchor="mm")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    sw.pedometer(dl, W / 2 - 190, 960, 300)
    sw.walker(dl, W / 2 + 200, 780, 360, fill=(255, 226, 196))
    im = im.convert("RGBA")
    im.alpha_composite(lay)
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([90, 1210, W - 90, 1420], radius=40, fill=(220, 60, 60))
    text(d, (W / 2, 1270), "その1万歩、どこから来た？", 60, WHITE, anchor="mm")
    text(d, (W / 2, 1365), "本当に必要なのは…", 76, WHITE, anchor="mm")
    for cx, lab, c in ((W / 2 - 230, LABELS[0], GOOD), (W / 2 + 230, LABELS[1], BAD)):
        d.rounded_rectangle([cx - 160, 1530, cx + 160, 1640], radius=55, fill=c)
        text(d, (cx, 1585), lab, 64, WHITE, anchor="mm")
    text(d, (W / 2, 1585), "vs", 60, TRIM, anchor="mm")
    im.save(path)
    return path


def main():
    if "--cover" in sys.argv:
        os.makedirs(os.path.join(OUT, "..", "thumbnails"), exist_ok=True)
        print(cover(os.path.join(OUT, "..", "thumbnails", "steps_short.png")))
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
        for k in range(5):   # 笑い声などの余計な音があれば作り直す(今後一切入れない)
            bad = voice_check.extra_sound(v, 24000)
            if bad is None:
                break
            print(f"  ! 場面{i} 余計な音 {bad} → 作り直し", flush=True)
            v = cs.voice_for(i, sc[5], os.path.join(OUT, "voice"), fresh=True)
        else:
            raise SystemExit(f"場面{i}: 余計な音のない声が作れなかった")
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
    out = os.path.join(OUT, "steps_short.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"), "-i", wav,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(tmp)
    print("done:", out, f"{n / FPS:.1f}秒")


if __name__ == "__main__":
    sys.exit(main())
