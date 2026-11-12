#!/usr/bin/env python3
"""ショート動画「こんな時スペイン語でなんて言う？」を作る（縦長 1080x1920、約25〜35秒）。

使い方:
    python3 scripts/build_short.py content/shorts/s01_sorena.json
    python3 scripts/build_short.py content/shorts/*.json

流れ:
    1. お題（日本語の言葉を大きく）
    2. 直訳すると…（ありがちな間違い。台本に literal がある回だけ）
    3. 自然な言い方（ふつう → ゆっくり）＋ほかの言い方
    4. 使ってみよう（2人の短いやりとり）
    5. ひとことメモ ＋ フォローの呼びかけ

できるもの（output/shorts/<id>/）: <id>.mp4、description.txt（タイトル・概要欄・ハッシュタグ）
"""
import argparse
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw

import build_video as bv
from thumbnail import heavy_font

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "shorts"

SW, SH = 1080, 1920
MARGIN = 90           # 左右の余白
SAFE_BOTTOM = 1480    # これより下は YouTube のボタンや説明文で隠れるので、文字を置かない
SERIES = "スペイン語でなんて言う？"

RED = (214, 32, 39)
YELLOW = (255, 214, 0)
WHITE = (255, 255, 255)
INK = (20, 20, 20)
BG = (24, 32, 44)
SUB = (178, 190, 205)
VOICE_COLOR = {"F": (240, 128, 112), "M": (88, 190, 180)}

HOOK_SECONDS = 2.8
GAP = 0.7
END_SECONDS = 3.8


# ---------- 台本 ----------

def load_short(path):
    s = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_short(s)
    return s


def validate_short(s):
    for key in ("id", "word", "answer", "example", "tip"):
        if key not in s:
            raise ValueError(f"台本に「{key}」がありません")
    if s["answer"].get("voice") not in bv.SPEAKER_IDS:
        raise ValueError("answer の voice は F か M にしてください")
    if not 1 <= len(s["example"]) <= 3:
        raise ValueError("example（やりとり）は1〜3行にしてください")
    for ln in s["example"]:
        if ln.get("voice") not in bv.SPEAKER_IDS or not ln.get("es") or not ln.get("ja"):
            raise ValueError("example の各行には voice（F/M）・es・ja が必要です")


# ---------- 効果音 ----------

def write_chime(path, rate, seconds=0.45):
    """場面の切り替えに鳴らす、やわらかい2音のチャイム。"""
    n = int(rate * seconds)
    frames = bytearray()
    for i in range(n):
        t = i / rate
        f = 880 if t < seconds / 2 else 1320
        env = math.exp(-6 * (t % (seconds / 2)))
        frames += struct.pack("<h", int(9000 * env * math.sin(2 * math.pi * f * t)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return path


# ---------- 画面 ----------

def canvas(s):
    img = Image.new("RGB", (SW, SH), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SW, 250], fill=RED)
    d.rectangle([0, 250, SW, 262], fill=YELLOW)
    f1, f2 = heavy_font(44), heavy_font(70)
    d.text((MARGIN, 40), "こんな時", font=f1, fill=YELLOW)
    d.text((MARGIN, 110), SERIES, font=f2, fill=WHITE)
    tag = f"#{s['id'][1:]}"
    ft = heavy_font(40)
    d.text((SW - MARGIN - ft.getlength(tag), 48), tag, font=ft, fill=WHITE)
    return img, d


def centered(d, y, text, f, fill, stroke=0, stroke_fill=INK):
    x = (SW - f.getlength(text)) / 2
    d.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def fit_heavy(text, max_w, start=230, minimum=90):
    for size in range(start, minimum, -6):
        f = heavy_font(size)
        if f.getlength(text) <= max_w:
            return f
    return heavy_font(minimum)


def slide_hook(s, path):
    img, d = canvas(s)
    word = f"「{s['word']}」"
    f = fit_heavy(word, SW - 2 * MARGIN)
    f2 = heavy_font(84)
    y = 300 + (SAFE_BOTTOM - 300 - (f.size + 70 + 220)) // 2
    centered(d, y, word, f, WHITE, stroke=max(6, f.size // 16))
    centered(d, y + f.size + 70, "って、スペイン語で", f2, YELLOW)
    centered(d, y + f.size + 70 + 110, "なんて言う？", f2, YELLOW)
    img.save(path)


def compose(s, label, body, path, measure=None):
    """見出しと中身を、安全な範囲（上の帯の下〜ボタンで隠れない高さ）の中で上下中央にそろえる。

    body(d, y) は y から描いて、描き終わりの高さを返す関数。
    measure を渡すと、その関数で高さを測る（やりとりが1行ずつ増えても位置が動かないように）。
    """
    probe = ImageDraw.Draw(Image.new("RGB", (SW, SH)))
    height = (measure or body)(probe, 0)
    label_h = 100 if label else 0
    top = 300
    y = top + max(0, (SAFE_BOTTOM - top - height - label_h) // 2)
    img, d = canvas(s)
    if label:
        d.text((MARGIN, y), label, font=heavy_font(52), fill=YELLOW)
        y += label_h
    body(d, y)
    img.save(path)


def slide_literal(s, path):
    lit = s["literal"]

    def body(d, y):
        fe = bv.font(bv.FONT_ES_BOLD, 88)
        y = bv.draw_lines(d, bv.wrap(lit["es"], fe, SW - 2 * MARGIN), fe, MARGIN, y, WHITE, 18)
        fx = heavy_font(200)
        centered(d, y + 20, "×", fx, RED)
        fj = bv.font(bv.FONT_JA, 54)
        return bv.draw_lines(d, bv.wrap(lit["ja"], fj, SW - 2 * MARGIN, by_char=True), fj, MARGIN, y + 290, SUB, 16)

    compose(s, "直訳すると…", body, path)


def slide_answer(s, path, tag):
    a = s["answer"]
    alts = s.get("alternatives", [])

    def body(d, y):
        d.text((MARGIN, y), tag, font=bv.font(bv.FONT_JA, 44), fill=SUB)
        y += 80
        fe = bv.font(bv.FONT_ES_BOLD, 112)
        rows = bv.wrap(a["es"], fe, SW - 2 * MARGIN)
        if len(rows) > 2:
            fe = bv.font(bv.FONT_ES_BOLD, 84)
            rows = bv.wrap(a["es"], fe, SW - 2 * MARGIN)
        y = bv.draw_lines(d, rows, fe, MARGIN, y, YELLOW, 20)
        fj = heavy_font(64)
        y = bv.draw_lines(d, bv.wrap(a["ja"], fj, SW - 2 * MARGIN, by_char=True), fj, MARGIN, y + 40, WHITE, 16)
        if alts:
            y += 80
            d.text((MARGIN, y), "こんな言い方も", font=heavy_font(46), fill=YELLOW)
            y += 80
            fa, fj2 = bv.font(bv.FONT_ES_BOLD, 60), bv.font(bv.FONT_JA, 44)
            for alt in alts:
                y = bv.draw_lines(d, bv.wrap(alt["es"], fa, SW - 2 * MARGIN), fa, MARGIN, y, WHITE, 10)
                y = bv.draw_lines(d, bv.wrap(alt["ja"], fj2, SW - 2 * MARGIN, by_char=True), fj2, MARGIN, y + 8, SUB, 8) + 34
        return y

    compose(s, "自然な言い方は", body, path)


def slide_example(s, path, upto):
    """やりとりを1行ずつ増やして見せる。今話している行だけ明るくする。"""
    fe, fj = bv.font(bv.FONT_ES, 66), bv.font(bv.FONT_JA, 48)

    def bubbles(d, y, count, active):
        for i, ln in enumerate(s["example"][:count]):
            current = i == active
            color = VOICE_COLOR[ln["voice"]] if current else (95, 105, 120)
            es_rows = bv.wrap(ln["es"], fe, SW - 2 * MARGIN - 60)
            ja_rows = bv.wrap(ln["ja"], fj, SW - 2 * MARGIN - 60, by_char=True)
            h = len(es_rows) * 86 + len(ja_rows) * 62 + 76
            d.rounded_rectangle([MARGIN - 20, y, SW - MARGIN + 20, y + h], radius=28,
                                outline=color, width=6, fill=(34, 45, 61))
            yy = bv.draw_lines(d, es_rows, fe, MARGIN + 30, y + 28, WHITE if current else SUB, 20)
            bv.draw_lines(d, ja_rows, fj, MARGIN + 30, yy + 12, SUB, 14)
            y += h + 44
        return y

    compose(s, "使ってみよう", lambda d, y: bubbles(d, y, upto + 1, upto), path,
            measure=lambda d, y: bubbles(d, y, len(s["example"]), -1))


def slide_end(s, path):
    def body(d, y):
        fj = bv.font(bv.FONT_JA, 56)
        y = bv.draw_lines(d, bv.wrap(s["tip"], fj, SW - 2 * MARGIN, by_char=True), fj, MARGIN, y, WHITE, 24)
        y += 110
        d.rounded_rectangle([MARGIN - 20, y, SW - MARGIN + 20, y + 270], radius=30, fill=RED)
        centered(d, y + 42, "フォローして", heavy_font(68), WHITE)
        centered(d, y + 146, "毎日1フレーズ覚えよう", heavy_font(68), YELLOW)
        return y + 270

    compose(s, "ひとことメモ", body, path)


# ---------- 組み立て ----------

def build(path, keep_work=False):
    s = load_short(path)
    out = OUT_DIR / s["id"]
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"{s['id']}_"))
    speaker = bv.Speaker(ROOT / "output" / ".tts_cache")
    a = s["answer"]
    first = speaker.say(a["es"], a["voice"])
    with wave.open(str(first), "rb") as w:
        rate = w.getframerate()
    chime = write_chime(work / "chime.wav", rate)
    tl = bv.Timeline(rate)
    n = [0]

    def img():
        n[0] += 1
        return work / f"s{n[0]:03d}.png"

    p = img(); slide_hook(s, p); tl.add(p, [chime, HOOK_SECONDS - bv.wav_seconds(chime)])
    if s.get("literal"):
        p = img(); slide_literal(s, p)
        tl.add(p, [speaker.say(s["literal"]["es"], a["voice"]), 2.2])
    p = img(); slide_answer(s, p, "ふつうの速さ"); tl.add(p, [chime, 0.2, first, GAP])
    p = img(); slide_answer(s, p, "ゆっくり"); tl.add(p, [speaker.say(a["es"], a["voice"], slow=True), 1.2])
    for i, ln in enumerate(s["example"]):
        p = img(); slide_example(s, p, i)
        tl.add(p, [speaker.say(ln["es"], ln["voice"]), GAP + (0.6 if i == len(s["example"]) - 1 else 0)])
    p = img(); slide_end(s, p); tl.add(p, [chime, END_SECONDS - bv.wav_seconds(chime)])

    audio = work / "audio.wav"
    tl.write_audio(audio)
    concat = work / "slides.txt"
    durs = tl.video_durations()
    with open(concat, "w", encoding="utf-8") as f:
        for image, dur in durs:
            f.write(f"file '{image}'\nduration {dur:.6f}\n")
        f.write(f"file '{durs[-1][0]}'\n")
    mp4 = out / f"{s['id']}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(audio), "-fps_mode", "cfr", "-r", str(bv.FPS), "-c:v", "libx264",
                    "-tune", "stillimage", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", str(mp4)], check=True)
    (out / "description.txt").write_text(description(s), encoding="utf-8")
    if keep_work:
        shutil.copytree(work, out / "work", dirs_exist_ok=True)
    shutil.rmtree(work, ignore_errors=True)
    print(f"できました: {mp4}（{tl.now:.1f}秒）")
    return mp4, tl.now


def description(s):
    a = s["answer"]
    lines = [
        f"「{s['word']}」ってスペイン語でなんて言う？ #shorts #スペイン語",
        "",
        f"答え: {a['es']}（{a['ja']}）",
    ]
    for alt in s.get("alternatives", []):
        lines.append(f"ほかにも: {alt['es']}（{alt['ja']}）")
    lines += ["", "■ 使ってみよう"]
    lines += [f"{ln['es']}\n　{ln['ja']}" for ln in s["example"]]
    lines += ["", f"メモ: {s['tip']}", "", "#スペイン語勉強 #スペイン語会話 #語学 #こんな時スペイン語で",
              "", bv.VOICE_CREDIT]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="ショート動画「こんな時スペイン語でなんて言う？」を作る")
    ap.add_argument("shorts", nargs="+", help="台本の JSON（content/shorts/ 以下）")
    ap.add_argument("--keep-work", action="store_true", help="途中の画像を output/shorts/<id>/work に残す")
    args = ap.parse_args(argv)
    for p in args.shorts:
        build(p, keep_work=args.keep_work)


if __name__ == "__main__":
    sys.exit(main())
