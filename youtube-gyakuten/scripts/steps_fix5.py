"""1万歩の回 5回目の指摘(2026-11-28):1:54「2007年」の年がまだ「ねん」に聞こえない → 声だけ3本作る。

A = 数字のまま送り、読み方辞書で「2007年/にせんななねん」(卵・赤ワインの回で年号を直したやり方)
B = 数字+辞書で、「には」を「に」にして年と助詞を離す(声だけ。字幕は変えない)
C = 漢字「二千七年」+辞書「二千七年/にせんななねん」
どれも voice_check.extra_sound() で笑い声などを調べ、あるものは捨てる。
  .venv/bin/python scripts/steps_fix5.py   -> output/steps_story/fix5/09_A〜C.mp3 と voice_fix5.zip
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

OUT = os.path.join(ss.OUT, "fix5")
os.makedirs(OUT, exist_ok=True)
plan = ss.build_plan()
narr = plan[9][3][2]
base = ss.voice_text(narr)   # 「にせんななねんには、…」
ss.SCENE_TONE["2007年に"] = ["2007年/にせんななねん"]
ss.SCENE_TONE["二千七年には"] = ["二千七年/にせんななねん"]
VARIANTS = {"A": base.replace("にせんななねんには", "2007年には"),
            "B": base.replace("にせんななねんには", "2007年に"),
            "C": base.replace("にせんななねんには", "二千七年には")}
tmp = os.path.join(OUT, "_cache")
for c, text in VARIANTS.items():
    for k in range(6):
        v = ss._voice_for(9, text, tmp, fresh=True)
        if voice_check.extra_sound(v, RATE) is None:
            break
        print(f"  ! 09{c} 余計な音 → 作り直し", flush=True)
    else:
        raise SystemExit(f"09{c}: 余計な音のない声が作れなかった")
    wav = os.path.join(OUT, f"09_{c}.wav")
    sf.write(wav, v, RATE)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k", wav[:-4] + ".mp3"], check=True)
    print(f"[09{c}] {len(v) / RATE:.1f}秒 {voice_check.transcribe(v, RATE)}", flush=True)
shutil.rmtree(tmp, ignore_errors=True)
