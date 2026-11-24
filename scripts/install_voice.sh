#!/usr/bin/env bash
# M13 - builds whisper.cpp on the Pi and downloads the small multilingual model (about 75 MB).
# Takes roughly 10-20 minutes on a Pi 4. Needs internet. Speech recognition then runs fully on the Pi.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third_party models
if [ ! -d third_party/whisper.cpp ]; then
  git clone --depth 1 --branch v1.7.4 https://github.com/ggerganov/whisper.cpp third_party/whisper.cpp
fi
cmake -S third_party/whisper.cpp -B third_party/whisper.cpp/build -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_TESTS=OFF
cmake --build third_party/whisper.cpp/build -j2 --target whisper-cli
if [ ! -s models/ggml-tiny.bin ]; then
  curl -fL --retry 3 -o models/ggml-tiny.bin.part https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin
  mv models/ggml-tiny.bin.part models/ggml-tiny.bin
fi
ls -la third_party/whisper.cpp/build/bin/whisper-cli models/ggml-tiny.bin
echo "Voice parts installed. Next:  ./eve stage M13"
