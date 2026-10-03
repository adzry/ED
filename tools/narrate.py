#!/usr/bin/env python3
"""Synthesize narration with Piper and derive the video timeline from it.

Reads script/storyboard.json and writes:
  build/audio/<scene>_<n>.wav   one clip per narration line
  build/narration.wav          the full voice track, placed on the timeline
  build/timeline.json          scene / line / caption timings used by render + validation
  out/captions.srt             sidecar captions
"""
import array
import json
import re
import sys
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MODEL = ROOT / "models" / "en-us-lessac-medium.onnx"
MAX_CAPTION_CHARS = 58
SPEECH = SynthesisConfig(length_scale=0.9)


def speakable(text, pronunciation):
    s = text.replace(" & ", " and ").replace("(Admission)", ", Admission")
    s = s.replace("—", ",").replace(":", ",")
    for word, say in pronunciation.items():
        s = re.sub(rf"\b{re.escape(word)}\b", say, s)
    s = re.sub(r",\s*,", ",", re.sub(r"\s+,", ",", s))
    return s.rstrip(" ,")


def chunk_caption(text, keep_together=()):
    """Split a line into balanced caption chunks of at most MAX_CAPTION_CHARS,
    never breaking inside a highlighted term."""
    glued = text
    for term in sorted(keep_together, key=len, reverse=True):
        glued = re.sub(re.escape(term), lambda m: m.group(0).replace(" ", "\u00a0"), glued)
    words = glued.split(" ")
    n = max(1, -(-len(text) // MAX_CAPTION_CHARS))
    while True:
        target = len(text) / n
        chunks, cur = [], ""
        for w in words:
            cand = (cur + " " + w).strip()
            if cur and len(cand) > target + 6 and len(chunks) < n - 1:
                chunks.append(cur)
                cur = w
            else:
                cur = cand
        chunks.append(cur)
        chunks = [c.replace("\u00a0", " ") for c in chunks]
        if all(len(c) <= MAX_CAPTION_CHARS for c in chunks):
            return chunks
        n += 1


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    board = json.loads((ROOT / "script" / "storyboard.json").read_text())
    voice = PiperVoice.load(str(MODEL))
    rate = voice.config.sample_rate
    (BUILD / "audio").mkdir(parents=True, exist_ok=True)
    (ROOT / "out").mkdir(exist_ok=True)

    tm = board["timing"]
    t = 0.0
    scenes, track = [], []
    for scene in board["scenes"]:
        start = t
        cursor = start + tm["leadIn"]
        lines = []
        for i, line in enumerate(scene["lines"]):
            spoken = speakable(line.get("speak", line["text"]), board["pronunciation"])
            path = BUILD / "audio" / f"{scene['id']}_{i}.wav"
            with wave.open(str(path), "wb") as wav:
                voice.synthesize_wav(spoken, wav, syn_config=SPEECH)
            with wave.open(str(path), "rb") as wav:
                samples = array.array("h", wav.readframes(wav.getnframes()))
            dur = len(samples) / rate
            track.append((cursor, samples))

            chunks = chunk_caption(line["text"], board["highlight"])
            total = sum(len(c) for c in chunks)
            c_t, caps = cursor, []
            for c in chunks:
                c_d = dur * len(c) / total
                caps.append({"text": c, "start": round(c_t, 3), "end": round(c_t + c_d, 3)})
                c_t += c_d
            lines.append({"text": line["text"], "spoken": spoken, "start": round(cursor, 3),
                          "end": round(cursor + dur, 3), "captions": caps})
            cursor += dur + tm["gap"]
        end = max(cursor - tm["gap"] + tm["tail"], start + scene["minDuration"])
        scenes.append({"id": scene["id"], "name": scene["name"], "start": round(start, 3),
                       "end": round(end, 3), "lines": lines})
        t = end

    duration = round(t, 3)
    pcm = array.array("h", bytes(int(duration * rate + rate) * 2))
    for at, samples in track:
        o = int(at * rate)
        pcm[o:o + len(samples)] = samples
    with wave.open(str(BUILD / "narration.wav"), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())

    timeline = {"fps": board["fps"], "width": board["width"], "height": board["height"],
                "duration": duration, "highlight": board["highlight"], "scenes": scenes}
    (BUILD / "timeline.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))

    n, srt = 0, []
    for s in scenes:
        for line in s["lines"]:
            for c in line["captions"]:
                n += 1
                srt.append(f"{n}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n")
    (ROOT / "out" / "captions.srt").write_text("\n".join(srt), encoding="utf-8")

    for s in scenes:
        print(f"{s['id']:>3} {s['start']:6.2f}–{s['end']:6.2f}  {s['name']}")
    print(f"total {duration:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
