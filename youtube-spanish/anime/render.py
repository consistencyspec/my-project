#!/usr/bin/env python3
"""アニメ「オラポン一家」を、台本（JSON）から動画にする（16:9、1920x1080）。

使い方:
    JA_TTS_PYTHON=<Kokoro を入れた Python> python3 anime/render.py anime/ep01.json

流れ: タイトル → 本編（シーンごとに、話す人・表情・セリフ・効果音・車の動き）
      → きょうのスペイン語（キーフレーズを ふつう → ゆっくり → 言ってみよう でくり返し、最後にまとめ）→ つづく（次回予告）

動き:
- 話している人は軽くはずむ。オラポン君は「talk」の顔のとき、声に合わせて口パク
- 「ぶるぶる」の顔のペロは小刻みに震える。出てくるときは下からひょこっと
- 車は左から走ってきて止まり、故障するとガタガタ揺れる
"""
import hashlib
import io
import json
import math
import os
import random
import subprocess
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_video as bv  # noqa: E402  合成スペイン語（Piper）
import character as ch  # noqa: E402  オラポン君の口パク
from thumbnail import heavy_font  # noqa: E402

W, H, FPS, RATE = 1920, 1080, 24, 24000
CHARS = ROOT / "characters"
CACHE = ROOT / "output" / ".tts_cache" / "anime"
OUT_DIR = ROOT / "output" / "anime"
JA_TTS_PYTHON = os.environ.get("JA_TTS_PYTHON", sys.executable)
SAY_JA = ROOT / "scripts" / "say_ja.py"
INK, YELLOW, RED, WHITE = (42, 26, 18), (245, 183, 0), (215, 38, 61), (255, 255, 255)

# 登場人物：名前の表示・色・声（ja=日本語の声、es=スペイン語の声）
CAST = {
    "olapon": {"name": "オラポン君", "color": YELLOW, "ja": ("jf_alpha", -2), "es": ("M", 0)},
    "dolores": {"name": "ドローレス", "color": RED, "ja": ("jf_gongitsune", -1), "es": ("F", 0)},
    "bebe": {"name": "ベベ", "color": (242, 135, 138), "ja": ("jf_nezumi", 4), "es": ("F", 4)},
    "pero": {"name": "ペロ", "color": (233, 185, 122), "ja": ("jf_tebukuro", 4), "es": ("F", 6)},
}
# 立ち位置（横の中心、幅）。下端は画面の下にそろえる
POS = {"dolores": (330, 470), "olapon": (790, 450), "bebe": (1130, 230), "pero": (1440, 310)}
POS_WITH_CAR = {"dolores": (230, 440), "olapon": (600, 430), "bebe": (1130, 230), "pero": (1440, 310)}
CAR_W, CAR_X, CAR_BOTTOM = 980, 1200, 1010
GAP_PART, GAP_EVENT = 0.15, 0.55


# ---------- 音 ----------

def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _finish(src, dst, pitch=0.0, formant="shifted"):
    """24kHz・モノラルにそろえ、必要なら高さを変え、音量をそろえる。"""
    fx = (f"rubberband=pitch={2 ** (pitch / 12):.6f}:formant={formant}:pitchq=quality," if pitch else "")
    _run(["ffmpeg", "-y", "-i", str(src), "-af", fx + "loudnorm=I=-15:TP=-1.5:LRA=7",
          "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", str(dst)])
    return Path(dst)


def ja_voice(text, voice, pitch):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"ja|{voice}|{pitch}|{text}".encode()).hexdigest()[:16]
    out = CACHE / f"ja_{key}.wav"
    if not out.exists():
        raw = CACHE / f"ja_{key}_raw.wav"
        _run([JA_TTS_PYTHON, str(SAY_JA), voice, str(raw), text])
        _finish(raw, out, pitch)
        raw.unlink(missing_ok=True)
    return out


_speaker = None


def es_voice(text, voice, pitch=0.0, slow=False):
    global _speaker
    if _speaker is None:
        _speaker = bv.Speaker(ROOT / "output" / ".tts_cache")
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"es|{voice}|{pitch}|{slow}|{text}".encode()).hexdigest()[:16]
    out = CACHE / f"es_{key}.wav"
    if not out.exists():
        _finish(_speaker.say(text, voice, slow=slow), out, pitch)
    return out


def _write(path, x):
    y = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return Path(path)


def sfx(name):
    """効果音。声で作るもの（ニワトリ・犬・赤ちゃん）と、計算で作るもの（車の音）がある。"""
    CACHE.mkdir(parents=True, exist_ok=True)
    if name == "rooster":
        return es_voice("¡Quiquiriquí!", "M", 5)
    if name == "bark":
        return es_voice("¡Guau!", "F", 6)
    if name == "baby_cry":
        return ja_voice("ふぇーん、ふぇーん", "jf_nezumi", 5)
    out = CACHE / f"sfx_{name}.wav"
    if out.exists():
        return out
    rnd = np.random.default_rng(1)
    if name == "engine":  # ブロロロ…（低いエンジン音）
        t = np.arange(int(RATE * 2.6)) / RATE
        f = 38 + 6 * np.sin(2 * np.pi * 1.5 * t)
        saw = 2 * ((np.cumsum(f) / RATE) % 1) - 1
        x = 0.5 * saw * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t)) + 0.08 * rnd.standard_normal(len(t))
        x *= np.minimum(1, t / 0.3) * np.minimum(1, (t[-1] - t) / 0.3)
    elif name == "pusun":  # プスン（音が下がって止まる）
        t = np.arange(int(RATE * 0.7)) / RATE
        f = 120 * np.exp(-3 * t)
        x = 0.6 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * np.exp(-2.5 * t)
    elif name == "boom":  # ボンッ（爆発）
        t = np.arange(int(RATE * 0.9)) / RATE
        x = (0.9 * rnd.standard_normal(len(t)) + 0.8 * np.sin(2 * np.pi * 55 * t)) * np.exp(-6 * t)
    elif name == "chime":
        t = np.arange(int(RATE * 0.6)) / RATE
        f = np.where(t < 0.3, 880, 1320)
        x = 0.35 * np.sin(2 * np.pi * f * t) * np.exp(-6 * (t % 0.3))
    else:
        raise ValueError(f"知らない効果音です: {name}")
    return _write(out, x / (np.abs(x).max() + 1e-9) * 0.8)


def seconds(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def concat(clips, path):
    """[(wav or 無音の秒数), ...] を1本の wav にする。"""
    xs = []
    for c in clips:
        if isinstance(c, (int, float)):
            xs.append(np.zeros(int(RATE * c), np.float32))
        else:
            with wave.open(str(c), "rb") as w:
                xs.append(np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768)
    return _write(path, np.concatenate(xs) if xs else np.zeros(1, np.float32))


# ---------- 絵 ----------

def _svg(path, width):
    import cairosvg
    return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=width))).convert("RGBA")


@lru_cache(maxsize=256)
def sprite(who, face, width):
    """キャラクターの絵。face は表情名（ファイル名の番号のあと）か、オラポン君の口パク用 ("talk", 口の形)。"""
    if isinstance(face, tuple):
        return ch.talking(face[1], width)
    files = {p.stem.split("_", 1)[1]: p for p in (CHARS / who / "expressions").glob("*.svg")}
    if face not in files:
        raise ValueError(f"{who} に「{face}」の表情がありません（{', '.join(files)}）")
    return _svg(files[face], width)


@lru_cache(maxsize=8)
def car_sprite(broken):
    return _svg(CHARS / "car" / ("02_enko.svg" if broken else "01_hashiru.svg"), CAR_W)


@lru_cache(maxsize=4)
def background(name):
    if name == "house":
        p = CHARS / "scenes" / "house_garden.png"
        if not p.exists():
            import cairosvg
            cairosvg.svg2png(url=str(CHARS / "scenes" / "house_garden.svg"), write_to=str(p), output_width=W)
        return Image.open(p).convert("RGBA").resize((W, H))
    raise ValueError(f"知らない背景です: {name}")


@lru_cache(maxsize=4)
def dimmed(name):
    img = background(name).copy()
    img.alpha_composite(Image.new("RGBA", (W, H), (20, 25, 40, 150)))
    return img


def wrap_text(text, font, width):
    rows, cur = [], ""
    for c in text:
        if cur and font.getlength(cur + c) > width and c not in "、。！？」）…":
            rows.append(cur)
            cur = c
        else:
            cur += c
    return rows + ([cur] if cur else [])


@lru_cache(maxsize=256)
def subtitle(who, text):
    """画面の上に出す字幕（名前のラベル＋セリフ）。"""
    f, fn = heavy_font(50), heavy_font(36)
    rows = wrap_text(text, f, W - 260)
    h = 70 + len(rows) * 66
    img = Image.new("RGBA", (W - 120, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 18, W - 121, h - 1], radius=26, fill=(255, 255, 255, 236), outline=INK, width=5)
    if who in CAST:
        name = CAST[who]["name"]
        d.rounded_rectangle([30, 0, 70 + fn.getlength(name), 50], radius=14, fill=CAST[who]["color"], outline=INK, width=4)
        d.text((50, 4), name, font=fn, fill=INK)
    y = 52
    for r in rows:
        d.text((50, y), r, font=f, fill=INK)
        y += 66
    return img


def card(lines):
    """きょうのスペイン語・つづく用の、文字だけのカード（透明の板）。lines は (文字, 大きさ, 色)。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    total = sum(s + 34 for _, s, _ in lines)
    y = (H - total) // 2 - 60
    for text, size, color in lines:
        f = heavy_font(size)
        while f.getlength(text) > W - 160 and size > 30:
            size -= 4
            f = heavy_font(size)
        d.text(((W - f.getlength(text)) / 2, y), text, font=f, fill=color, stroke_width=max(2, size // 22), stroke_fill=INK)
        y += size + 34
    return img


# ---------- 台本 → 時間割 ----------

class Plan:
    """音の時間割（どこで何を鳴らすか）と、画面の時間割（いつ何を見せるか）。"""

    def __init__(self):
        self.t = 0.0
        self.audio = []   # (開始秒, wav)
        self.shots = []   # dict(start, end, kind, ...)

    def add_audio(self, wav, at=None):
        self.audio.append((self.t if at is None else at, Path(wav)))


def event_audio(ev, tmp):
    """1つのセリフの音（日本語・スペイン語・効果音・間）をつないだもの。"""
    who = ev["who"]
    clips = []
    for i, part in enumerate(ev.get("parts", [])):
        if i:
            clips.append(GAP_PART)
        if "ja" in part:
            v, p = CAST[who]["ja"]
            clips.append(ja_voice(part["ja"], v, p))
        elif "es" in part:
            v, p = CAST[who]["es"] if who in CAST else ("F", 0)
            clips.append(es_voice(part["es"], v, p))
        elif "sfx" in part:
            clips.append(sfx(part["sfx"]))
        elif "pause" in part:
            clips.append(part["pause"])
    key = hashlib.sha1(json.dumps(ev, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    return concat(clips or [0.5], Path(tmp) / f"ev_{key}.wav")


def default_text(ev):
    out = []
    for p in ev.get("parts", []):
        out.append(p.get("ja") or p.get("es") or "")
    return "".join(out)


def build_plan(ep, tmp):
    plan = Plan()
    # タイトル
    plan.add_audio(sfx("chime"))
    plan.shots.append({"start": 0, "end": 3.0, "kind": "title", "ep": ep})
    plan.t = 3.0
    state = {"visible": set(ep.get("start", {})), "faces": dict(ep.get("start", {})), "car": None}
    for scene in ep["scenes"]:
        for ev in scene["events"]:
            for who in ev.get("show", []):
                state["visible"].add(who)
                state["faces"].setdefault(who, "normal")
            for who in ev.get("hide", []):
                state["visible"].discard(who)
            for who, face in ev.get("set", {}).items():
                state["faces"][who] = face
            if ev.get("action") == "car_drive":
                state["car"] = "drive"
            elif ev.get("action") == "car_break":
                state["car"] = "broken"
            wav = event_audio(ev, tmp)
            dur = seconds(wav)
            who, face = ev["who"], ev.get("face")
            shot = {"start": plan.t, "end": plan.t + dur + GAP_EVENT, "kind": "story", "bg": scene["bg"],
                    "who": who, "face": face, "visible": set(state["visible"]), "faces": dict(state["faces"]),
                    "car": state["car"], "action": ev.get("action"), "text": ev.get("text") or default_text(ev),
                    "talk_until": plan.t + dur, "wav": wav}
            if who == "olapon" and face == "talk":
                shot["mouth"], shot["mouth_step"] = ch.mouth_track(wav, fps=FPS)
            plan.shots.append(shot)
            plan.add_audio(wav)
            plan.t += dur + GAP_EVENT
            if who in CAST and face:
                state["faces"][who] = "normal" if face == "talk" else face
            if state["car"] == "drive":
                state["car"] = "parked"
        plan.t += 0.4
    # きょうのスペイン語
    intro = ja_voice("きょうのスペイン語、いっしょに言ってみるポン！", *CAST["olapon"]["ja"])
    plan.add_audio(sfx("chime"))
    plan.add_audio(intro, plan.t + 0.6)
    d = 0.6 + seconds(intro) + 0.6
    plan.shots.append({"start": plan.t, "end": plan.t + d, "kind": "lesson_intro", "talk_from": plan.t + 0.6,
                       "talk_until": plan.t + 0.6 + seconds(intro), **dict(zip(("mouth", "mouth_step"), ch.mouth_track(intro, fps=FPS)))})
    plan.t += d
    voice = CAST["olapon"]["es"][0]
    for i, ph in enumerate(ep["phrases"], 1):
        normal, slow = es_voice(ph["es"], voice), es_voice(ph["es"], voice, slow=True)
        steps = [("ふつうの速さ", normal), ("ゆっくり", slow)]
        for label, wav in steps:
            plan.add_audio(wav)
            d = seconds(wav) + 0.8
            plan.shots.append({"start": plan.t, "end": plan.t + d, "kind": "phrase", "ph": ph, "i": i,
                               "n": len(ep["phrases"]), "label": label})
            plan.t += d
        d = seconds(normal) * 1.3 + 1.2  # 言ってみよう（無音）
        plan.shots.append({"start": plan.t, "end": plan.t + d, "kind": "phrase", "ph": ph, "i": i,
                           "n": len(ep["phrases"]), "label": "言ってみよう！", "countdown": True})
        plan.t += d
    # まとめ：3つを続けてもう一度
    for ph in ep["phrases"]:
        wav = es_voice(ph["es"], voice)
        plan.add_audio(wav)
        d = seconds(wav) + 0.7
        plan.shots.append({"start": plan.t, "end": plan.t + d, "kind": "review", "phrases": ep["phrases"], "current": ph})
        plan.t += d
    # つづく
    nxt = ep.get("next")
    if nxt:
        line = ja_voice(nxt["line"], *CAST["olapon"]["ja"])
        plan.add_audio(sfx("chime"))
        plan.add_audio(line, plan.t + 0.8)
        d = 0.8 + seconds(line) + 1.6
        plan.shots.append({"start": plan.t, "end": plan.t + d, "kind": "next", "next": nxt, "talk_from": plan.t + 0.8,
                           "talk_until": plan.t + 0.8 + seconds(line), **dict(zip(("mouth", "mouth_step"), ch.mouth_track(line, fps=FPS)))})
        plan.t += d
    return plan


# ---------- 1コマずつ描く ----------

def place(frame, img, cx, bottom, dy=0, dx=0):
    frame.alpha_composite(img, (int(cx - img.width / 2 + dx), int(bottom - img.height + dy)))


def mouth_at(shot, t, start_key="start"):
    track = shot.get("mouth")
    if not track:
        return "n"
    i = int((t - shot.get("talk_from", shot["start"])) / shot["mouth_step"])
    return track[i] if 0 <= i < len(track) else "n"


def draw_story(shot, t):
    frame = background(shot["bg"]).copy()
    pos = POS_WITH_CAR if shot["car"] else POS
    # 車（家族より奥）
    if shot["car"]:
        broken = shot["car"] == "broken"
        img = car_sprite(broken)
        x, dx, dy = CAR_X, 0, 0
        if shot["action"] == "car_drive":
            k = min(1, (t - shot["start"]) / max(0.1, shot["talk_until"] - shot["start"]))
            x = -CAR_W / 2 + (CAR_X + CAR_W / 2) * (1 - (1 - k) ** 2)
            dy = 4 * math.sin(t * 40)
        elif broken and shot["action"] == "car_break":
            amp = 10 * max(0, 1 - (t - shot["start"]) / 1.5)
            dx, dy = amp * math.sin(t * 60), amp * math.cos(t * 47)
        place(frame, img, x, CAR_BOTTOM, dy, dx)
    rnd = random.Random(int(t * FPS))
    for who in ("dolores", "olapon", "bebe", "pero"):
        if who not in shot["visible"]:
            continue
        cx, w = pos[who]
        face = shot["faces"].get(who, "normal")
        talking = who == shot["who"] and t < shot["talk_until"]
        if who == shot["who"] and shot["face"]:
            face = shot["face"]
        if face == "talk":
            face = ("talk", mouth_at(shot, t) if talking else "n")
        dy = -10 * abs(math.sin(2 * math.pi * 2.6 * (t - shot["start"]))) if talking else 0
        dx = rnd.uniform(-6, 6) if face == "buruburu" else 0
        # ひょこっと出てくる（このセリフで見えるようになった人）
        if who == shot["who"] and t - shot["start"] < 0.3 and shot.get("popped"):
            dy += 260 * (1 - (t - shot["start"]) / 0.3) ** 2
        place(frame, sprite(who, face, w), cx, H, dy, dx)
    frame.alpha_composite(subtitle(shot["who"], shot["text"]), (60, 26))
    return frame


def olapon_corner(frame, shot, t, face=None):
    talking = shot.get("talk_from", 0) <= t < shot.get("talk_until", 0)
    img = sprite("olapon", ("talk", mouth_at(shot, t) if talking else "n") if face is None else face, 380)
    dy = -8 * abs(math.sin(2 * math.pi * 2.6 * t)) if talking else 0
    place(frame, img, W - 250, H, dy)


def draw_frame(shot, t):
    k = shot["kind"]
    if k == "story":
        return draw_story(shot, t)
    frame = dimmed("house").copy()
    if k == "title":
        ep = shot["ep"]
        frame.alpha_composite(card([("オラポン一家", 72, YELLOW), (f"第{ep['number']}話", 64, WHITE), (ep["title"], 104, WHITE)]))
        a = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        family = [("dolores", "normal", 300, 520), ("olapon", "normal", 300, 830), ("bebe", "normal", 170, 1100), ("pero", "happy", 220, 1360)]
        for who, face, w, cx in family:
            place(a, sprite(who, face, w), cx, H)
        frame.alpha_composite(a)
    elif k == "lesson_intro":
        frame.alpha_composite(card([("きょうのスペイン語", 110, YELLOW), ("いっしょに言ってみよう！", 64, WHITE)]))
        olapon_corner(frame, shot, t)
    elif k == "phrase":
        ph = shot["ph"]
        lines = [(f"きょうのスペイン語  {shot['i']} / {shot['n']}", 46, YELLOW), (ph["es"], 150, WHITE),
                 (ph["ja"], 72, YELLOW)]
        if ph.get("note"):
            lines.append((ph["note"], 44, WHITE))
        lines.append((shot["label"], 56, (143, 211, 255)))
        frame.alpha_composite(card(lines))
        if shot.get("countdown"):
            k2 = (t - shot["start"]) / (shot["end"] - shot["start"])
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([460, 960, 1460, 990], radius=15, outline=WHITE, width=4)
            d.rounded_rectangle([460, 960, 460 + max(30, 1000 * (1 - k2)), 990], radius=15, fill=YELLOW)
        olapon_corner(frame, shot, t, face="kimegao" if not shot.get("countdown") else "normal")
    elif k == "review":
        lines = [("まとめ：もう一度！", 64, YELLOW)]
        for ph in shot["phrases"]:
            lines.append((f"{ph['es']}（{ph['ja']}）", 76, WHITE if ph is not shot["current"] else YELLOW))
        frame.alpha_composite(card(lines))
        olapon_corner(frame, shot, t, face="doya")
    elif k == "next":
        nxt = shot["next"]
        frame.alpha_composite(card([("つづく", 150, YELLOW), (f"次回「{nxt['title']}」", 70, WHITE), (nxt["line"], 52, WHITE)]))
        olapon_corner(frame, shot, t)
    return frame


def render(ep_path):
    ep = json.loads(Path(ep_path).read_text(encoding="utf-8"))
    out = OUT_DIR / ep["id"]
    out.mkdir(parents=True, exist_ok=True)
    plan = build_plan(ep, out)
    # ひょこっと出てくる印（直前のセリフで見えていなかった人が話すとき）
    prev = set()
    for s in plan.shots:
        if s["kind"] == "story":
            s["popped"] = s["who"] in s["visible"] and s["who"] not in prev
            prev = s["visible"]
    total = plan.shots[-1]["end"]
    # 音をまとめる
    mix = np.zeros(int(RATE * (total + 1)), np.float32)
    for t0, wav in plan.audio:
        with wave.open(str(wav), "rb") as w:
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        i = int(t0 * RATE)
        mix[i:i + len(x)] += x[:len(mix) - i]
    audio = _write(out / "audio.wav", mix / max(1.0, np.abs(mix).max() / 0.95))
    # 絵を1コマずつ ffmpeg に流す
    mp4 = out / f"{ep['id']}.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio), "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                             "-shortest", "-movflags", "+faststart", str(mp4)], stdin=subprocess.PIPE)
    si = 0
    for n in range(int(total * FPS)):
        t = n / FPS
        while si < len(plan.shots) - 1 and t >= plan.shots[si]["end"]:
            si += 1
        proc.stdin.write(draw_frame(plan.shots[si], t).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    for f in out.glob("ev_*.wav"):
        f.unlink()
    print(f"できました: {mp4}（{total:.1f}秒）")
    return mp4


if __name__ == "__main__":
    for p in sys.argv[1:]:
        render(p)
