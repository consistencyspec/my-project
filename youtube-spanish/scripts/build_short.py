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

import hashlib
import os

import build_video as bv
import character as ch
import commentary as cm
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
GAP_JA_ES = 1.0     # 日本語ナレーションとスペイン語の間

# キャラクター（オラポン君）。画面の下（ボタンで隠れない範囲の一番下）に立たせる
CHAR_W = 440
CHAR_H = ch.height_for(CHAR_W)
CHAR_X = (SW - CHAR_W) // 2
CHAR_Y = SAFE_BOTTOM - CHAR_H
SHOW_CHARACTER = True  # build() で切り替える


def content_bottom():
    """文字を置いてよい範囲の下端。キャラクターを出すときは、その頭の上まで。"""
    return CHAR_Y - 20 if SHOW_CHARACTER else SAFE_BOTTOM

# 日本語ナレーション（Kokoro, Apache-2.0）。Kokoro を入れた Python を環境変数 JA_TTS_PYTHON で指定する
JA_VOICE = os.environ.get("JA_VOICE", "jf_alpha")
# オラポン君の声：高い声のおじさん。女性の声を少しだけ低くし、声の響き（フォルマント）も一緒に下げて男性っぽくする。
# 機械的に聞こえないよう、ピッチの変更は Rubber Band（ffmpeg の rubberband フィルター）で行う
JA_PITCH = float(os.environ.get("JA_PITCH", "-2"))   # 半音（+で高く、-で低く）。0 で元の声のまま
JA_FORMANT = os.environ.get("JA_FORMANT", "shifted")  # shifted＝響きも一緒に動かす / preserved＝響きはそのまま
JA_TEMPO = float(os.environ.get("JA_TEMPO", "1.0"))  # 話す速さ
# キャラ設定のリアクション：正解は「ポン！」（不正解の「ポ〜ン…」は、ポンが多すぎるので使わない。表情だけでしょんぼりする）
REACT_WRONG = ""
REACT_RIGHT = "ポン！"
JA_TTS_PYTHON = os.environ.get("JA_TTS_PYTHON", sys.executable)
SAY_JA = Path(__file__).resolve().parent / "say_ja.py"


def narration_lines(s):
    """ショートの日本語ナレーション（最初のお題・最後のひとこと）。台本の narration で上書きできる。"""
    n = s.get("narration", {})
    word = s["word"].split("（")[0]
    hook = n.get("hook", f"「{word}」って、スペイン語でなんて言うと思いますか？")
    end = n.get("end", "")
    return hook, end


def ja_say(text, rate, cache_dir, voice=None):
    """日本語を読み上げ、合成スペイン語と同じ形式・同じ音量の wav にする（同じ文はキャッシュを使う）。"""
    voice = voice or JA_VOICE
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"kokoro|{voice}|rb|{JA_PITCH}|{JA_FORMANT}|{JA_TEMPO}|{text}".encode()).hexdigest()[:16]
    out = cache_dir / f"ja_{key}.wav"
    if not out.exists():
        raw = cache_dir / f"ja_{key}_raw.wav"
        subprocess.run([JA_TTS_PYTHON, str(SAY_JA), voice, str(raw), text], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        voice_fx = (f"rubberband=pitch={2 ** (JA_PITCH / 12):.6f}:tempo={JA_TEMPO:.4f}:"
                    f"formant={JA_FORMANT}:pitchq=quality," if (JA_PITCH or JA_TEMPO != 1.0) else "")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", voice_fx + "loudnorm=I=-14:TP=-1.5:LRA=7",
                        "-ac", "1", "-ar", str(rate), "-sample_fmt", "s16", str(out)], check=True)
        raw.unlink(missing_ok=True)
    return out


# ---------- 台本 ----------

def load_short(path):
    s = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_short(s)
    return s


def validate_short(s):
    n = s.get("narration", {})
    if not isinstance(n, dict) or any(k not in ("hook", "end") for k in n):
        raise ValueError("narration には hook（最初）と end（最後）だけを書いてください")
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
    y = 300 + max(0, (content_bottom() - 300 - (f.size + 70 + 220)) // 2)
    centered(d, y, word, f, WHITE, stroke=max(6, f.size // 16))
    centered(d, y + f.size + 70, "って、スペイン語で", f2, YELLOW)
    centered(d, y + f.size + 70 + 110, "なんて言う？", f2, YELLOW)
    img.save(path)


def compose(s, label, body, path, measure=None):
    """見出しと中身を、文字を置いてよい範囲（上の帯の下〜キャラクターの頭の上）の中で上下中央にそろえる。

    body(d, y) は y から描いて、描き終わりの高さを返す関数。
    measure を渡すと、その関数で高さを測る（やりとりが1行ずつ増えても位置が動かないように）。
    中身が範囲に入りきらないときは、全体を少し縮めて収める。
    """
    label_h = 100 if label else 0
    probe = ImageDraw.Draw(Image.new("RGB", (SW, 10)))
    height = (measure or body)(probe, 0) + label_h
    top, bottom = 300, content_bottom()
    scale = min(1.0, (bottom - top) / max(1, height))
    layer = Image.new("RGBA", (SW, int(height) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if label:
        d.text((MARGIN, 0), label, font=heavy_font(52), fill=YELLOW)
    body(d, label_h)
    if scale < 1.0:
        layer = layer.resize((int(SW * scale), int(layer.height * scale)), Image.LANCZOS)
    x = (SW - layer.width) // 2
    y = top + max(0, int((bottom - top - height * scale) // 2))
    img, _ = canvas(s)
    img.paste(layer, (x, y), layer)
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


# ---------- キャラクター ----------

def with_character(base_path, face, cache):
    """スライドにキャラクターを重ねた画像。face は表情名か ("talk", 口の形)。同じ組み合わせは使い回す。"""
    key = (str(base_path), face)
    if key not in cache:
        img = Image.open(base_path).convert("RGBA")
        sprite = ch.talking(face[1], CHAR_W) if isinstance(face, tuple) else ch.expression(face, CHAR_W)
        img.alpha_composite(sprite, (CHAR_X, CHAR_Y))
        out = Path(base_path).with_name(Path(base_path).stem + f"_{face[1] if isinstance(face, tuple) else face}.png")
        img.convert("RGB").save(out)
        cache[key] = out
    return cache[key]


def add_talking(tl, base, wav, before, after, after_face, work, cache):
    """ナレーションに合わせて口パクさせながら、タイムラインに積む。"""
    if not SHOW_CHARACTER:
        tl.add(base, before + [wav] + after)
        return
    tl.add(with_character(base, ("talk", "n"), cache), before)
    track, frame_sec = ch.mouth_track(wav)
    groups = ch.runs(track)
    starts, t = [], 0.0
    for _, count in groups:
        starts.append(t)
        t += count * frame_sec
    sub = Path(work) / f"lip_{Path(base).stem}"
    sub.mkdir(exist_ok=True)
    for (mouth, _), part in zip(groups, cm.split_wav(wav, starts, sub)):
        tl.add(with_character(base, ("talk", mouth), cache), [part])
    tl.add(with_character(base, after_face, cache), after)


def show(base, face, cache):
    return with_character(base, face, cache) if SHOW_CHARACTER else base


# ---------- 組み立て ----------

def build(path, keep_work=False, narration=True, character=True):
    global SHOW_CHARACTER
    SHOW_CHARACTER = character
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

    hook_text, end_text = narration_lines(s)
    cache = ROOT / "output" / ".tts_cache"
    faces = {}
    # 1. お題（手を振りながら話す）
    p = img(); slide_hook(s, p)
    if narration:
        add_talking(tl, p, ja_say(hook_text, rate, cache), [chime, 0.2], [GAP_JA_ES], ("talk", "n"), work, faces)
    else:
        tl.add(show(p, "normal", faces), [chime, HOOK_SECONDS - bv.wav_seconds(chime)])
    # 2. 直訳すると…（しょんぼりして「ポーン…」）
    if s.get("literal"):
        p = img(); slide_literal(s, p)
        lit = speaker.say(s["literal"]["es"], a["voice"])
        if narration and REACT_WRONG:
            tl.add(show(p, "shonbori", faces), [lit, GAP_JA_ES, ja_say(REACT_WRONG, rate, cache), 1.0])
        else:
            tl.add(show(p, "shonbori", faces), [lit, 2.2])
    # 3. 自然な言い方（決め顔で「ポン！」）
    p = img(); slide_answer(s, p, "ふつうの速さ")
    if narration:
        tl.add(show(p, "kimegao", faces), [chime, 0.2, ja_say(REACT_RIGHT, rate, cache), GAP_JA_ES, first, GAP])
    else:
        tl.add(show(p, "kimegao", faces), [chime, 0.2, first, GAP])
    p = img(); slide_answer(s, p, "ゆっくり")
    tl.add(show(p, "kimegao", faces), [speaker.say(a["es"], a["voice"], slow=True), 1.2])
    # 4. 使ってみよう（通常）
    for i, ln in enumerate(s["example"]):
        p = img(); slide_example(s, p, i)
        tl.add(show(p, "normal", faces), [speaker.say(ln["es"], ln["voice"]), GAP + (0.6 if i == len(s["example"]) - 1 else 0)])
    # 5. ひとことメモ（話して、最後はドヤ顔）
    p = img(); slide_end(s, p)
    if narration and end_text:
        add_talking(tl, p, ja_say(end_text, rate, cache), [chime, 0.4], [1.2], "doya", work, faces)
    else:
        tl.add(show(p, "doya", faces), [chime, END_SECONDS - bv.wav_seconds(chime)])

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
    ap.add_argument("--no-narration", action="store_true", help="日本語ナレーションを付けない")
    ap.add_argument("--no-character", action="store_true", help="キャラクター（オラポン君）を出さない")
    args = ap.parse_args(argv)
    for p in args.shorts:
        build(p, keep_work=args.keep_work, narration=not args.no_narration, character=not args.no_character)


if __name__ == "__main__":
    sys.exit(main())
