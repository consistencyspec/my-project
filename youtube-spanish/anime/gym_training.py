"""アニメ「ジムでミット打ち」：オラポン君がマノロ会長とトレーニングする（約18秒、音なし・吹き出しつき）。

使い方:
  python3 anime/gym_training.py  → output/anime/gym_training.mp4
声と効果音は、ほかの話と同じく最後に入れる。いまは吹き出し（スペイン語＋日本語）で見せる。

流れ:
  会長「¡Vamos, Olapón!」→「¡Uno!」ジャブ →「¡Uno, dos!」ジャブ・ストレート →「¡Uno, uno, dos!」
  →「¡Más fuerte!」がんばる顔で特大ストレート（バシーン！会長がのけぞる）→「¡Muy bien!」
  → オラポン君、サッカーのゴールのように「¡Gooool!」と大はしゃぎしてガードががら空き
  → 会長のミットで頭をポコッ「¡Guardia!」→「ポ〜ン…」→ きょうのスペイン語
"""
import io
import math
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "characters"))
import make_boxing as mb  # noqa: E402

W, H, FPS = 1920, 1080, 24
DUR = 18.0
SC = 1.9                      # キャラクターの縮尺（1単位 = 1.9px）
GY = 1036                     # 地面の高さ（px）
X_O = 720                     # オラポン君の位置（x=150単位の画面位置）
X_M = X_O + 307 * SC          # 会長の位置（グローブの先とミットの面がちょうど当たる距離）
FONT_ES = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_JA = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
INK = (42, 26, 18)

LEADS = [2.9, 3.95, 5.15, 5.5]          # ジャブ（奥の手）の時刻
REARS = [4.3, 5.85]                     # ストレート（手前の手）
BIG = 8.3                               # 特大ストレート
BOP = 10.85                             # 会長のポコッ

BUBBLES = [  # (始まり, 終わり, だれ, スペイン語, 日本語)
    (0.4, 2.4, "M", "¡Vamos, Olapón!", "さあ、いくぞ、オラポン！"),
    (2.5, 3.4, "M", "¡Uno!", "ワン！（1）"),
    (3.55, 4.7, "M", "¡Uno, dos!", "ワン、ツー！"),
    (4.8, 6.3, "M", "¡Uno, uno, dos!", "ワン、ワン、ツー！"),
    (6.6, 8.0, "M", "¡Más fuerte!", "もっと強く！"),
    (8.9, 10.4, "M", "¡Muy bien!", "いいぞ！"),
    (9.3, 10.6, "O", "¡Gooool!", "やったー！（ゴールの叫び）"),
    (10.95, 12.6, "M", "¡Guardia!", "ガードを上げろ！"),
    (12.0, 13.3, "O", "ポ〜ン…", ""),
]
PHRASES = [("¡Uno, dos!", "ワン、ツー（1、2）"), ("¡Más fuerte!", "もっと強く"),
           ("¡Muy bien!", "いいぞ・よくできた"), ("¡Guardia!", "ガード（を上げろ）")]
END_START = 13.6


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def punch(t, t0, dur=0.42):
    u = (t - t0) / dur
    if u < 0 or u > 1:
        return 0.0
    if u < 0.3:
        return ease(u / 0.3)
    if u < 0.45:
        return 1.0
    return 1 - ease((u - 0.45) / 0.55)


def ramp(t, t0, t1):
    return ease((t - t0) / (t1 - t0))


def state(t):
    lead = max([punch(t, x) for x in LEADS] + [0])
    rear = max([punch(t, x) for x in REARS] + [punch(t, BIG, 0.6)])
    big = punch(t, BIG, 0.6)
    # はしゃいで前に出る → ポコッとされて戻る
    o_dx = 90 * ramp(t, 9.0, 10.2) * (1 - ramp(t, 12.6, 13.4))
    m_dx = -50 * ramp(t, 10.4, 10.75) * (1 - ramp(t, 12.4, 13.2))
    celebrate = 9.0 <= t < BOP - 0.45
    up = ramp(t, 9.0, 9.3) * (1 - ramp(t, BOP - 0.1, BOP + 0.1))
    if celebrate:
        bounce = 34 * abs(math.sin(2 * math.pi * 1.5 * (t - 9.0)))
    elif BOP - 0.45 <= t < BOP:
        bounce = 0.0
    elif t < 8.0 or 12.6 < t:
        bounce = 6 * abs(math.sin(2 * math.pi * 1.6 * t))
    else:
        bounce = 0.0
    if 7.6 <= t < 8.95 or BOP <= t < 12.0:
        o_mouth = "strain"
    elif 9.0 <= t < BOP:
        o_mouth = "open"
    else:
        o_mouth = "normal"
    stars = (t - BOP) if BOP <= t < 12.6 else 0.0
    # 会長：ミットが押される
    recoil = max([punch(t, x) ** 3 for x in LEADS + REARS] + [min(1.6, big ** 2 * 1.6)])
    talking = any(b[0] <= t < b[1] and b[2] == "M" for b in BUBBLES)
    m_mouth = "open" if talking and int(t * 8) % 2 == 0 else "closed"
    return dict(lead=lead, rear=rear, big=big, o_dx=o_dx, m_dx=m_dx, up=up, bounce=bounce,
                o_mouth=o_mouth, stars=stars, recoil=recoil, m_mouth=m_mouth)


def bop_mitt(t, st):
    """ポコッのときの会長の手前のミットの位置（会長の単位）。オラポン君の頭の上をめがける。"""
    a = ramp(t, BOP - 0.35, BOP) * (1 - ramp(t, BOP + 0.25, BOP + 0.6))
    if a <= 0:
        return None
    xm = X_M + st["m_dx"]
    head_x, head_y = X_O + st["o_dx"] + 10 * SC, GY - (408 - 70) * SC
    tx = 150 + (xm - head_x) / SC
    ty = 408 - (GY - head_y) / SC
    base = mb.M_MITT["near"]
    return (base[0] + (tx - base[0]) * a, base[1] + (ty - base[1]) * a)


def overlay_svg(t):
    st = state(t)
    xo = X_O + st["o_dx"]
    xm = X_M + st["m_dx"]
    o = mb.olapon(lead=st["lead"], rear=st["rear"], up=st["up"], mouth=st["o_mouth"],
                  bounce=st["bounce"], stars=st["stars"])
    # ポコッのときは、ひじを上げて上からたたく
    bop = ramp(t, BOP - 0.35, BOP) * (1 - ramp(t, BOP + 0.25, BOP + 0.6))
    m = mb.manolo(mitt_near=bop_mitt(t, st), recoil=st["recoil"] if t < 9 else 0.0, mouth=st["m_mouth"],
                  near_bend=18 - 70 * bop)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<g transform="translate({xm + 150 * SC:.1f} {GY - 408 * SC:.1f}) scale({-SC} {SC})">{m}</g>'
            f'<g transform="translate({xo - 150 * SC:.1f} {GY - 408 * SC:.1f}) scale({SC})">{o}</g>'
            '</svg>'), st


def burst(d, cx, cy, r, text, font):
    pts = []
    for i in range(24):
        rr = r if i % 2 == 0 else r * 0.55
        a = math.pi * 2 * i / 24
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(255, 230, 90), outline=INK, width=5)
    d.text((cx, cy), text, font=font, fill=(215, 38, 61), anchor="mm", stroke_width=3, stroke_fill=(255, 255, 255))


def bubble(d, cx, bottom, es, ja, f_es, f_ja):
    w = max(d.textlength(es, font=f_es), d.textlength(ja, font=f_ja) if ja else 0) + 70
    h = 150 if ja else 96
    x0, y0 = cx - w / 2, bottom - h
    x0 = max(20, min(W - 20 - w, x0))
    d.polygon([(cx - 22, bottom - 4), (cx + 22, bottom - 4), (cx, bottom + 44)], fill="white", outline=INK, width=5)
    d.rounded_rectangle([x0, y0, x0 + w, bottom], radius=36, fill="white", outline=INK, width=5)
    d.rectangle([cx - 18, bottom - 6, cx + 18, bottom - 2], fill="white")
    d.text((x0 + w / 2, y0 + 50), es, font=f_es, fill=INK, anchor="mm")
    if ja:
        d.text((x0 + w / 2, y0 + 110), ja, font=f_ja, fill=(90, 70, 60), anchor="mm")


_BG = None


def render(n):
    global _BG
    import cairosvg
    from PIL import Image, ImageDraw, ImageFont

    if _BG is None:
        _BG = Image.open(ROOT / "characters" / "scenes" / "gym.png").convert("RGB")
    t = n / FPS
    svg, st = overlay_svg(t)
    chars = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA")
    img = _BG.copy()
    img.paste(chars, (0, 0), chars)
    d = ImageDraw.Draw(img)
    f_es = ImageFont.truetype(FONT_ES, 58)
    f_ja = ImageFont.truetype(FONT_JA, 36)
    f_fx = ImageFont.truetype(FONT_JA, 54)
    xo, xm = X_O + st["o_dx"], X_M + st["m_dx"]
    # パン！（ミットに当たった瞬間）
    contact_x = (xo + xm) / 2 + 10
    if st["lead"] > 0.85:
        burst(d, contact_x, GY - (408 - 206) * SC, 80, "パン！", f_fx)
    if st["rear"] > 0.85 and st["big"] < 0.5:
        burst(d, contact_x + 10, GY - (408 - 222) * SC, 80, "パン！", f_fx)
    if st["big"] > 0.8:
        burst(d, contact_x + 20, GY - (408 - 222) * SC, 170, "バシーン！", ImageFont.truetype(FONT_JA, 56))
    if BOP - 0.05 <= t < BOP + 0.35:
        burst(d, xo + 10 * SC, GY - 360 * SC, 90, "ポコッ", f_fx)
    # 左上の場所テロップ
    if t < 3.0:
        d.rounded_rectangle([40, 36, 640, 120], radius=20, fill=(255, 255, 255), outline=INK, width=4)
        d.text((340, 78), "ボクシングジムで ミット打ち", font=ImageFont.truetype(FONT_JA, 40), fill=INK, anchor="mm")
    # 吹き出し
    for t0, t1, who, es, ja in BUBBLES:
        if t0 <= t < t1:
            if who == "M":
                bubble(d, xm + 30, GY - 330 * SC, es, ja, f_es, f_ja)
            else:
                bubble(d, xo - 40, GY - 385 * SC - st["bounce"] * SC, es, ja, f_es, f_ja)
    # きょうのスペイン語
    if t >= END_START:
        a = ramp(t, END_START, END_START + 0.5)
        dark = Image.new("RGB", img.size, (20, 14, 10))
        img = Image.blend(img, dark, 0.55 * a)
        d = ImageDraw.Draw(img)
        if a > 0.6:
            d.rounded_rectangle([360, 150, 1560, 930], radius=40, fill=(255, 248, 236), outline=INK, width=6)
            d.text((960, 240), "きょうのスペイン語", font=ImageFont.truetype(FONT_JA, 64), fill=(215, 38, 61), anchor="mm")
            for i, (es, ja) in enumerate(PHRASES):
                if t >= END_START + 0.6 + i * 0.7:
                    y = 380 + i * 140
                    d.text((470, y), es, font=ImageFont.truetype(FONT_ES, 64), fill=INK, anchor="lm")
                    d.text((1060, y), ja, font=ImageFont.truetype(FONT_JA, 44), fill=(90, 70, 60), anchor="lm")
    return img.tobytes()


def main():
    import subprocess

    if not (ROOT / "characters" / "scenes" / "gym.png").exists():
        subprocess.run([sys.executable, str(ROOT / "characters" / "scenes" / "make_gym.py")], check=True)
    out = ROOT / "output" / "anime" / "gym_training.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    total = int(DUR * FPS)
    with Pool(4) as pool:
        for frame in pool.imap(render, range(total), chunksize=4):
            ff.stdin.write(frame)
    ff.stdin.close()
    ff.wait()
    print(f"できました: {out}（{DUR:.0f}秒）")


if __name__ == "__main__":
    main()
