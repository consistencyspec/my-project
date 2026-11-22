"""ナレーションの音声を作る。ENGINE で MiniMax(有料 API)か Kokoro(Apache-2.0、無料)を選ぶ。

読み間違えやすい数字・記号を、読み方(かな)に直してから合成する。
  .venv/bin/python scripts/narrate.py "<文章>" out.wav     # 1つだけ作る(確認用)
"""
import re
import sys

ENGINE = "minimax"   # "minimax" か "kokoro"

# MiniMax(api.minimax.io。API キーは環境のネットワーク設定でプロキシが付ける)
MM_MODEL = "speech-2.8-hd"
MM_VOICE = "Japanese_IntellectualSenior"   # 知的で落ち着いた男性の声
MM_SPEED = 1.2
# 読み間違えやすい語(元の文字/読み方)。MiniMax の pronunciation_dict に渡す
MM_DICT = ["1日/いちにち", "悪い派/わるいは", "いい派/いいは", "濾した/こした", "濾す/こす", "膵臓/すいぞう", "8杯/はっぱい", "6杯/ろっぱい",
           "1杯/いっぱい", "10杯/じゅっぱい", "14日間/じゅうよっかかん", "644人/ろっぴゃくよんじゅうよにん"]

# Kokoro
VOICE = "jf_alpha"   # 落ち着いた女性の声
SPEED = 1.43         # 0.95 の1.5倍(テンポよく)
RATE = 24000

HAI = {"1": "いっぱい", "2": "にはい", "3": "さんばい", "4": "よんはい", "5": "ごはい", "6": "ろっぱい",
       "7": "ななはい", "8": "はっぱい", "9": "きゅうはい", "10": "じゅっぱい"}
FIXED = [
    ("1.5〜3.5杯", "いってんごからさんてんごはい"),
    ("3〜4杯", "さんからよんはい"), ("3〜5杯", "さんからごはい"), ("1〜2杯", "いちからにはい"),
    ("1.5倍", "いってんごばい"), ("644人", "ろっぴゃくよんじゅうよにん"), ("369人", "さんびゃくろくじゅうきゅうにん"),
    ("WHO", "ダブリューエイチオー"), ("65℃", "65度"), ("℃", "度"),
    ("40〜79歳", "40歳から79歳"), ("16%", "16パーセント"), ("22%", "22パーセント"), ("53%", "53パーセント"),
    ("1万9千人", "いちまんきゅうせんにん"), ("1万4千人", "いちまんよんせんにん"),
    ("14日間", "じゅうよっかかん"),
    ("約1000歩", "やくせんぽ"), ("10年戦争", "じゅうねんせんそう"), ("新常識", "しんじょうしき"),
    ("濾した", "こした"), ("濾す", "こす"),
]


DIG = ["", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう"]


def kana(n):
    """0〜9999 の数をかなに。"""
    out = ""
    for unit, name, special in ((1000, "せん", {1: "せん", 3: "さんぜん", 8: "はっせん"}),
                                (100, "ひゃく", {1: "ひゃく", 3: "さんびゃく", 6: "ろっぴゃく", 8: "はっぴゃく"}),
                                (10, "じゅう", {1: "じゅう"})):
        q, n = divmod(n, unit)
        if q:
            out += special.get(q, DIG[q] + name)
    return out + DIG[n]


def reading(text):
    t = re.sub(r"(\d),(\d{3})", r"\1\2", text)
    t = re.sub(r"(\d{4})年", lambda m: (lambda y: ("にせん" if y // 1000 == 2 else "せん") + kana(y % 1000))(int(m.group(1))) + "ねん", t)
    t = re.sub(r"(\d+)万人", r"\1万 人", t)
    t = re.sub(r"第(\d+)話", lambda m: f"だい{m.group(1)}わ", t)
    for a, b in FIXED:
        t = t.replace(a, b)
    t = re.sub(r"(\d+)杯", lambda m: HAI.get(m.group(1), m.group(1) + "はい"), t)
    t = t.replace("%", "パーセント").replace("+", "プラス").replace("「", "").replace("」", "、")
    t = t.replace("…", "、").replace("？", "？ ").replace("！", "！ ")
    return t


_pipe = None


def voice_key():
    return f"minimax|{MM_MODEL}|{MM_VOICE}|{MM_SPEED}|{'/'.join(MM_DICT)}" if ENGINE == "minimax" else f"{VOICE}|{SPEED}"


def synth_minimax(text):
    import io
    import json
    import time
    import urllib.request
    import soundfile as sf
    body = {"model": MM_MODEL, "text": text.replace("……", "、"), "stream": False, "language_boost": "Japanese",
            "output_format": "hex", "voice_setting": {"voice_id": MM_VOICE, "speed": MM_SPEED, "vol": 1, "pitch": 0},
            "pronunciation_dict": {"tone": MM_DICT},
            "audio_setting": {"sample_rate": RATE, "format": "wav", "channel": 1}}
    for attempt in range(4):
        req = urllib.request.Request("https://api.minimax.io/v1/t2a_v2", data=json.dumps(body).encode(),
                                     headers={"Authorization": "Bearer proxy-injected", "Content-Type": "application/json"})
        j = json.load(urllib.request.urlopen(req, timeout=180))
        code = j["base_resp"]["status_code"]
        if code == 0:
            a, sr = sf.read(io.BytesIO(bytes.fromhex(j["data"]["audio"])), dtype="float32")
            return a if a.ndim == 1 else a.mean(axis=1)
        if code in (1002, 1039, 1001):  # 混雑・時間切れは待って再試行
            time.sleep(5 * (attempt + 1))
            continue
        raise RuntimeError(f"MiniMax error {code}: {j['base_resp']['status_msg']}")
    raise RuntimeError("MiniMax: retries exhausted")


def synth(text):
    """文章 → 音声(numpy, 24kHz)。"""
    if ENGINE == "minimax":
        return synth_minimax(text)
    global _pipe
    import numpy as np
    if _pipe is None:
        from kokoro import KPipeline
        _pipe = KPipeline(lang_code="j", repo_id="hexgrad/Kokoro-82M")
    chunks = [a.numpy() if hasattr(a, "numpy") else a for _, _, a in _pipe(reading(text), voice=VOICE, speed=SPEED)]
    return np.concatenate(chunks)


if __name__ == "__main__":
    import soundfile as sf
    sf.write(sys.argv[2], synth(sys.argv[1]), RATE)
    print(sys.argv[2])
