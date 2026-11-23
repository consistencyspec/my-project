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
MM_DICT = ["コーヒー/こーひー", "1日/いちにち", "今日/きょう", "熱すぎ/あつすぎ", "一日中/いちにちじゅう",
           "何年か/なんねんか", "高めの方/たかめのかた", "心配な方/しんぱいなかた", "高い方/たかいかた",
           "37年前/さんじゅうななねんまえ", "37年後/さんじゅうななねんご", "25年/にじゅうごねん", "大勝/たいしょう",
           "火種/ひだね", "1日1個/いちにちいっこ", "甘党/あまとう", "一方/いっぽう", "主な/おもな", "天秤/てんびん",
           "互角/ごかく", "優勢/ゆうせい", "煮出/にだ", "南米/なんべい", "行ってみましょう/いってみましょう",
           "研究者/けんきゅうしゃ", "数値/すうち", "高評価/こうひょうか", "悪い派/わるいは", "いい派/いいは", "濾した/こした", "濾す/こす", "膵臓/すいぞう", "8杯/はっぱい", "6杯/ろっぱい",
           "1杯/いっぱい", "10杯/じゅっぱい", "14日間/じゅうよっかかん", "644人/ろっぴゃくよんじゅうよにん"]

# 読み上げのルール(全回共通。2026-11-23 追加)
# ・「29%」は数字のあとに「パーセント」と読む(数字とパーセントをまとめて、かなの読みを辞書に入れる)
# ・「1日1杯」「1日20g」のように 1日 のあとに量が続くときは、1日 のあとに少し間を置く(MiniMax の <#秒#>)
PERCENT_READING = True
ICHINICHI_PAUSE = 0.25   # 秒。0 で間を置かない

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
    rules = f"|pct{int(PERCENT_READING)}|pause{ICHINICHI_PAUSE}" if (PERCENT_READING or ICHINICHI_PAUSE) else ""
    return (f"minimax2|{MM_MODEL}|{MM_VOICE}|{MM_SPEED}|{'/'.join(MM_DICT)}{rules}" if ENGINE == "minimax"
            else f"{VOICE}|{SPEED}")


def decimal_kana(s):
    """「1.5」「49」「0.68」→ かな。"""
    if "." in s:
        a, b = s.split(".")
        return (kana(int(a)) or "れい") + "てん" + "".join(DIG[int(c)] or "ぜろ" for c in b)
    return kana(int(s)) or "ぜろ"


def percent_dict(text):
    """「29%」「3〜5%」→「29%/にじゅうきゅうパーセント」。数字のあとにパーセントと読ませる。"""
    out = []
    for a, b in sorted(set(re.findall(r"(?:(\d+(?:\.\d+)?)〜)?(\d+(?:\.\d+)?)%", text)), key=lambda x: -len(x[0] + x[1])):
        src = (f"{a}〜" if a else "") + f"{b}%"
        out.append(f"{src}/{(decimal_kana(a) + 'から') if a else ''}{decimal_kana(b)}パーセント")
    return out


def add_pauses(text):
    """「1日」のあとに量(数字・約・半分・グラス・純アルコールなど)が続くとき、少し間を置く。"""
    if not ICHINICHI_PAUSE:
        return text
    return re.sub(r"1日(?=[0-9約半グ純平お]|あたり)", f"1日<#{ICHINICHI_PAUSE}#>", text)


def big_kana(n):
    """0〜99,999,999 の数をかなに(万まで)。"""
    man, rest = divmod(n, 10000)
    out = (kana(man) + "まん") if man else ""
    return out + (kana(rest) if rest else "")


def jp_number(s):
    """「52万」「1万9千」「1,000」「100」→ 数。読めなければ None。"""
    s = s.replace(",", "")
    m = re.fullmatch(r"(?:(\d+)万)?(?:(\d+)千)?(\d+)?", s)
    if not m or not any(m.groups()):
        return None
    man, sen, rest = (int(g) if g else 0 for g in m.groups())
    return man * 10000 + sen * 1000 + rest


def auto_dict(text):
    """文章の中の「年号」と「数+人」の読み方を、自動で辞書にする。"""
    out = []
    for y in sorted(set(re.findall(r"(\d{4})年", text))):
        n = int(y)
        out.append(f"{y}年/{('にせん' if n // 1000 == 2 else 'せん') + kana(n % 1000)}ねん")
    for num in sorted(set(re.findall(r"([\d,]+万?(?:\d+千)?|\d+万\d+千)人", text)), key=len, reverse=True):
        n = jp_number(num)
        if n is None:
            continue
        small = {1: "ひとり", 2: "ふたり", 4: "よにん"}
        out.append(f"{num}人/{small.get(n, big_kana(n) + 'にん')}")
    if "数十万人" in text:
        out.append("数十万人/すうじゅうまんにん")
    return out


def synth_minimax(text):
    import io
    import json
    import time
    import urllib.request
    import soundfile as sf
    tone = MM_DICT + auto_dict(text) + (percent_dict(text) if PERCENT_READING else [])
    body = {"model": MM_MODEL, "text": add_pauses(text.replace("……", "、")), "stream": False, "language_boost": "Japanese",
            "output_format": "hex", "voice_setting": {"voice_id": MM_VOICE, "speed": MM_SPEED, "vol": 1, "pitch": 0},
            "pronunciation_dict": {"tone": tone},
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
