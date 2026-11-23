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

# 読み上げのルール(全回共通。2026-11-23 追加)
# ・「29%」は数字のあとに「パーセント」と読む(数字とパーセントをまとめて、かなの読みを辞書に入れる)
# ・「1日1杯」「1日20g」のように 1日 のあとに量が続くときは、1日 のあとに少し間を置く(MiniMax の <#秒#>)
PERCENT_READING = True
ICHINICHI_PAUSE = 0.03   # 秒。0 で間を置かない(2026-11-23 0.25→0.1→0.03:「間を置きすぎ」の指摘で詰める)

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


MM_EMOTION = None   # 声の感情(None=自動。"happy" "calm" など)。場面ごとに回のスクリプトから切りかえてよい


def voice_key():
    rules = f"|pct{int(PERCENT_READING)}|pause{ICHINICHI_PAUSE}|{'/'.join(a + '=' + b for a, b in TEXT_READ)}" if (PERCENT_READING or ICHINICHI_PAUSE) else ""
    rules += f"|emo{MM_EMOTION}" if MM_EMOTION else ""
    return (f"minimax4|{MM_MODEL}|{MM_VOICE}|{MM_SPEED}|{'/'.join(MM_DICT)}{rules}" if ENGINE == "minimax"
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


# 間(ま)の長さ(秒)。MiniMax は文中の <#秒#> で間をあける
PAUSE_HA = 0.15     # 「いい派」と助詞「は(わ)」の間
PAUSE_NUM = 0.2     # 「いい派」と議席の数字の間
PAUSE_SHORT = 0.03  # 「約」と数字の間(「1日」のあとは ICHINICHI_PAUSE)。0.1 でも「間を置きすぎ」
PAUSE_QUOTE_HA = 0.03   # 「卵は食べていい」派 のように、かぎかっこと「派」の間(ほんの少し)
# 数字の送り方。"kana"=数字をかなに直して送る / "dict"=数字・年号・人数・議席は数字のまま送り、読み方は辞書(pronunciation_dict)で指定する
# (かなや漢数字で送ると「68」「1913年」の読みが不自然になったため。卵の回は "dict")
NUM_STYLE = "kana"

KOSU = {1: "いっこ", 2: "ニコ",   # 「にこ」は「にご」と濁って聞こえるのでカタカナで送る
        3: "さんこ", 4: "よんこ", 5: "ごこ", 6: "ろっこ", 7: "ななこ", 8: "はっこ", 9: "きゅうこ", 10: "じゅっこ"}
HA_YOMI = {"いい": "いい", "悪い": "わるい"}


def tts_text(t):
    """合成の前に、読み方と間を文章に書き込む(全回共通のルール)。

    - 「いい派は」→「いいは・わ」(派と助詞の間に少し間)/「いい派、15議席」→「いいは・じゅうごぎせき」
    - 「約3万人」→「やく・さんまんにん」/「1日200mg」→「1日・にひゃくミリグラム」(約・1日のあとに少し間)
    - 「11%」→「じゅういちパーセント」、「750mg未満」→「ななひゃくごじゅうミリグラムみまん」、「半個」→「はんこ」
    """
    p = lambda sec: f"<#{sec}#>"  # noqa: E731
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)
    t = re.sub(r"(いい|悪い)派は", lambda m: HA_YOMI[m.group(1)] + "は" + p(PAUSE_HA) + "わ", t)
    t = re.sub(r"(いい|悪い)派、?(?=\d)", lambda m: HA_YOMI[m.group(1)] + "は" + p(PAUSE_NUM), t)
    t = re.sub(r"(いい|悪い)派", lambda m: HA_YOMI[m.group(1)] + "は", t)
    t = add_pauses(t)   # 「1日」のあとに量が続くときの間(ICHINICHI_PAUSE)
    t = re.sub(r"約(?=\d)", "やく" + p(PAUSE_SHORT), t)
    t = re.sub(r"(\d+)mg", lambda m: kana(int(m.group(1))) + "ミリグラム", t)
    t = t.replace("未満", "みまん")
    t = re.sub(r"(?:(\d+(?:\.\d+)?)〜)?(\d+(?:\.\d+)?)%",
               lambda m: ((decimal_kana(m.group(1)) + "から") if m.group(1) else "") + decimal_kana(m.group(2)) + "パーセント", t)
    if NUM_STYLE != "dict":
        t = re.sub(r"(\d+)議席", lambda m: kana(int(m.group(1))) + "ぎせき", t)
    t = t.replace("半個", "ハンコ").replace("2個目", "ニコめ")   # ひらがなだと「はんご」「にご」と濁る
    t = re.sub(r"(\d+)個", lambda m: KOSU.get(int(m.group(1)), kana(int(m.group(1))) + "こ"), t)

    def people(m):
        n = jp_number(m.group(1))
        return ({1: "ひとり", 2: "ふたり", 4: "よにん"}.get(n) or big_kana(n) + "にん") if n else m.group(0)
    if NUM_STYLE != "dict":
        t = re.sub(r"(\d+万\d+千|\d+万|\d+)人", people, t)
    t = t.replace("派", "ハ")   # 残った「派」(「…」派 など)を助詞の「わ」と読ませない
    return t


# 回ごとに、文字を直接読み方に置きかえる語(例 ("飲む国", "のむくに"))。その回のスクリプトで narrate.TEXT_READ += する
TEXT_READ = []


def too_long(text, sec):
    """合成した声が、文字数に比べて長すぎる(笑い声・うなり声などの壊れた音声)か。"""
    plain = re.sub(r"<#[\d.]+#>", "", text)
    pauses = sum(float(x) for x in re.findall(r"<#([\d.]+)#>", text))
    return sec > len(plain) / 5.0 + pauses + 3.0

# ---- 全回共通の読み方の流れ:pre_text(決まった言い回し)→ tts_text(派・約・1日の間など)→ post_text(残りの数字をかなに)
# 決まった言い回し(数字ごと、かなに直す)。tts_text より前に使う
MM_FIXED = [
    ("1.5〜3.5杯", "いちてんごはいからさんてんごはいまで"),
    ("3〜4杯", "さんよんはい"), ("3から4杯", "さんからよんはい"), ("3〜5杯", "さんからごはい"), ("1〜2杯", "いちからにはい"),
    ("40〜79歳", "よんじっさいからななじゅうきゅうさいまで"),
    ("約1.5倍", "やくいってんごばい"), ("36分", "さんじゅうろっぷん"),
    ("10か国", "じっかこく"), ("今日は飲む", "きょうわのむ"), ("今日は飲まない", "きょうわのまない"),
    ("今日", "きょう"), ("一日中", "いちにちじゅう"),
    ("WHO", "ダブリューエイチオー"), ("65℃", "ろくじゅうごど"), ("℃", "ど"),
]
COUNTER = {"杯": {1: "いっぱい", 2: "にはい", 3: "さんばい", 4: "よんはい", 5: "ごはい", 6: "ろっぱい", 8: "はっぱい", 10: "じゅっぱい"},
           "歳": {60: "ろくじゅっさい", 40: "よんじっさい", 20: "はたち"},
           "社": {90: "きゅうじゅっしゃ", 10: "じゅっしゃ"},
           "歩": {1000: "せんぽ", 10000: "いちまんぽ", 3000: "さんぜんぽ", 8000: "はっせんぽ"}}


KAN = "〇一二三四五六七八九"


def kanji_num(n):
    """1986 → 千九百八十六(年号用)。"""
    out = ""
    for unit, name in ((1000, "千"), (100, "百"), (10, "十")):
        q, n = divmod(n, unit)
        if q:
            out += ("" if q == 1 else KAN[q]) + name
    return out + (KAN[n] if n else "")


def num_kana(s):
    n = jp_number(s)
    return None if n is None else (big_kana(n) if n else "ぜろ")


def pre_text(text):
    t = add_pauses(text)   # 「1日」のあとの間は、数字をかなに直す前に入れる(あとだと「1日3〜5杯」が見つからない)
    for a, b in TEXT_READ:   # 回ごとの読み方(文字を直接置きかえる)。決まった言い回しより先に使う
        t = t.replace(a, b)
    t = t.replace("」派", f"<#{PAUSE_QUOTE_HA}#>派")   # 「卵は食べていい」派:かぎかっこのあとは、ほんの少しの間だけ
    t = t.replace("……", "、").replace("「", "").replace("」", "、").replace("、。", "。").replace("、？", "？")
    for a, b in MM_FIXED:
        t = t.replace(a, b)
    return t


def post_text(t):
    """tts_text のあとに残った数字を、すべてかなに直す(<#秒#> の間の記号はそのまま)。"""
    marks = []
    t = re.sub(r"<#[\d.]+#>", lambda m: marks.append(m.group(0)) or f"\x00{chr(65 + len(marks) - 1)}\x00", t)
    t = t.replace("1日", "いちにち")
    t = re.sub(r"第(\d+)話", lambda m: f"だい{num_kana(m.group(1))}わ", t)
    if NUM_STYLE == "dict":   # 残りの数字は数字のまま(読み方は mm_tone の辞書で指定)
        t = t.replace("いいは", "いいハ").replace("わるいは", "わるいハ")
        return re.sub(r"\x00([A-Z])\x00", lambda m: marks[ord(m.group(1)) - 65], t)
    t = re.sub(r"(\d{3}4)年", lambda m: "\x01" + kana(int(m.group(1)))[:-2] + "よねん", t)   # 4で終わる年は「〜よねん」(2014年=にせんじゅうよねん)
    t = re.sub(r"(\d{4})年", lambda m: "\x01" + kanji_num(int(m.group(1))) + "年", t)   # 年号は漢数字で(ひらがなだと読み崩れる)
    for unit, yomi in (("杯", "はい"), ("歳", "さい"), ("社", "しゃ"), ("歩", "ほ")):
        t = re.sub(r"([\d,]+万?)" + unit, lambda m, u=unit, y=yomi: COUNTER[u].get(jp_number(m.group(1)) or -1, (num_kana(m.group(1)) or "") + y), t)
    t = re.sub(r"(\d+)対(\d+)", lambda m: f"{num_kana(m.group(1))}たい{num_kana(m.group(2))}", t)
    t = re.sub(r"(\d+)年", lambda m: num_kana(m.group(1)) + "ねん", t)
    t = re.sub(r"(\d+)割", lambda m: num_kana(m.group(1)) + "わり", t)
    t = re.sub(r"(\d+(?:\.\d+)?)倍", lambda m: decimal_kana(m.group(1)) + "ばい", t)
    t = re.sub(r"(\d+)以上", lambda m: num_kana(m.group(1)) + "いじょう", t)
    t = re.sub(r"(\d+\.\d+)", lambda m: decimal_kana(m.group(1)), t)
    t = re.sub(r"(\d+万?)", lambda m: num_kana(m.group(1)) or m.group(1), t)   # 残りの数字
    t = re.sub(r"(^|[、。！？\s])\x01", r"\1", t).replace("\x01", "<#0.15#>")   # 文の頭・句読点のあとは間を入れない
    t = t.replace("ねん後", "ねんご").replace("ねん前", "ねんまえ").replace("年後", "年ご").replace("年前", "年まえ")
    t = t.replace("いいは", "いいハ").replace("わるいは", "わるいハ")   # 派の「は」を助詞の「わ」と読ませない
    return re.sub(r"\x00([A-Z])\x00", lambda m: marks[ord(m.group(1)) - 65], t)


def mm_text(text):
    """MiniMax に送る文(全回共通)。数字はすべて読み方に直し、間を入れる。"""
    return post_text(tts_text(pre_text(text)))


def year_kana(y):
    return ("にせん" if y // 1000 == 2 else "せん") + kana(y % 1000)


def nen_kana(n):
    return (kana(n)[:-2] + "よ" if n % 10 == 4 else kana(n)) + "ねん"


def mm_tone(text):
    """MiniMax の読み方辞書。NUM_STYLE="dict" のときは、送る文に残った数字の読み方を足す(長いものから)。"""
    if NUM_STYLE != "dict":
        return MM_DICT
    sent = re.sub(r"<#[\d.]+#>", " ", mm_text(text))
    out = {}
    for y in re.findall(r"(\d{4})年", sent):
        out[f"{y}年"] = year_kana(int(y)) + "ねん"
    for a, b in re.findall(r"(\d+)対(\d+)", sent):
        out[f"{a}対{b}"] = f"{num_kana(a)}たい{num_kana(b)}"
    for n in re.findall(r"(\d+)議席", sent):
        out[f"{n}議席"] = num_kana(n) + "ぎせき"
    for n in re.findall(r"(\d+万\d+千|\d+万|\d+)人", sent):
        v = jp_number(n)
        out[f"{n}人"] = {1: "ひとり", 2: "ふたり", 4: "よにん"}.get(v) or big_kana(v) + "にん"
    for n in re.findall(r"(?<!\d)(\d{1,3})年", sent):
        out[f"{n}年"] = nen_kana(int(n))
    for n in re.findall(r"(?<![\d万])(\d+)(?![\d年人議対万])", sent):
        out.setdefault(n, num_kana(n))
    return MM_DICT + [f"{k}/{v}" for k, v in sorted(out.items(), key=lambda kv: -len(kv[0]))]




def synth_minimax(text):
    import io
    import json
    import time
    import urllib.request
    import soundfile as sf
    body = {"model": MM_MODEL, "text": mm_text(text), "stream": False, "language_boost": "Japanese",
            "output_format": "hex", "voice_setting": {"voice_id": MM_VOICE, "speed": MM_SPEED, "vol": 1, "pitch": 0},
            "pronunciation_dict": {"tone": mm_tone(text)},
            "audio_setting": {"sample_rate": RATE, "format": "wav", "channel": 1}}
    if MM_EMOTION:
        body["voice_setting"]["emotion"] = MM_EMOTION
    for attempt in range(4):
        req = urllib.request.Request("https://api.minimax.io/v1/t2a_v2", data=json.dumps(body).encode(),
                                     headers={"Authorization": "Bearer proxy-injected", "Content-Type": "application/json"})
        j = json.load(urllib.request.urlopen(req, timeout=180))
        code = j["base_resp"]["status_code"]
        if code == 0:
            a, sr = sf.read(io.BytesIO(bytes.fromhex(j["data"]["audio"])), dtype="float32")
            a = a if a.ndim == 1 else a.mean(axis=1)
            if too_long(body["text"], len(a) / sr):   # 壊れた音声(笑い声など)は使わず作り直す
                print(f"  ! 声が長すぎるので作り直し({len(a) / sr:.1f}秒): {text[:30]}…", flush=True)
                continue
            return a
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
