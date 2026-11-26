"""合成した声を音声認識(Whisper)で聞き取り、読み間違い・余計な音がないか調べる(全回で使える)。

使い方(回のスクリプトから):
    import voice_check
    probs = voice_check.problems(narr, audio, rate)   # [] なら合格
faster-whisper が入っていなければ、チェックは飛ばす(.venv/bin/pip install faster-whisper scipy)。

分かっている MiniMax のくせ(2026-11-23 に確かめた):
- 「順位」は、かな(じゅんい)やカタカナ(ジュンイ)で送ると「潤い(うるおい)」と読まれる。漢字のまま、前に「ランキングの」「沖縄の」などをつけると正しく読まれやすい。それでも外れることがあるので、このチェックで作り直す
- 「たった13」が「ことわった」と聞こえることがある →「わずか13」にする
"""
import re

# 認識結果にこれが出たら読み間違い
FORBIDDEN = ["潤い", "うるおい", "ウルオイ", "断った", "ことわった"]
# 台本にこの語があるなら、認識結果にもどれかが出ていること
REQUIRED = {"順位": ["順位"], "天草": ["天草", "甘草", "甘くさ", "あまくさ", "アマクサ"]}

_model = None


def _load():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            _model = False
            return False
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def transcribe(audio, rate):
    m = _load()
    if not m:
        return None
    import scipy.signal as ss
    a16 = ss.resample_poly(audio, 16000, rate) if rate != 16000 else audio
    segs, _ = m.transcribe(a16, language="ja", beam_size=5)
    return "".join(s.text for s in segs)


def problems(narr, audio, rate, sent=None):
    """問題のリスト(空なら合格)。sent=MiniMax に送った文(長さの比較に使う)。"""
    heard = transcribe(audio, rate)
    if heard is None:
        return []
    out = [f"「{w}」と聞こえる" for w in FORBIDDEN if w in heard]
    for k, alts in REQUIRED.items():
        if k in narr and not any(a in heard for a in alts):
            out.append(f"「{k}」が聞き取れない")
    # 余計な音(台本にない言葉)が入ると、聞き取った文字が台本よりずっと多くなる
    base = re.sub(r"[、。！？「」\s]", "", narr)
    got = re.sub(r"[、。！？「」\s]", "", heard)
    if len(got) > len(base) * 1.25 + 4:
        out.append(f"台本より長い(余計な音?) {len(got)}字/{len(base)}字")
    return [f"{p}:{heard}" for p in out]


# ---- 笑い声・余計な音の自動チェック(2026-11-25 追加。笑い声は今後一切入れない)----
# 1万歩の回で、最後の言葉のあとに笑い声(「フッ」など)が入ったのに気づけなかった。
# 文字起こしには出ないことが多いので、「最後の言葉が終わったあとに大きな音があるか」で見つける。
TAIL_RMS = 0.08   # 最後の言葉のあとの音の強さがこれを超えたら余計な音(ふつうの話し声は 0.15 前後、消え際は 0.05 未満)


def extra_sound(audio, rate):
    """最後の言葉のあとに笑い声などの音があれば、その秒数と強さを返す。なければ None。"""
    m = _load()
    if not m:
        return None
    import numpy as np
    import scipy.signal as ss
    a16 = ss.resample_poly(audio, 16000, rate) if rate != 16000 else audio
    segs, _ = m.transcribe(a16, language="ja", beam_size=5, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    if not words:
        return None
    fr = int(0.05 * rate)
    rms = np.sqrt(np.convolve(audio ** 2, np.ones(fr) / fr, "same"))
    t = np.arange(len(audio)) / rate
    tail = rms[t > words[-1].end + 0.15]
    if len(tail) and tail.max() > TAIL_RMS:
        return float(t[t > words[-1].end + 0.15][tail.argmax()]), float(tail.max())
    return None
