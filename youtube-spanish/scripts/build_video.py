#!/usr/bin/env python3
"""スペイン語 中級リスニング（会話・和訳付き）の動画を作る。

使い方:
    python3 scripts/build_video.py content/ep01_piso.json
    python3 scripts/build_video.py content/*.json

できるもの（output/<id>/ に保存）:
    <id>.mp4             1920x1080 の動画（約9〜10分）
    thumbnail.png        サムネイル（1280x720）
    description.txt      YouTube の概要欄（チャプター・台本・和訳・クレジット）
    review.md            ネイティブチェック用の台本

音声は Piper（無料・オフラインの音声合成）で作ります。初回だけ音声モデル（約77MB）を自動でダウンロードします。
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from thumbnail import make_thumbnail

ROOT = Path(__file__).resolve().parent.parent
VOICE_DIR = ROOT / "voices"
OUT_DIR = ROOT / "output"

VOICE_NAME = "es_ES-sharvard-medium"
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/"
VOICE_CREDIT = (
    "音声: Piper TTS（音声モデル es_ES-sharvard-medium）\n"
    "学習データ: The Sharvard Corpus（University of Edinburgh） CC BY 3.0 "
    "https://datashare.ed.ac.uk/handle/10283/574"
)
SPEAKER_IDS = {"M": 0, "F": 1}

W, H = 1920, 1080
FPS = 30
SLOW_SCALE = 1.4  # ゆっくり読みの速さ（大きいほど遅い）

# 間（秒）
GAP_LINE = 0.6        # 通しで聞くときの、セリフとセリフの間
GAP_REPEAT = 0.8      # 1文ずつ：ふつう → ゆっくり の間
GAP_AFTER_LINE = 1.6  # 1文ずつ：次のセリフまでの間（口に出して繰り返す時間）
GAP_PHRASE = 1.2
SHADOW_EXTRA = 0.8    # シャドーイング：セリフと同じ長さ＋この秒数だけ無音にする
CARD_SECONDS = 3.0    # 区切りの画面を出す長さ
TITLE_SECONDS = 6.0
END_SECONDS = 6.0

FONT_ES = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_ES_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_JA = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

COLORS = {
    "bg": (24, 32, 44),
    "panel": (34, 45, 61),
    "text": (245, 245, 240),
    "sub": (178, 190, 205),
    "accent": (255, 196, 87),
    "F": (240, 128, 112),
    "M": (88, 190, 180),
}

SECTIONS = [
    ("listen1", "1回目　まずは通しで聞く", "字幕はスペイン語だけ。内容を想像しながら聞いてみましょう"),
    ("line", "2回目　1文ずつ聞く（ふつう → ゆっくり）", "和訳を見ながら、声に出してまねしてみましょう"),
    ("phrases", "キーフレーズ", "会話に出てきた、覚えておきたい表現"),
    ("listen2", "3回目　和訳付きで通しで聞く", "意味を確かめながら、もう一度"),
    ("shadow", "4回目　シャドーイング", "セリフのあとの無音の間に、同じように言ってみましょう"),
    ("listen3", "5回目　字幕なしで聞く", "どこまで聞き取れるか、試してみましょう"),
]


# ---------- 台本 ----------

def load_episode(path):
    ep = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_episode(ep)
    return ep


def validate_episode(ep):
    for key in ("id", "title_es", "title_ja", "level", "grammar", "speakers", "lines", "phrases"):
        if key not in ep:
            raise ValueError(f"台本に「{key}」がありません")
    for name, info in ep["speakers"].items():
        if info.get("voice") not in SPEAKER_IDS:
            raise ValueError(f"{name} の voice は F か M にしてください")
    for i, line in enumerate(ep["lines"], 1):
        if line.get("speaker") not in ep["speakers"]:
            raise ValueError(f"{i}行目の話し手「{line.get('speaker')}」が speakers にいません")
        if not line.get("es") or not line.get("ja"):
            raise ValueError(f"{i}行目に es（スペイン語）か ja（和訳）がありません")
        vocab = line.get("vocab", [])
        if len(vocab) > 3:
            raise ValueError(f"{i}行目の単語（vocab）は3つまでにしてください")
        for v in vocab:
            if not v.get("es") or not v.get("ja"):
                raise ValueError(f"{i}行目の単語に es か ja がありません")
    for i, p in enumerate(ep["phrases"], 1):
        if not p.get("es") or not p.get("ja"):
            raise ValueError(f"キーフレーズ{i}に es か ja がありません")


# ---------- 音声 ----------

def ensure_voice():
    VOICE_DIR.mkdir(exist_ok=True)
    for suffix in (".onnx", ".onnx.json"):
        dest = VOICE_DIR / (VOICE_NAME + suffix)
        if not dest.exists():
            print(f"音声モデルをダウンロードしています: {dest.name}")
            urllib.request.urlretrieve(VOICE_URL + VOICE_NAME + suffix, dest)
    return VOICE_DIR / (VOICE_NAME + ".onnx")


class Speaker:
    """Piper で音声を作り、同じ文はキャッシュから使い回す。"""

    def __init__(self, cache_dir):
        from piper import PiperVoice, SynthesisConfig  # 使うときだけ読み込む（テストでは不要）
        self._config_cls = SynthesisConfig
        self.voice = PiperVoice.load(str(ensure_voice()))
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def say(self, text, voice, slow=False):
        scale = SLOW_SCALE if slow else 1.0
        key = hashlib.sha1(f"{VOICE_NAME}|{voice}|{scale}|{text}".encode()).hexdigest()[:16]
        path = self.cache_dir / f"{key}.wav"
        if not path.exists():
            cfg = self._config_cls(speaker_id=SPEAKER_IDS[voice], length_scale=scale)
            with wave.open(str(path), "wb") as w:
                self.voice.synthesize_wav(text, w, syn_config=cfg)
        return path


# ---------- 画面 ----------

def font(path, size):
    return ImageFont.truetype(path, size)


NO_LINE_START = set("、。，．！？）」』】ーっゃゅょァィゥェォッャュョ")


def wrap(text, fnt, max_width, by_char=False):
    """表示幅に収まるように改行する。日本語は1文字ずつ、スペイン語は単語ごとに区切る。"""
    units = list(text) if by_char else text.split(" ")
    sep = "" if by_char else " "
    lines, cur = [], ""
    for u in units:
        trial = u if not cur else cur + sep + u
        # 句読点や閉じかっこは行の先頭に置かない（前の行の末尾にぶら下げる）
        if fnt.getlength(trial) <= max_width or not cur or (by_char and u in NO_LINE_START):
            cur = trial
        else:
            lines.append(cur)
            cur = u
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, fnt, x, y, fill, spacing):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def base_canvas(ep, section_label=None):
    img = Image.new("RGB", (W, H), COLORS["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 96], fill=COLORS["panel"])
    d.text((60, 26), "スペイン語 中級リスニング｜会話・和訳付き", font=font(FONT_JA, 40), fill=COLORS["accent"])
    right = f"#{ep['id'][2:]}  {ep['title_ja']}"
    f = font(FONT_JA, 34)
    d.text((W - 60 - f.getlength(right), 32), right, font=f, fill=COLORS["sub"])
    if section_label:
        d.text((60, 130), section_label, font=font(FONT_JA, 40), fill=COLORS["sub"])
    return img, d


def slide_title(ep, path):
    img, d = base_canvas(ep)
    d.text((120, 230), ep["title_es"], font=font(FONT_ES_BOLD, 110), fill=COLORS["text"])
    d.text((120, 380), ep["title_ja"], font=font(FONT_JA, 64), fill=COLORS["accent"])
    y = 520
    for label, value in (("レベル", ep["level"]), ("ポイント", ep["grammar"])):
        d.text((120, y), label, font=font(FONT_JA, 40), fill=COLORS["sub"])
        y = draw_lines(d, wrap(value, font(FONT_JA, 44), 1450, by_char=True), font(FONT_JA, 44), 360, y, COLORS["text"], 14) + 24
    y += 20
    d.text((120, y), "この動画の流れ", font=font(FONT_JA, 36), fill=COLORS["sub"])
    y += 56
    for _, title, _ in SECTIONS:
        d.text((150, y), "・" + title, font=font(FONT_JA, 34), fill=COLORS["text"])
        y += 48
    img.save(path)


def slide_card(ep, title, sub, path):
    img, d = base_canvas(ep)
    f1, f2 = font(FONT_JA, 76), font(FONT_JA, 44)
    d.text(((W - f1.getlength(title)) / 2, 420), title, font=f1, fill=COLORS["accent"])
    d.text(((W - f2.getlength(sub)) / 2, 540), sub, font=f2, fill=COLORS["sub"])
    img.save(path)


def slide_line(ep, section_label, line, idx, total, path, show_es=True, show_ja=True, tag=None):
    img, d = base_canvas(ep, section_label)
    voice = ep["speakers"][line["speaker"]]["voice"]
    color = COLORS[voice]
    fn = font(FONT_ES_BOLD, 46)
    name_w = fn.getlength(line["speaker"])
    d.rounded_rectangle([120, 250, 120 + name_w + 60, 330], radius=40, fill=color)
    d.text((150, 262), line["speaker"], font=fn, fill=COLORS["bg"])
    if tag:
        ft = font(FONT_JA, 38)
        d.text((120 + name_w + 100, 268), tag, font=ft, fill=COLORS["accent"])
    vocab = line.get("vocab", []) if show_ja else []
    if show_es:
        bottom = vocab_top(vocab) - 30 if vocab else H - 110
        es_size, ja_size = fit_text_sizes(line, bottom)
        fe = font(FONT_ES, es_size)
        y = draw_lines(d, wrap(line["es"], fe, W - 240), fe, 120, TEXT_TOP, COLORS["text"], 22) + 40
    else:
        d.text((120, TEXT_TOP), "（字幕なし）", font=font(FONT_JA, 56), fill=COLORS["sub"])
        y, ja_size = TEXT_TOP + 120, 50
    if show_ja:
        fj = font(FONT_JA, ja_size)
        draw_lines(d, wrap(line["ja"], fj, W - 240, by_char=True), fj, 120, y, COLORS["sub"], 18)
    if vocab:
        draw_vocab(d, vocab)
    prog = f"{idx} / {total}"
    fp = font(FONT_ES, 36)
    d.text((W - 60 - fp.getlength(prog), H - 80), prog, font=fp, fill=COLORS["sub"])
    img.save(path)


TEXT_TOP = 390      # セリフを書き始める高さ
VOCAB_BOTTOM = 985  # 単語の欄の下端（右下のページ番号に重ならない高さ）
VOCAB_ROW = 46


def text_bottom(line, es_size, ja_size):
    """セリフ（スペイン語＋和訳）を書いたときの下端の高さ。"""
    fe, fj = font(FONT_ES, es_size), font(FONT_JA, ja_size)
    n_es = len(wrap(line["es"], fe, W - 240))
    n_ja = len(wrap(line["ja"], fj, W - 240, by_char=True))
    return TEXT_TOP + n_es * (es_size + 22) + 40 + n_ja * (ja_size + 18)


def fit_text_sizes(line, bottom):
    """長いセリフでも単語の欄に重ならないように、文字を少しずつ小さくする。"""
    for es_size, ja_size in ((70, 50), (64, 46), (58, 42), (52, 38)):
        if text_bottom(line, es_size, ja_size) <= bottom:
            return es_size, ja_size
    return 52, 38


def vocab_layout(vocab, max_width=W - 240):
    """単語を横に並べ、入りきらなければ次の行に回す。各単語の (x, 行番号) を返す。"""
    fe, fj = font(FONT_ES_BOLD, 36), font(FONT_JA, 34)
    pos, x, row = [], 0, 0
    for v in vocab:
        w = fe.getlength(v["es"]) + 18 + fj.getlength(v["ja"])
        if x > 0 and x + w > max_width:
            x, row = 0, row + 1
        pos.append((x, row, w))
        x += w + 60
    return pos


def vocab_top(vocab):
    """単語の欄の上端。単語が2行になるときは、その分だけ上に広げる。"""
    rows = max(row for _, row, _ in vocab_layout(vocab)) + 1
    return VOCAB_BOTTOM - (58 + rows * VOCAB_ROW + 14)


def draw_vocab(d, vocab):
    top = vocab_top(vocab)
    d.rounded_rectangle([90, top, W - 90, VOCAB_BOTTOM], radius=24, fill=COLORS["panel"])
    d.text((120, top + 14), "単語", font=font(FONT_JA, 30), fill=COLORS["accent"])
    fe, fj = font(FONT_ES_BOLD, 36), font(FONT_JA, 34)
    for v, (x, row, _) in zip(vocab, vocab_layout(vocab)):
        y = top + 58 + row * VOCAB_ROW
        d.text((120 + x, y), v["es"], font=fe, fill=COLORS["text"])
        d.text((120 + x + fe.getlength(v["es"]) + 18, y + 2), v["ja"], font=fj, fill=COLORS["sub"])


def slide_phrase(ep, phrase, idx, total, path, tag=None):
    img, d = base_canvas(ep, "キーフレーズ")
    if tag:
        d.text((120, 250), tag, font=font(FONT_JA, 38), fill=COLORS["accent"])
    fe, fj, fn = font(FONT_ES_BOLD, 74), font(FONT_JA, 54), font(FONT_JA, 42)
    y = draw_lines(d, wrap(phrase["es"], fe, W - 240), fe, 120, 330, COLORS["text"], 22) + 40
    y = draw_lines(d, wrap(phrase["ja"], fj, W - 240, by_char=True), fj, 120, y, COLORS["accent"], 18) + 50
    if phrase.get("note"):
        draw_lines(d, wrap(phrase["note"], fn, W - 240, by_char=True), fn, 120, y, COLORS["sub"], 16)
    prog = f"{idx} / {total}"
    fp = font(FONT_ES, 36)
    d.text((W - 60 - fp.getlength(prog), H - 80), prog, font=fp, fill=COLORS["sub"])
    img.save(path)


def slide_end(ep, path):
    img, d = base_canvas(ep)
    f1, f2 = font(FONT_JA, 72), font(FONT_JA, 44)
    for y, text, f, c in (
        (380, "おつかれさまでした！", f1, COLORS["accent"]),
        (500, "聞き取れなかったセリフは、2回目の「1文ずつ」に戻って確認しましょう", f2, COLORS["text"]),
        (580, "台本と和訳は概要欄にあります", f2, COLORS["sub"]),
    ):
        d.text(((W - f.getlength(text)) / 2, y), text, font=f, fill=c)
    img.save(path)


# ---------- タイムライン ----------

class Timeline:
    """画面（静止画）と音声を順に積み上げ、動画の時間割を作る。"""

    def __init__(self, rate):
        self.rate = rate
        self.frames = 0          # 音声のフレーム数（= 時間）
        self.clips = []          # (画像パス, 開始秒, 終了秒)
        self.chapters = []       # (開始秒, 名前)
        self.audio_parts = []    # wav パス or 無音フレーム数(int)

    @property
    def now(self):
        return self.frames / self.rate

    def chapter(self, name):
        self.chapters.append((self.now, name))

    def add(self, image, parts):
        start = self.now
        for p in parts:
            if isinstance(p, (int, float)):
                n = int(round(p * self.rate))
                self.audio_parts.append(n)
                self.frames += n
            else:
                with wave.open(str(p), "rb") as w:
                    if w.getframerate() != self.rate:
                        raise ValueError("音声のサンプリングレートがそろっていません")
                    self.frames += w.getnframes()
                self.audio_parts.append(Path(p))
        self.clips.append((Path(image), start, self.now))

    def video_durations(self, fps=FPS):
        """各画面の表示時間。境目をフレーム単位に丸め、ずれが積み重ならないようにする。"""
        out = []
        for image, start, end in self.clips:
            a, b = round(start * fps), round(end * fps)
            out.append((image, max(b - a, 1) / fps))
        return out

    def write_audio(self, path):
        with wave.open(str(path), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(self.rate)
            for p in self.audio_parts:
                if isinstance(p, int):
                    out.writeframes(b"\x00\x00" * p)
                else:
                    with wave.open(str(p), "rb") as w:
                        out.writeframes(w.readframes(w.getnframes()))


def wav_seconds(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def fmt_time(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def build(ep_path, keep_work=False):
    ep = load_episode(ep_path)
    out = OUT_DIR / ep["id"]
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"{ep['id']}_", dir=out)) if keep_work else Path(tempfile.mkdtemp(prefix=f"{ep['id']}_"))
    speaker = Speaker(OUT_DIR / ".tts_cache")
    voice_of = {name: info["voice"] for name, info in ep["speakers"].items()}

    # サンプリングレートを1回作って確かめる
    probe = speaker.say("Hola.", "F")
    with wave.open(str(probe), "rb") as w:
        rate = w.getframerate()
    tl = Timeline(rate)
    n_img = [0]

    def img_path():
        n_img[0] += 1
        return work / f"s{n_img[0]:04d}.png"

    lines, total = ep["lines"], len(ep["lines"])

    p = img_path(); slide_title(ep, p); tl.chapter("はじめに"); tl.add(p, [TITLE_SECONDS])

    for key, title, sub in SECTIONS:
        tl.chapter(title)
        p = img_path(); slide_card(ep, title, sub, p); tl.add(p, [CARD_SECONDS])
        if key in ("listen1", "listen2", "listen3"):
            for i, ln in enumerate(lines, 1):
                p = img_path()
                slide_line(ep, title, ln, i, total, p,
                           show_es=key != "listen3", show_ja=key == "listen2")
                tl.add(p, [speaker.say(ln["es"], voice_of[ln["speaker"]]), GAP_LINE])
        elif key == "line":
            for i, ln in enumerate(lines, 1):
                v = voice_of[ln["speaker"]]
                p = img_path(); slide_line(ep, title, ln, i, total, p, tag="ふつう")
                tl.add(p, [speaker.say(ln["es"], v), GAP_REPEAT])
                p = img_path(); slide_line(ep, title, ln, i, total, p, tag="ゆっくり")
                tl.add(p, [speaker.say(ln["es"], v, slow=True), GAP_AFTER_LINE])
        elif key == "shadow":
            for i, ln in enumerate(lines, 1):
                wav = speaker.say(ln["es"], voice_of[ln["speaker"]])
                p = img_path(); slide_line(ep, title, ln, i, total, p, show_ja=False, tag="あとについて言う")
                tl.add(p, [wav, wav_seconds(wav) + SHADOW_EXTRA])
        elif key == "phrases":
            ph = ep["phrases"]
            for i, item in enumerate(ph, 1):
                p = img_path(); slide_phrase(ep, item, i, len(ph), p)
                tl.add(p, [speaker.say(item["es"], "F"), GAP_REPEAT,
                           speaker.say(item["es"], "F", slow=True), GAP_PHRASE])

    p = img_path(); slide_end(ep, p); tl.chapter("まとめ"); tl.add(p, [END_SECONDS])

    # 動画を書き出す
    audio = work / "audio.wav"
    tl.write_audio(audio)
    concat = work / "slides.txt"
    durs = tl.video_durations()
    with open(concat, "w", encoding="utf-8") as f:
        for image, dur in durs:
            f.write(f"file '{image}'\nduration {dur:.6f}\n")
        f.write(f"file '{durs[-1][0]}'\n")  # 最後の画面を確実に表示するための決まりごと
    mp4 = out / f"{ep['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
           "-i", str(audio), "-fps_mode", "cfr", "-r", str(FPS), "-c:v", "libx264", "-tune", "stillimage",
           "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-shortest", "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)

    make_thumbnail(ep, out / "thumbnail.png")
    (out / "description.txt").write_text(description(ep, tl), encoding="utf-8")
    (out / "review.md").write_text(review_sheet(ep), encoding="utf-8")
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"できました: {mp4}（{fmt_time(tl.now)}）")
    return mp4, tl.now


def description(ep, tl):
    out = [
        f"【スペイン語 中級リスニング】{ep['title_es']}｜{ep['title_ja']}（会話・和訳付き）",
        "",
        f"レベル: {ep['level']}",
        f"ポイント: {ep['grammar']}",
        "",
        "■ チャプター",
    ]
    out += [f"{fmt_time(t)} {name}" for t, name in tl.chapters]
    out += ["", "■ 台本と和訳"]
    for ln in ep["lines"]:
        out += [f"{ln['speaker']}: {ln['es']}", f"　{ln['ja']}"]
    out += ["", "■ キーフレーズ"]
    for p in ep["phrases"]:
        out.append(f"・{p['es']} … {p['ja']}" + (f"（{p['note']}）" if p.get("note") else ""))
    words = [v for ln in ep["lines"] for v in ln.get("vocab", [])]
    if words:
        out += ["", "■ 単語"]
        out += [f"・{v['es']} … {v['ja']}" for v in words]
    out += ["", "■ クレジット", VOICE_CREDIT, "会話文はこのチャンネルのオリジナルです（AIを使って作成し、内容を確認しています）。"]
    return "\n".join(out) + "\n"


def review_sheet(ep):
    out = [f"# ネイティブチェック用: {ep['id']} {ep['title_es']}", "",
           "スペイン語として不自然な所・間違いがあれば、右の欄に修正案を書いてください。", "",
           "| # | 話し手 | スペイン語 | 和訳 | 単語 | 修正案 |", "|---|---|---|---|---|---|"]
    for i, ln in enumerate(ep["lines"], 1):
        words = " / ".join(f"{v['es']}：{v['ja']}" for v in ln.get("vocab", []))
        out.append(f"| {i} | {ln['speaker']} | {ln['es']} | {ln['ja']} | {words} | |")
    out += ["", "## キーフレーズ", "", "| # | スペイン語 | 和訳 | 説明 | 修正案 |", "|---|---|---|---|---|"]
    for i, p in enumerate(ep["phrases"], 1):
        out.append(f"| {i} | {p['es']} | {p['ja']} | {p.get('note', '')} | |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="スペイン語 中級リスニング動画を作る")
    ap.add_argument("episodes", nargs="+", help="台本の JSON ファイル（content/ 以下）")
    ap.add_argument("--keep-work", action="store_true", help="途中の画像と音声を output/<id>/ に残す")
    args = ap.parse_args(argv)
    for path in args.episodes:
        build(path, keep_work=args.keep_work)


if __name__ == "__main__":
    sys.exit(main())
