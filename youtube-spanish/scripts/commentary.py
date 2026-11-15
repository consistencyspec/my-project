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

スライドごとに別々に録音する書き方（秒数を数えなくてよいので、こちらがおすすめ）:
    "commentary": {
        "slides": [
            {"audio": "commentary/ep01_1.m4a", "title": "この回のポイント", "points": ["..."]},
            {"audio": "commentary/ep01_2.m4a", "title": "このセリフ", "play": true,
             "points": [{"es": "Estoy buscando un piso que esté cerca del centro.", "ja": "..."}]}
        ]
    }

"play": true のスライドでは、表示したとたんに、points のスペイン語を合成音声で読み上げてから、あなたの録音を流す。
スペイン語を自分で読まなくてよい。
"""
import json
import subprocess
import wave
from pathlib import Path

AFTER_KEYS = ("listen1", "line", "phrases", "listen2", "shadow", "listen3")
DEFAULT_AFTER = "line"
SECTION = ("commentary", "解説　この回のポイント", "ポイントを日本語で解説します")


def per_slide(conf):
    """スライドごとに別々の録音ファイルを使う書き方かどうか。"""
    slides = conf.get("slides", [])
    return bool(slides) and all(sl.get("audio") for sl in slides)


def validate(conf):
    if not isinstance(conf, dict):
        raise ValueError("commentary の書き方が正しくありません")
    slides = conf.get("slides", [])
    if not conf.get("audio") and not per_slide(conf):
        raise ValueError("commentary には audio（録音ファイル）か、すべてのスライドに audio が必要です")
    if conf.get("audio") and any(sl.get("audio") for sl in slides):
        raise ValueError("録音は「全体で1つ」か「スライドごと」のどちらかにしてください")
    for i, sl in enumerate(slides, 1):
        if sl.get("play") and not any(isinstance(pt, dict) and pt.get("es") for pt in sl.get("points", [])):
            raise ValueError(f"解説のスライド{i}は play: true ですが、読み上げるスペイン語（es）がありません")
    if conf.get("after", DEFAULT_AFTER) not in AFTER_KEYS:
        raise ValueError(f"commentary の after は {', '.join(AFTER_KEYS)} のどれかにしてください")
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


def prepare_audio(src, dst, rate, trim_start=False):
    """録音を動画用にそろえる：最後の無音を切り、音量を一定にし、合成音声と同じ形式（モノラル・16bit）にする。

    頭の無音は切らない（スライドの切り替え秒数 at を、録音を聞いたときの秒数のまま使えるように）。
    """
    trim = "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    if trim_start:  # スライドごとの録音なら、頭の無音も切ってよい（秒数を使わないので）
        trim = "silenceremove=start_periods=1:start_threshold=-45dB," + trim
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
           "-af", f"{trim},loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "1", "-ar", str(rate),
           "-sample_fmt", "s16", str(dst)]
    subprocess.run(cmd, check=True)
    return Path(dst)


def spanish_to_play(slide):
    """play: true のスライドで読み上げるスペイン語の一覧。"""
    if not slide.get("play"):
        return []
    return [pt["es"] for pt in slide.get("points", []) if isinstance(pt, dict) and pt.get("es")]


def load_parts(conf, root, work, rate, fallback_slide):
    """録音を動画用にそろえ、(スライド, 録音) の組を返す。録音が足りなければ空（解説なし）。"""
    slides = conf.get("slides", [])
    if per_slide(conf):
        parts = []
        for i, sl in enumerate(slides):
            src = find_audio(sl, root)
            if src is None:
                return []
            parts.append(prepare_audio(src, Path(work) / f"commentary_{i:02d}.wav", rate, trim_start=True))
        return list(zip(slides, parts))
    src = find_audio(conf, root)
    if src is None:
        return []
    talk = prepare_audio(src, Path(work) / "commentary.wav", rate)
    starts = slide_times(slides, wav_seconds(talk))
    return list(zip(slides or [fallback_slide], split_wav(talk, starts, work)))


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
    """録音するときの原稿の下書き（Markdown）。スライドごとに1つずつ録音する形で、話すのは日本語だけ。"""
    ph = ep.get("phrases", [])
    eid = ep["id"]
    lines = [
        f"# 解説の原稿の下書き: {eid} {ep['title_ja']}",
        "",
        "- 話すのは日本語だけです。♪の所は、スペイン語を合成音声が読み上げます",
        f"- 録音①②③…を、スマホのボイスメモで1つずつ録り、`commentary/{eid}_1.m4a` のような名前で置きます",
        "- 全部で1〜2分が目安。読み上げるより、自分の言葉で話すほうが自然になります",
        "",
        "## 録音①（この回のポイント）",
        "",
        f"今回は「{ep['title_ja']}」の会話でした。ここまで聞いてみて、どうでしたか？",
        f"今回のポイントは、{ep['grammar']}。もう一度聞いてみましょう。",
        "",
    ]
    slides = [{"audio": f"commentary/{eid}_1.m4a", "title": "この回のポイント", "points": [ep["grammar"]]}]
    for n, p in enumerate(ph[:2], 2):
        lines += [f"## 録音{'①②③④⑤'[n - 1]}（♪{p['es']}）", "",
                  f"「{p['ja']}」という意味です。"]
        if p.get("note"):
            lines.append(f"（説明の材料：{p['note']}）")
        lines += ["次の表現も聞いてみましょう。" if n == 2 else "", ""]
        slides.append({"audio": f"commentary/{eid}_{n}.m4a", "title": "このフレーズ", "play": True,
                       "points": [{"es": p["es"], "ja": p["ja"]}]})
    last = len(slides) + 1
    lines += [f"## 録音{'①②③④⑤'[last - 1]}（自分のひとこと）", "",
              "【実際に使った場面、覚え方のコツ、スペインでの体験など。ここがあなたにしか話せない部分です】",
              "では、続きを聞いてみましょう。", ""]
    slides.append({"audio": f"commentary/{eid}_{last}.m4a", "title": "ひとこと", "points": []})
    body = ",\n".join("    " + json.dumps(sl, ensure_ascii=False) for sl in slides)
    lines += ["## 台本に足す設定", "", "```json", '"commentary": {', '  "slides": [', body, "  ]", "}", "```", ""]
    return "\n".join(lines)
