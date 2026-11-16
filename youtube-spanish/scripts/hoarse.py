"""声を「しゃがれ声」にする。

使い方: python3 scripts/hoarse.py <入力.wav> <出力.wav> <強さ 0〜5>（4・5 は「つぶれた声」）

しゃがれ声を作る3つの処理を重ねる：
1. 息っぽさ … 声の大きさに合わせて「スー」という息の音（高めの雑音）を足す（無音のところには足さない）
2. ガラガラ感 … 声の大きさを、不規則に細かく揺らす（声帯がこすれるような感じ）
3. ざらつき … ほんの少し音をつぶして、倍音を足す
"""
import sys
import wave

import numpy as np

LEVELS = {  # 強さ: (息の量, 揺れの深さ, つぶし具合, 声の帯域をしぼるか)
    0: (0.0, 0.0, 1.0, False),
    1: (0.06, 0.10, 1.4, False),
    2: (0.11, 0.18, 2.0, False),
    3: (0.18, 0.26, 2.8, False),
    4: (0.20, 0.32, 5.0, True),   # つぶれた声（叫びすぎたあとのような声）
    5: (0.26, 0.40, 8.0, True),   # かなりつぶれた声
}


def read(path):
    with wave.open(str(path), "rb") as w:
        rate, n, ch, width = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError("16bit の wav にしてください")
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, rate


def write(path, x, rate):
    y = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def envelope(x, rate, ms=12):
    k = max(1, int(rate * ms / 1000))
    return np.sqrt(np.convolve(x * x, np.ones(k) / k, mode="same"))


def band_noise(n, rate, lo=1500, hi=6000, seed=0):
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / rate)
    spec[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(spec, n)
    return y / (np.abs(y).max() + 1e-9)


def hoarse(x, rate, level, seed=0):
    breath, depth, drive, narrow = LEVELS[level]
    if level == 0:
        return x
    env = envelope(x, rate)
    t = np.arange(len(x)) / rate
    rng = np.random.default_rng(seed + 1)
    # ガラガラ感：40〜70Hz で揺れる速さ自体も少しずつ変える（規則的だと機械っぽくなるため）
    freq = 55 + 15 * np.interp(t, np.linspace(0, t[-1] if len(t) else 1, 50), rng.uniform(-1, 1, 50))
    phase = 2 * np.pi * np.cumsum(freq) / rate
    rough = 1 + depth * np.sin(phase) * (0.6 + 0.4 * rng.random(len(x)))
    y = x * rough
    # ざらつき
    y = np.tanh(drive * y) / np.tanh(drive)
    # 息っぽさ（声の大きさに比例。無音には足さない）
    y = y + breath * env / (env.max() + 1e-9) * band_noise(len(x), rate, seed=seed) * np.abs(x).max()
    if narrow:
        # のどが詰まったような感じ：低音と高音を削り、中ほど（のどの響き）を少し持ち上げる
        spec = np.fft.rfft(y)
        f = np.fft.rfftfreq(len(y), 1 / rate)
        gain = np.where((f > 250) & (f < 4500), 1.0, 0.25)
        gain *= 1 + 0.6 * np.exp(-((f - 1200) / 500) ** 2)
        y = np.fft.irfft(spec * gain, len(y))
    return y / (np.abs(y).max() + 1e-9) * 0.9


def main():
    src, dst, level = sys.argv[1], sys.argv[2], int(sys.argv[3])
    x, rate = read(src)
    write(dst, hoarse(x, rate, level), rate)


if __name__ == "__main__":
    main()
