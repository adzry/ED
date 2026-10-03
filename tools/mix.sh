#!/usr/bin/env bash
# Synthesize a quiet ambient pad, duck it under the narration, and mux with the rendered picture.
set -euo pipefail
cd "$(dirname "$0")/.."
DUR=$(python3 -c "import json;print(json.load(open('build/timeline.json'))['duration'])")
OUT=out/ed-pharmacy-visibility.mp4

# Two soft chords (A minor → F major) cross-fading every 16 s, with a slow breathing swell.
A="sin(2*PI*110*t)+0.7*sin(2*PI*164.81*t)+0.5*sin(2*PI*220*t)+0.35*sin(2*PI*261.63*t)+0.2*sin(2*PI*329.63*t)"
B="sin(2*PI*87.31*t)+0.7*sin(2*PI*130.81*t)+0.5*sin(2*PI*174.61*t)+0.35*sin(2*PI*220*t)+0.2*sin(2*PI*329.63*t)"
W="(0.5+0.5*cos(2*PI*t/16))"
PAD="0.05*(${W}*(${A})+(1-${W})*(${B}))*(0.85+0.15*sin(2*PI*t/7))"

ffmpeg -y -loglevel error \
  -f lavfi -i "aevalsrc=exprs='${PAD}':s=44100:d=${DUR}" \
  -i build/narration.wav \
  -i build/video.mp4 \
  -filter_complex "
    [0:a]lowpass=f=900,aecho=0.8:0.6:90|170:0.25|0.15,afade=t=in:d=2.5,afade=t=out:st=$(python3 -c "print(${DUR}-3.5)"):d=3.5,aformat=channel_layouts=stereo[music];
    [1:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=70,asplit=2[voice][key];
    [music][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=700:makeup=1[ducked];
    [voice][ducked]amix=inputs=2:weights='1 1.0':normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]" \
  -map 2:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
echo "mixed → $OUT"
