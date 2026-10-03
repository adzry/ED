#!/usr/bin/env python3
"""Validate the final MP4 against the timeline: format, duration, audio, loudness, captions sidecar."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "ed-pharmacy-visibility.mp4"


def main():
    tl = json.loads((ROOT / "build/timeline.json").read_text())
    problems = []
    if not OUT.exists():
        print(f"output: missing {OUT}")
        return 1
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(OUT)],
                                      capture_output=True, text=True, check=True).stdout)
    v = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
    if not v or (v["width"], v["height"]) != (tl["width"], tl["height"]):
        problems.append("video stream missing or wrong size")
    elif eval(v["r_frame_rate"]) != tl["fps"]:
        problems.append(f"frame rate {v['r_frame_rate']} != {tl['fps']}")
    if not a:
        problems.append("audio stream missing")
    dur = float(probe["format"]["duration"])
    size_mb = OUT.stat().st_size / 1e6
    if size_mb > 95:
        problems.append(f"file is {size_mb:.0f} MB; GitHub rejects files over 100 MB")
    if abs(dur - tl["duration"]) > 0.25:
        problems.append(f"duration {dur:.2f}s differs from timeline {tl['duration']:.2f}s")
    if not 60 <= dur <= 95:
        problems.append(f"duration {dur:.1f}s outside the ~60–90 s target")

    ebur = subprocess.run(["ffmpeg", "-nostats", "-i", str(OUT), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = re.search(r"Integrated loudness:\s+I:\s+(-?[\d.]+) LUFS", ebur)
    lufs = float(m.group(1)) if m else None
    if lufs is None or not -18.5 <= lufs <= -13.5:
        problems.append(f"integrated loudness {lufs} LUFS outside -16 ± 2.5")

    srt = (ROOT / "out/captions.srt").read_text(encoding="utf-8")
    n_caps = sum(len(l["captions"]) for s in tl["scenes"] for l in s["lines"])
    if srt.count(" --> ") != n_caps:
        problems.append("captions.srt cue count does not match timeline")

    for p in problems:
        print(p)
    print(f"output: {'OK' if not problems else f'{len(problems)} problem(s)'} "
          f"({dur:.2f}s, {v and v['width']}x{v and v['height']} @ {v and v['r_frame_rate']}, {lufs} LUFS)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
