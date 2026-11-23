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
MM_DICT = ["コーヒー/こおひい", "熱すぎ/あつすぎ", "何年か/なんねんか", "高めの方/たかめのかた", "心配な方/しんぱいなかた",
           "高い方/たかいかた", "大勝/たいしょう", "火種/ひだね", "甘党/あまとう", "一方/いっぽう", "主な/おもな",
           "天秤/てんびん", "互角/ごかく", "優勢/ゆうせい", "煮出/にだ", "南米/なんべい", "行ってみましょう/いってみましょう",
           "研究者/けんきゅうしゃ", "数値/すうち", "高評価/こうひょうか", "濾した/こした", "濾す/こす", "膵臓/すいぞう",
           "14日間/じゅうよっかかん", "年前/ねんまえ", "年後/ねんご"]

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
    return f"minimax3|{MM_MODEL}|{MM_VOICE}|{MM_SPEED}|{'/'.join(MM_DICT)}" if ENGINE == "minimax" else f"{VOICE}|{SPEED}"


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


# 読み方を指定どおりにするため、MiniMax に送る前に数字・記号・「派」などを、かなに書き換える
P = "§"   # 少しの間(最後に MiniMax の間の記号 <#0.2#> に置き換える)
MM_FIXED = [
    ("1.5〜3.5杯", "いちてんごはいからさんてんごはいまで"),
    ("3〜4杯", "さんよんはい"), ("3から4杯", "さんからよんはい"), ("3〜5杯", "さんからごはい"), ("1〜2杯", "いちからにはい"),
    ("40〜79歳", "よんじっさいからななじゅうきゅうさいまで"),
    ("1日2杯以上", f"いちにち{P}にはいいじょう"),
    ("約2倍", f"やく{P}にばい"), ("約90社", f"やく{P}きゅうじゅっしゃ"),
    ("1日約1,000歩", "いちにちやくせんぽ"), ("1日1万歩", "いちにちいちまんぽ"), ("1日1個", "いちにちいっこ"),
    ("約1.5倍", "やくいってんごばい"), ("36分", "さんじゅうろっぷん"),
    ("10か国", "じっかこく"), ("今日は飲む", "きょうわのむ"), ("今日は飲まない", "きょうわのまない"),
    ("今日", "きょう"), ("一日中", "いちにちじゅう"), ("1日", "いちにち"),
    ("いい派", "イイハ"), ("悪い派", "ワルイハ"), ("コーヒー", "コーヒー"),
    ("WHO", "ダブリューエイチオー"), ("65℃", "ろくじゅうごど"), ("℃", "ど"),
]
COUNTER = {"杯": {1: "いっぱい", 2: "にはい", 3: "さんばい", 4: "よんはい", 5: "ごはい", 6: "ろっぱい", 8: "はっぱい", 10: "じゅっぱい"},
           "歳": {60: "ろくじゅっさい", 40: "よんじっさい"}}


def num_kana(s):
    n = jp_number(s)
    return None if n is None else (big_kana(n) if n else "ぜろ")


def mm_text(text):
    """MiniMax に送る文。数字はすべて読み方に直す。"""
    t = text.replace("……", "、").replace("「", "").replace("」", "、")
    for a, b in MM_FIXED:
        t = t.replace(a, b)
    t = re.sub(r"第(\d+)話", lambda m: f"だい{num_kana(m.group(1))}わ", t)
    t = re.sub(r"(\d{4})年", lambda m: (lambda y: ("にせん" if y // 1000 == 2 else "せん") + kana(y % 1000))(int(m.group(1))) + "ねん", t)
    t = re.sub(r"(\d+)杯", lambda m: COUNTER["杯"].get(int(m.group(1)), num_kana(m.group(1)) + "はい"), t)
    t = re.sub(r"(\d+)歳", lambda m: COUNTER["歳"].get(int(m.group(1)), num_kana(m.group(1)) + "さい"), t)
    t = re.sub(r"([\d,]+(?:万)?(?:\d+千)?)人", lambda m: (num_kana(m.group(1)) or m.group(1)) + "にん", t)
    t = re.sub(r"(\d+(?:\.\d+)?)%", lambda m: (num_kana(m.group(1)) if "." not in m.group(1) else m.group(1)) + "パーセント", t)
    t = re.sub(r"(\d+)対(\d+)", lambda m: f"{num_kana(m.group(1))}たい{num_kana(m.group(2))}", t)
    t = re.sub(r"(\d+)年", lambda m: num_kana(m.group(1)) + "ねん", t)
    t = re.sub(r"(\d+)割", lambda m: num_kana(m.group(1)) + "わり", t)
    t = re.sub(r"(\d+)倍", lambda m: num_kana(m.group(1)) + "ばい", t)
    t = re.sub(r"([\d,]+)以上", lambda m: num_kana(m.group(1)) + "いじょう", t)
    t = re.sub(r"(\d[\d,]*万?)", lambda m: num_kana(m.group(1)) or m.group(1), t)   # 残りの数字(議席など)
    t = t.replace("ねん後", "ねんご").replace("ねん前", "ねんまえ").replace("ねんぶり", "ねんぶり")
    return t.replace(P, "<#0.2#>")


def synth_minimax(text):
    import io
    import json
    import time
    import urllib.request
    import soundfile as sf
    body = {"model": MM_MODEL, "text": mm_text(text), "stream": False, "language_boost": "Japanese",
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
