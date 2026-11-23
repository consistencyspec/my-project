#!/usr/bin/env bash
# 新常識クロニクル：新しいクラウドセッションで動画を作る準備(日本語フォント・Python の部品)
#   bash youtube-gyakuten/scripts/setup.sh
set -e
cd "$(dirname "$0")/.."

# 日本語フォント(Noto CJK)と ffmpeg
if ! fc-list | grep -q "Noto Sans CJK"; then
  (apt-get install -y -q fonts-noto-cjk fonts-noto-cjk-extra ffmpeg >/dev/null 2>&1) || \
  (apt-get update -q >/dev/null 2>&1 && apt-get install -y -q fonts-noto-cjk fonts-noto-cjk-extra ffmpeg >/dev/null)
fi

# Python の部品(MiniMax で声を作るなら、これだけでよい)
PY=$(command -v python3.12 || command -v python3)
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

# 無料の Kokoro の声も使う場合だけ(重い):  KOKORO=1 bash scripts/setup.sh
if [ "${KOKORO:-0}" = "1" ]; then
  .venv/bin/pip install -q --index-url https://download.pytorch.org/whl/cpu torch
  .venv/bin/pip install -q "kokoro>=0.9" "misaki[ja]"
  .venv/bin/python -m unidic download
fi

.venv/bin/python -c "import PIL, soundfile, numpy; print('準備OK')"
