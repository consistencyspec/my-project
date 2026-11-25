"""1万歩の回:候補の声(output/steps_story/candidates/NN_A.wav など)から使う声を選んで入れる。

  .venv/bin/python scripts/steps_pick_voice.py 11=C 17=B   # 場面11はC、場面17はBを使う(そのあと steps_story.py で書き出す)
"""
import sys, os, shutil
sys.path.insert(0, 'scripts')
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'steps_regen_voices.py')).read().split("MISREAD =")[0])
PICK = dict(a.split("=") for a in sys.argv[1:])
for i, c in PICK.items():
    i = int(i)
    shutil.copy(os.path.join(cand, f"{i:02d}_{c}.wav"), path_for(plan[i][3][2]))
    print("使う声:", i, c)
