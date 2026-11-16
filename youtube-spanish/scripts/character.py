"""キャラクター「オラポン君」を画面に出す・口パクさせる。

素材は characters/olapon/（SVG、背景透過、全部同じ大きさ。重ねると位置がそろう）。
- expressions/ … 表情（01_normal 通常 / 02_doya ドヤ / 03_namida 涙目 / 04_kimegao 決め顔 / 05_odoroki 驚き / 06_shonbori しょんぼり）
- lipsync/ … 口のない顔（base_nomouth）＋ 口の形（mouth_a/i/u/e/o/n）

口パクは、ナレーションの音の大きさから口の形を決める（大きい→「あ」、中くらい→「お・え」、小さい→「い・う」、無音→閉じる）。
"""
import wave
from functools import lru_cache
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = ROOT / "characters" / "olapon"
SRC_W, SRC_H = 960, 944  # 素材の書き出しサイズ
FPS = 15                 # 口パクのコマ数（1秒あたり）。素材の目安「30fpsで2〜4フレーム」に合わせる
EXPRESSIONS = {"normal": "01_normal", "doya": "02_doya", "namida": "03_namida",
               "kimegao": "04_kimegao", "odoroki": "05_odoroki", "shonbori": "06_shonbori"}
MOUTHS = ("a", "i", "u", "e", "o", "n")


def _render(svg_path, width):
    import io

    import cairosvg  # 使うときだけ読み込む
    png = cairosvg.svg2png(url=str(svg_path), output_width=width)
    return Image.open(io.BytesIO(png)).convert("RGBA")


@lru_cache(maxsize=64)
def expression(name, width):
    """表情の画像（RGBA）。name は EXPRESSIONS のキー。"""
    return _render(CHAR_DIR / "expressions" / f"{EXPRESSIONS[name]}.svg", width)


@lru_cache(maxsize=64)
def talking(mouth, width):
    """口パク用の画像：口のない顔に、指定の口を重ねたもの。"""
    if mouth not in MOUTHS:
        raise ValueError(f"口の形は {MOUTHS} のどれかです: {mouth}")
    face = _render(CHAR_DIR / "lipsync" / "base_nomouth.svg", width)
    face.alpha_composite(_render(CHAR_DIR / "lipsync" / f"mouth_{mouth}.svg", width))
    return face


def height_for(width):
    return round(width * SRC_H / SRC_W)


def mouth_track(wav_path, fps=FPS):
    """音声から、1コマごとの口の形を決める。最後は必ず閉じた口（n）にする。"""
    with wave.open(str(wav_path), "rb") as w:
        rate, n = w.getframerate(), w.getnframes()
        data = w.readframes(n)
    import array
    samples = array.array("h", data)
    step = max(1, rate // fps)
    levels = []
    for i in range(0, len(samples), step):
        chunk = samples[i:i + step]
        levels.append((sum(x * x for x in chunk) / max(1, len(chunk))) ** 0.5)
    peak = max(levels) if levels else 1
    track, flip = [], False
    for lv in levels:
        r = lv / peak if peak else 0
        if r < 0.12:
            m = "n"
        elif r > 0.6:
            m = "a"
        elif r > 0.38:
            m = "o" if flip else "e"
        else:
            m = "i" if flip else "u"
        if m != (track[-1] if track else None):
            flip = not flip
        track.append(m)
    if track:
        track[-1] = "n"
    return track, step / rate


def runs(track):
    """同じ口が続くコマをまとめる：[(口, コマ数), ...]"""
    out = []
    for m in track:
        if out and out[-1][0] == m:
            out[-1][1] += 1
        else:
            out.append([m, 1])
    return [(m, c) for m, c in out]
