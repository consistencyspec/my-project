"""1万歩の回:  .venv/bin/python scripts/steps_regen_voices.py
指摘のあった場面は声を3本(A・B・C)、約の間だけ変わる場面は1本作り直し、文字起こしで確かめる。"""
import sys, os, shutil, hashlib, subprocess
sys.path.insert(0, 'scripts')
import steps_story as ss, coffee_story as cs, narrate, voice_check
import soundfile as sf
from narrate import RATE
plan = ss.build_plan()
cache = os.path.join(ss.OUT, 'voice')
cand = os.path.join(ss.OUT, 'candidates')
os.makedirs(cand, exist_ok=True)

def path_for(narr):
    t = ss.voice_text(narr)
    for x, y in cs.VOICE_FIX:
        t = t.replace(x, y)
    narrate.MM_EMOTION = None
    tone = "|" + "/".join(narrate.mm_tone(t))
    key = hashlib.md5(f"{narrate.voice_key()}|{narrate.mm_text(t)}{tone}".encode()).hexdigest()[:12]
    return os.path.join(cache, f"{key}.wav")

MISREAD = {0: "焦る", 11: "アオヤギユキトシ", 13: "十分", 17: "41%・約", 29: "1月", 33: "十分"}
YAKU = [9, 12, 16, 20, 21, 23, 26, 27]
for i in sorted(MISREAD):
    narr = plan[i][3][2]
    p = path_for(narr)
    for c in "ABC":
        v = cs.voice_for(i, narr, cache, fresh=True)
        assert os.path.exists(p), p
        out = os.path.join(cand, f"{i:02d}_{c}.wav")
        shutil.copy(p, out)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-b:a", "128k", out[:-4] + ".mp3"], check=True)
        print(f"[{i:02d}{c} {MISREAD[i]}] {len(v)/RATE:.1f}秒 {voice_check.transcribe(v, RATE)}", flush=True)
for i in YAKU:
    narr = plan[i][3][2]
    for k in range(3):
        v = cs.voice_for(i, narr, cache, fresh=k > 0)
        t = voice_check.transcribe(v, RATE)
        print(f"[{i:02d} 約 try{k}] {len(v)/RATE:.1f}秒 {t}", flush=True)
        if len(t.replace(' ', '')) <= len(narr) + 8:
            break
