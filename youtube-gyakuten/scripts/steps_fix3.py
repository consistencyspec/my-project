"""1万歩の回 3回目の指摘(2026-11-25):声の修正だけ作る。

- 場面9(1:56)「2007年」が「とし」と読まれた → 書き方を変えて3本(A=ひらがな、B=数字+読み方辞書、C=カタカナに間)
- 場面19(4:03)最後に笑い声 → 同じ文章で作り直し、笑い声のない3本
- 場面21(4:28)「7万8千人」の人が「ニン」にならない → 書き方を変えて3本(A=ひらがな、B=数字+読み方辞書、C=漢数字+カタカナのニン)
どの声も voice_check.extra_sound() で「最後の言葉のあとの音(笑い声など)」を調べ、あるものは捨てて作り直す。
  .venv/bin/python scripts/steps_fix3.py   -> output/steps_story/fix3/*.mp3 と fix3.zip
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import steps_story as ss  # noqa: E402
import voice_check  # noqa: E402
import soundfile as sf  # noqa: E402
from narrate import RATE  # noqa: E402

OUT = os.path.join(ss.OUT, "fix3")
os.makedirs(OUT, exist_ok=True)
plan = ss.build_plan()
cache = os.path.join(ss.OUT, "voice")
fix_cache = os.path.join(OUT, "_cache")


def variants(i):
    t = ss.voice_text(plan[i][3][2])
    if i == 9:
        return {"A": t.replace("ニセンナナネンには", "にせんななねんには"),
                "B": t.replace("ニセンナナネンには", "2007年には"),
                "C": t.replace("ニセンナナネンには", "ニセンナナ、ネンには")}
    if i == 21:
        return {"A": t.replace(f"約{ss.YAKU_GAP}ナナマンハッセンニン", "約ななまんはっせんにん"),
                "B": t.replace(f"約{ss.YAKU_GAP}ナナマンハッセンニン", f"約{ss.YAKU_GAP}7万8千人"),
                "C": t.replace(f"約{ss.YAKU_GAP}ナナマンハッセンニン", f"約{ss.YAKU_GAP}七万八千ニン")}
    return {c: t for c in "ABC"}


for i in (9, 19, 21):
    for c, text in variants(i).items():
        for k in range(6):
            v = ss._voice_for(i, text, fix_cache, fresh=True)
            bad = voice_check.extra_sound(v, RATE)
            heard = voice_check.transcribe(v, RATE)
            if bad is None and len(heard.replace(" ", "")) <= len(plan[i][3][2]) + 10:
                break
            print(f"  ! 場面{i}{c} 作り直し(最後の言葉のあとの音 {bad})", flush=True)
        else:
            raise SystemExit(f"場面{i}{c}: 余計な音のない声が作れなかった")
        wav = os.path.join(OUT, f"{i:02d}_{c}.wav")
        sf.write(wav, v, RATE)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k", wav[:-4] + ".mp3"], check=True)
        print(f"[{i:02d}{c}] {len(v) / RATE:.1f}秒 {heard}", flush=True)
shutil.rmtree(fix_cache, ignore_errors=True)
