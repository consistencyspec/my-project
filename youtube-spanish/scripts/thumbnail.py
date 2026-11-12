"""サムネイルを作る。

AI などで作った「文字の入っていない背景画像」に、左側の赤い帯と3つの文字（上のラベル・大きなタイトル・下の帯）を重ねる。
文字は台本（JSON）から読むので、毎回同じ配置・同じ見た目にそろう。

台本の書き方（すべて省略可）:
    "thumbnail": {
        "title": "不動産屋へ\\n行く",            ← 大きく出す文字。\\n で改行の位置を決められる（省略時は title_ja）
        "background": "thumbnails/ep01.jpg",  ← 背景画像（youtube-spanish/ からの場所）。省略時は無地
        "band": "会話・和訳・単語付き",          ← 下の帯の文字
        "panel_top": 0.56, "panel_bottom": 0.47  ← 赤い帯の右端（上・下）の位置。背景の文字などを隠したいときに広げる
    }

単体で使うとき（音声や動画は作らない）:
    python3 scripts/thumbnail.py content/ep01_piso.json
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TW, TH = 1280, 720

RED = (214, 32, 39)
YELLOW = (255, 214, 0)
WHITE = (255, 255, 255)
INK = (20, 20, 20)
NAVY = (24, 32, 44)

# 太い日本語フォントの候補（上から順に、見つかったものを使う）。(ファイル, コレクション内の番号)
HEAVY_FONTS = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", 0),       # Linux: fonts-noto-cjk-extra
    ("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", 0),               # Mac
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("C:/Windows/Fonts/YuGothB.ttc", 0),                                 # Windows
    ("C:/Windows/Fonts/meiryob.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
    ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", 0),            # 最後の手段（細め）
]

DEFAULT_BAND = "会話・和訳・単語付き"
PANEL_TOP_X = 0.56     # 赤い帯の右端（上）。画面の幅に対する割合
PANEL_BOTTOM_X = 0.47  # 赤い帯の右端（下）。斜めにする


def heavy_font(size):
    for path, index in HEAVY_FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size, index=index)
    raise FileNotFoundError("太い日本語フォントが見つかりません（README の「サムネイル」を見てください）")


def top_label(ep):
    m = re.search(r"[ABC][12]", ep.get("level", ""))
    return "スペイン語 中級リスニング" + (f" {m.group(0)}" if m else "")


def cover(img, w, h):
    """縦横比を保ったまま、画面いっぱいに広げて中央を切り抜く。"""
    return ImageOps.fit(img.convert("RGB"), (w, h), method=Image.LANCZOS, centering=(0.5, 0.4))


def fit_title(text, max_w, max_h, max_lines=3):
    """タイトルを、帯の中に収まる一番大きい文字サイズで並べる。\\n があればそこで改行する。

    まずは指定どおりの改行のまま（勝手に折り返さずに）収まる大きさを探す。
    それでは小さくなりすぎるときだけ、途中で折り返す。
    """
    parts = text.split("\n")
    for size in range(150, 76, -4):
        f = heavy_font(size)
        if len(parts) <= max_lines and len(parts) * size * 1.12 <= max_h \
                and all(f.getlength(p) <= max_w for p in parts):
            return f, parts
    for size in range(150, 40, -4):
        f = heavy_font(size)
        rows = []
        for part in text.split("\n"):
            rows += _wrap_chars(part, f, max_w)
        height = len(rows) * size * 1.12
        if len(rows) <= max_lines and height <= max_h and all(f.getlength(r) <= max_w for r in rows):
            return f, rows
    return heavy_font(44), _wrap_chars(text.replace("\n", ""), heavy_font(44), max_w)


NO_LINE_START = set("、。，．！？）」』】ーっゃゅょァィゥェォッャュョ")


def _wrap_chars(text, f, max_w):
    rows, cur = [], ""
    for ch in text:
        if cur and f.getlength(cur + ch) > max_w and ch not in NO_LINE_START:
            rows.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        rows.append(cur)
    return rows


def outlined(d, xy, text, f, fill, stroke, width):
    d.text(xy, text, font=f, fill=fill, stroke_width=width, stroke_fill=stroke)


def make_thumbnail(ep, path, root=ROOT):
    conf = ep.get("thumbnail", {})
    bg_path = conf.get("background")
    if bg_path:
        bg_file = (Path(root) / bg_path)
        if not bg_file.exists():
            raise FileNotFoundError(f"背景画像が見つかりません: {bg_file}")
        img = cover(Image.open(bg_file), TW, TH)
    else:
        img = Image.new("RGB", (TW, TH), NAVY)
    d = ImageDraw.Draw(img)

    # 左の赤い帯（斜め）と、左端の黄色い線
    top_x = int(TW * conf.get("panel_top", PANEL_TOP_X))
    bottom_x = int(TW * conf.get("panel_bottom", PANEL_BOTTOM_X))
    d.polygon([(0, 0), (top_x, 0), (bottom_x, TH), (0, TH)], fill=RED)
    d.rectangle([0, 0, 14, TH], fill=YELLOW)

    if not bg_path:
        # 背景画像がないときは、右側の空いた所にスペイン語のタイトルを入れる
        dejavu = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        fe = ImageFont.truetype(dejavu, 64) if Path(dejavu).exists() else heavy_font(64)
        left, right = top_x + 40, TW - 50
        words, rows, cur = ep.get("title_es", "").split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if cur and fe.getlength(trial) > right - left:
                rows.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            rows.append(cur)
        y = (TH - len(rows) * 80) // 2
        for row in rows:
            d.text((right - fe.getlength(row), y), row, font=fe, fill=(150, 165, 185))
            y += 80

    pad = 44
    usable = bottom_x - pad - 30  # 斜めの帯でも、下の方まで文字がはみ出さない幅

    # 上のラベル（黄色い下地に黒い文字）
    fl = heavy_font(40)
    label = top_label(ep)
    while fl.getlength(label) > usable and fl.size > 24:
        fl = heavy_font(fl.size - 2)
    lw = fl.getlength(label)
    d.rounded_rectangle([pad - 12, 36, pad + lw + 12, 36 + fl.size + 22], radius=10, fill=YELLOW)
    d.text((pad, 42), label, font=fl, fill=INK)

    # 下の帯（黒い下地に白い文字）
    band = conf.get("band", DEFAULT_BAND)
    fb = heavy_font(46)
    while fb.getlength(band) > usable and fb.size > 24:
        fb = heavy_font(fb.size - 2)
    bw = fb.getlength(band)
    band_top = TH - 46 - fb.size - 30
    d.rounded_rectangle([pad - 14, band_top, pad + bw + 14, TH - 46], radius=12, fill=INK)
    d.text((pad, band_top + 10), band, font=fb, fill=WHITE)

    # 大きなタイトル（白い文字に黒いふち）
    title = conf.get("title", ep.get("title_ja", ""))
    title_top = 36 + fl.size + 60
    f, rows = fit_title(title, usable, band_top - 40 - title_top)
    line_h = int(f.size * 1.12)
    y = title_top + max(0, (band_top - 40 - title_top - line_h * len(rows)) // 2)
    for row in rows:
        outlined(d, (pad, y), row, f, WHITE, INK, max(4, f.size // 18))
        y += line_h

    img.save(path)
    return path


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    for p in argv:
        ep = json.loads(Path(p).read_text(encoding="utf-8"))
        out = ROOT / "output" / ep["id"]
        out.mkdir(parents=True, exist_ok=True)
        print("できました:", make_thumbnail(ep, out / "thumbnail.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
