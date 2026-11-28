"""1万歩の回 4回目の指摘(2026-11-28):声を3本ずつ作り、選んだ声を動画用に入れる。

- 場面12(2:32)群馬県中之条町 → 「ぐんまけん、なかのじょうまち」(群馬県のあとに少しの間)
- 場面19(3:44・4:01)「必要派」の派を「は」と読ませる(その場面だけの読み方辞書)
どの声も voice_check.extra_sound() で笑い声などの余計な音を調べ、あるものは捨てる。
  .venv/bin/python scripts/steps_fix4.py            -> output/steps_story/fix4/*.mp3 と voice_fix4.zip(Aを動画用に入れる)
  .venv/bin/python scripts/steps_fix4.py 12=B 19=C  -> 選んだ声を動画用に入れ直す
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

OUT = os.path.join(ss.OUT, "fix4")
SCENES = {12: "群馬県中之条町", 19: "必要派の派"}
plan = ss.build_plan()
cache = os.path.join(ss.OUT, "voice")


def install(i, c):
    """選んだ候補を、動画を書き出すときに使う声の場所に入れる(voice_for と同じ鍵)。"""
    narr = plan[i][3][2]
    before = set(os.listdir(cache))
    ss.cs.voice_for(i, narr, cache)   # 鍵の場所を作る(なければ1本作られる)
    import hashlib, narrate  # noqa: E401
    t = ss.voice_text(narr)
    for x, y in ss.cs.VOICE_FIX:
        t = t.replace(x, y)
    narrate.MM_EMOTION = None
    key = hashlib.md5(f"{narrate.voice_key()}|{narrate.mm_text(t)}|{'/'.join(narrate.mm_tone(t))}".encode()).hexdigest()[:12]
    shutil.copy(os.path.join(OUT, f"{i:02d}_{c}.wav"), os.path.join(cache, f"{key}.wav"))
    print(f"動画用に入れた声: 場面{i} {c}")


if len(sys.argv) > 1:
    for a in sys.argv[1:]:
        i, c = a.split("=")
        install(int(i), c)
    sys.exit()

os.makedirs(OUT, exist_ok=True)
tmp = os.path.join(OUT, "_cache")
for i in SCENES:
    text = ss.voice_text(plan[i][3][2])
    for c in "ABC":
        for k in range(6):
            v = ss._voice_for(i, text, tmp, fresh=True)
            bad = voice_check.extra_sound(v, RATE)
            heard = voice_check.transcribe(v, RATE)
            if bad is None and len(heard.replace(" ", "")) <= len(plan[i][3][2]) + 10:
                break
            print(f"  ! 場面{i}{c} 作り直し(余計な音 {bad})", flush=True)
        else:
            raise SystemExit(f"場面{i}{c}: 余計な音のない声が作れなかった")
        wav = os.path.join(OUT, f"{i:02d}_{c}.wav")
        sf.write(wav, v, RATE)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k", wav[:-4] + ".mp3"], check=True)
        print(f"[{i:02d}{c} {SCENES[i]}] {len(v) / RATE:.1f}秒 {heard}", flush=True)
shutil.rmtree(tmp, ignore_errors=True)
