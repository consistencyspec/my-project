"""日本語のナレーションを Kokoro（Apache-2.0）で作る。

使い方: python say_ja.py <声の名前> <出力.wav> <文章>
声の名前: jf_alpha / jf_gongitsune / jf_nezumi / jf_tebukuro（女性）, jm_kumo（男性）
"""
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

voice, out, text = sys.argv[1], sys.argv[2], sys.argv[3]
pipe = KPipeline(lang_code="j")
chunks = [audio.numpy() if hasattr(audio, "numpy") else audio for _, _, audio in pipe(text, voice=voice)]
sf.write(out, np.concatenate(chunks), 24000)
print(out)
