"""自分の声の「解説」を動画に差し込む。

スマホのボイスメモなどで録音した音声（m4a / mp3 / wav など）を、動画の途中に「解説」として入れる。
録音に合わせて、話している内容のスライド（見出しと箇条書き）を切り替えて表示する。

台本（JSON）の書き方:
    "commentary": {
        "audio": "commentary/ep01.m4a",   ← 録音ファイル（youtube-spanish/ からの場所）
        "after": "line",                  ← どの区切りの後に入れるか（省略時は「2回目 1文ずつ」の後）
        "slides": [                        ← 録音に合わせて出すスライド（省略可）
            {"at": 0,  "title": "この回のポイント", "points": ["接続法は「まだ見つかっていない物」に使う"]},
            {"at": 35, "title": "例文で確認", "points": [{"es": "Busco un piso que esté cerca.", "ja": "近くにある部屋を探しています"}]}
        ]
    }

"at" はスライドを切り替える秒数（録音の頭から数えて）。省略すると、録音の長さで均等に切り替える。
録音ファイルがまだないときは、警告を出して解説なしで動画を作る。
"""
import subprocess
import wave
from pathlib import Path

AFTER_KEYS = ("listen1", "line", "phrases", "listen2", "shadow", "listen3")
DEFAULT_AFTER = "line"
SECTION = ("commentary", "解説　この回のポイント", "ポイントを日本語で解説します")


def validate(conf):
    if not isinstance(conf, dict) or not conf.get("audio"):
        raise ValueError("commentary には audio（録音ファイルの場所）が必要です")
    if conf.get("after", DEFAULT_AFTER) not in AFTER_KEYS:
        raise ValueError(f"commentary の after は {', '.join(AFTER_KEYS)} のどれかにしてください")
    slides = conf.get("slides", [])
    last = -1.0
    for i, sl in enumerate(slides, 1):
        if not sl.get("title"):
            raise ValueError(f"解説のスライド{i}に title がありません")
        for pt in sl.get("points", []):
            if isinstance(pt, dict) and not (pt.get("es") or pt.get("ja")):
                raise ValueError(f"解説のスライド{i}の points に es か ja が必要です")
        if "at" in sl:
            if sl["at"] <= last:
                raise ValueError("解説のスライドの at（秒）は、小さい順に並べてください")
            last = sl["at"]
    if slides and any("at" in s for s in slides) and not all("at" in s for s in slides):
        raise ValueError("解説のスライドの at は、全部に書くか、全部省略してください")


def find_audio(conf, root):
    """録音ファイルの場所。見つからなければ None（警告を出して解説なしで続ける）。"""
    path = Path(root) / conf["audio"]
    if not path.exists():
        print(f"注意: 解説の録音ファイルが見つからないので、解説なしで作ります: {path}")
        return None
    return path


def prepare_audio(src, dst, rate):
    """録音を動画用にそろえる：最後の無音を切り、音量を一定にし、合成音声と同じ形式（モノラル・16bit）にする。

    頭の無音は切らない（スライドの切り替え秒数 at を、録音を聞いたときの秒数のまま使えるように）。
    """
    trim = "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
           "-af", f"{trim},loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "1", "-ar", str(rate),
           "-sample_fmt", "s16", str(dst)]
    subprocess.run(cmd, check=True)
    return Path(dst)


def wav_seconds(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def slide_times(slides, total):
    """各スライドの開始秒。at がなければ均等に割る。最低1枚（空なら見出しだけの1枚）。"""
    if not slides:
        return [0.0]
    if all("at" in s for s in slides):
        times = [float(s["at"]) for s in slides]
        if times[0] > 0:
            times[0] = 0.0  # 最初のスライドは録音の頭から出す
        return [t for t in times if t < total] or [0.0]
    step = total / len(slides)
    return [i * step for i in range(len(slides))]


def split_wav(path, starts, out_dir):
    """録音を、スライドの切り替え位置で分ける。"""
    out_dir = Path(out_dir)
    with wave.open(str(path), "rb") as w:
        rate, n, params = w.getframerate(), w.getnframes(), w.getparams()
        data = w.readframes(n)
    width = params.sampwidth * params.nchannels
    bounds = [int(round(t * rate)) for t in starts] + [n]
    parts = []
    for i in range(len(starts)):
        a, b = bounds[i], max(bounds[i + 1], bounds[i])
        p = out_dir / f"commentary_{i:02d}.wav"
        with wave.open(str(p), "wb") as o:
            o.setparams(params)
            o.writeframes(data[a * width:b * width])
        parts.append(p)
    return parts


def script_template(ep):
    """録音するときの原稿の下書き（Markdown）。台本の内容から、話す順番と材料を並べる。"""
    ph = ep.get("phrases", [])
    lines = [
        f"# 解説の原稿の下書き: {ep['id']} {ep['title_ja']}",
        "",
        "目安は1〜2分。読み上げるより、自分の言葉で話すほうが自然になります。",
        "スマホのボイスメモで録音し、`youtube-spanish/commentary/` に置いて、台本に `commentary` を足してください。",
        "",
        "## 話す順番",
        "",
        f"1. **あいさつとテーマ**：今回は「{ep['title_ja']}」の会話です。",
        f"2. **この回のポイント**：{ep['grammar']}",
    ]
    if ph:
        lines.append(f"   - 例：{ph[0]['es']}（{ph[0]['ja']}）")
        if ph[0].get("note"):
            lines.append(f"   - 説明の材料：{ph[0]['note']}")
    if len(ph) > 1:
        lines.append("3. **間違えやすい所・使い分け**（1〜2個に絞る）")
        for p in ph[1:3]:
            lines.append(f"   - {p['es']}（{p['ja']}）" + (f"：{p['note']}" if p.get("note") else ""))
    lines += [
        "4. **自分のひとこと**：実際に使った場面、覚え方のコツ、スペインでの体験など（ここがあなたにしか話せない部分です）",
        "5. **しめ**：「では続きを聞いてみましょう」",
        "",
        "## 台本に足す例（秒数は録音を聞いて合わせる）",
        "",
        "```json",
        '"commentary": {',
        f'  "audio": "commentary/{ep["id"]}.m4a",',
        '  "slides": [',
        '    {"at": 0, "title": "この回のポイント", "points": ["' + ep["grammar"].replace('"', "'") + '"]},',
    ]
    if ph:
        lines.append('    {"at": 30, "title": "例文で確認", "points": [{"es": "'
                     + ph[0]["es"].replace('"', "'") + '", "ja": "' + ph[0]["ja"].replace('"', "'") + '"}]}')
    lines += ["  ]", "}", "```", ""]
    return "\n".join(lines)
