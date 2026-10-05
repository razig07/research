#!/bin/bash
set -x
cd /home/user/research/video
(python3 -m pip install -q kokoro-onnx soundfile faster-whisper 2>&1 || python3 -m pip install -q --break-system-packages kokoro-onnx soundfile faster-whisper 2>&1) | tail -3
npm init -y >/dev/null 2>&1; npm i -s --no-audit --no-fund hyperframes gsap roughjs lucide-static @fontsource/caveat @fontsource/inter 2>&1 | tail -3
cd .models
for f in kokoro-v1.0.onnx voices-v1.0.bin; do [ -s $f ] || curl -sSL -o $f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f || curl -sSL -o $f https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/$f; done
ls -la
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8', download_root='/home/user/research/video/.models/whisper'); print('whisper ok')"
python3 -c "import kokoro_onnx, soundfile; print('kokoro ok', kokoro_onnx.__version__ if hasattr(kokoro_onnx,'__version__') else '')"
cd .. && npx hyperframes --version 2>&1 | tail -1
echo SETUP_DONE
