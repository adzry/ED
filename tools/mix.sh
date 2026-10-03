#!/usr/bin/env bash
# Mix narration over the synthesized underscore (tools/music.py), duck the music under the voice,
# normalize loudness, and mux with the rendered picture.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=out/ed-pharmacy-visibility.mp4
python3 tools/music.py

ffmpeg -y -loglevel error \
  -i build/music.wav \
  -i build/narration.wav \
  -filter_complex "
    [0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.19[music];
    [1:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=0.1:ratio=2.5:attack=5:release=120,asplit=2[voice][key];
    [music][key]sidechaincompress=threshold=0.025:ratio=5:attack=50:release=700[ducked];
    [voice][ducked]amix=inputs=2:weights='1 1':normalize=0[aout]" \
  -map "[aout]" -c:a pcm_s16le build/mix.wav

# Linear (not dynamic) loudness normalization to -16 LUFS, so the music's level relative to the voice is kept.
LUFS=$(ffmpeg -nostats -i build/mix.wav -af ebur128 -f null - 2>&1 | sed -n 's/.*I: *\(-\?[0-9.]*\) LUFS.*/\1/p' | tail -1)
GAIN=$(python3 -c "print(-16 - (${LUFS}))")
ffmpeg -y -loglevel error -i build/video.mp4 -i build/mix.wav \
  -map 0:v -map 1:a -c:v copy -af "volume=${GAIN}dB,alimiter=limit=0.89" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
echo "mixed → $OUT"
