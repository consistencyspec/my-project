"""よく当たる売り場は本当？(ホットハンド編):ナレーションの声を作る。

台本 content/hothand_story.md の表から場面ごとのナレーションを読み、MiniMax で声を作る(作った声は保存して使い回す)。
Whisper で聞き取って、読み間違い・余計な音(笑い声など)を見つけたら作り直す。

  .venv/bin/python scripts/hothand_voice.py            # 声を作って、つないだ音声と台本の時間を更新
  .venv/bin/python scripts/hothand_voice.py --fresh 12 # 12番目の場面だけ作り直す(読み間違いの指摘があったとき)
できるもの:output/hothand_war/hothand_narration.mp3(全編)/output/hothand_war/voice_scenes/NN_場面.wav
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narrate  # noqa: E402
import voice_check  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "..", "content", "hothand_story.md")
OUT = os.path.join(HERE, "..", "output", "hothand_war")
CACHE = os.path.join(OUT, "voice")
SCENES = os.path.join(OUT, "voice_scenes")
LEAD, TAIL = 0.35, 0.55

narrate.NUM_STYLE = "dict"
narrate.ICHINICHI_PAUSE = 0.03
narrate.PAUSE_SHORT = 0
narrate.PAUSE_QUOTE_HA = 0
# この回の語(他の回の声のキャッシュを変えないよう、この回だけで足す)
narrate.MM_DICT += [
    "年末ジャンボ/ねんまつジャンボ", "銀座/ぎんざ", "何時間/なんじかん", "行列/ぎょうれつ", "売り場/うりば", "評判/ひょうばん",
    "流れ派/ながれは", "確率派/かくりつは", "勝つのか/かつのか", "数学/すうがく", "何万件/なんまんけん",
    "経済学者/けいざいがくしゃ", "テキサス州/テキサスしゅう", "宝くじ/たからくじ", "高額/こうがく", "翌週/よくしゅう",
    "40週間/よんじゅっしゅうかん", "1枚/いちまい", "1等/いっとう", "2,000万枚/にせんまんまい", "2000万枚/にせんまんまい",
    "1本/いっぽん", "結論/けつろん", "数字/すうじ", "前の週/まえのしゅう", "電光板/でんこうばん", "録画/ろくが",
    "2万4千回/にまんよんせんかい", "仕掛け/しかけ", "心理学者/しんりがくしゃ", "3本/さんぼん", "錯覚/さっかく",
    "千回以上/せんかいいじょう", "30年間/さんじゅうねんかん", "落とし穴/おとしあな", "4回/よんかい", "3回分/さんかいぶん",
    "3回/さんかい", "13ポイント/じゅうさんポイント", "1〜2ポイント/いちからにポイント", "筆頭著者/ひっとうちょしゃ",
    "1部リーグ/いちぶリーグ", "大リーグ/だいリーグ", "打席/だせき", "膨大/ぼうだい", "投資信託/とうししんたく",
    "過去1年/かこいちねん", "30年分/さんじゅうねんぶん", "手数料/てすうりょう", "連勝中/れんしょうちゅう", "胴元/どうもと",
    "再逆転/さいぎゃくてん", "番外編/ばんがいへん", "NBAジャム/エヌビーエージャム", "NBA/エヌビーエー", "上手/じょうず",
    "一番/いちばん", "判定/はんてい", "大国/たいこく", "真相/しんそう", "並び/ならび", "割合/わりあい",
]
narrate.TEXT_READ += [("表", "おもて")]   # この回の「表」はすべてコインの「おもて」


def scenes():
    rows = []
    for line in open(MD, encoding="utf-8"):
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) == 4 and re.fullmatch(r"\d+:\d\d", cols[0]):
            rows.append((cols[1], cols[3]))
    return rows


def voice(narr, fresh=False):
    narrate.MM_EMOTION = "calm" if "逆転" in narr else None
    tone = "/".join(narrate.mm_tone(narr))
    key = hashlib.md5(f"{narrate.voice_key()}|{narrate.mm_text(narr)}|{tone}".encode()).hexdigest()[:12]
    path = os.path.join(CACHE, f"{key}.wav")
    if fresh or not os.path.exists(path):
        sf.write(path, narrate.synth(narr), narrate.RATE)
    a, _ = sf.read(path, dtype="float32")
    return np.asarray(a), path


def main():
    os.makedirs(CACHE, exist_ok=True)
    shutil.rmtree(SCENES, ignore_errors=True)
    os.makedirs(SCENES)
    fresh = {int(sys.argv[sys.argv.index("--fresh") + 1])} if "--fresh" in sys.argv else set()
    rows = scenes()
    parts, times, t, warn = [], [], 0.0, []
    for i, (name, narr) in enumerate(rows, 1):
        a, path = voice(narr, fresh=i in fresh)
        for n in range(3):   # 聞き取りチェック(読み間違い・余計な音)
            probs = voice_check.problems(narr, a, narrate.RATE)
            extra = voice_check.extra_sound(a, narrate.RATE)
            if extra:
                probs.append(f"最後に余計な音({extra[0]:.1f}秒)")
            if not probs:
                break
            print(f"  ! {i:02d} {name}: {probs[0][:80]} → 作り直し {n + 1}/3", flush=True)
            a, path = voice(narr, fresh=True)
        else:
            warn.append(f"{i:02d} {name}")
        sec = LEAD + len(a) / narrate.RATE + TAIL
        seg = np.zeros(int(round(sec * narrate.RATE)), dtype="float32")
        seg[int(LEAD * narrate.RATE): int(LEAD * narrate.RATE) + len(a)] = a
        parts.append(seg)
        times.append(t)
        t += sec
        sf.write(os.path.join(SCENES, f"{i:02d}_{re.sub(r'[^0-9A-Za-zぁ-んァ-ヶ一-龠ー]', '', name)}.wav"), a, narrate.RATE)
        print(f"声 {i:2d}/{len(rows)} {len(a) / narrate.RATE:5.1f}秒 {name}", flush=True)
    wav = os.path.join(OUT, "narration.wav")
    sf.write(wav, np.concatenate(parts), narrate.RATE)
    mp3 = os.path.join(OUT, "hothand_narration.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-b:a", "192k", mp3], check=True)
    # 台本の時間を、合成した声の長さで更新
    md = open(MD, encoding="utf-8").read().split("\n")
    k = 0
    for j, line in enumerate(md):
        cols = line.strip().strip("|").split("|")
        if len(cols) == 4 and re.fullmatch(r"\s*\d+:\d\d\s*", cols[0]):
            md[j] = f"| {int(times[k] // 60)}:{int(times[k] % 60):02d} |" + "|".join(cols[1:]) + "|"
            k += 1
    s = "\n".join(md)
    s = re.sub(r"合計：約\d+分\d+秒", f"合計：約{int(t // 60)}分{int(t % 60):02d}秒", s)
    s = re.sub(r"ナレーション合計：約[\d,]+字\([^)]*\)", f"ナレーション合計：約{sum(len(n) for _, n in rows):,}字(時間は合成した声の長さ。場面の前に{LEAD}秒・後に{TAIL}秒の間)", s)
    open(MD, "w", encoding="utf-8").write(s)
    print(f"音声: {mp3}({int(t // 60)}分{int(t % 60):02d}秒)")
    if warn:
        print("!! 聞き取りチェックが通らなかった場面(耳で確認):", ", ".join(warn))


if __name__ == "__main__":
    sys.exit(main())
