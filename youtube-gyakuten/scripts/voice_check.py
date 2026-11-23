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
