#!/usr/bin/env python3
"""Synthesize a soft documentary underscore that follows build/timeline.json.

Warm pad + sub bass + felt-piano arpeggios over Am7 – Fmaj7 – C – G at 84 bpm, with a gentle lift
at the proposed solution (scene 4), soft whooshes on scene changes, and a resolving final chord.
Writes build/music.wav (44.1 kHz stereo). Everything is generated here: no third-party audio.
"""
import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 44100
BPM = 84
BAR = 60 / BPM * 4
rng = np.random.default_rng(7)

# (bass, pad voicing) as MIDI notes
CHORDS = [
    (45, [57, 60, 64, 67]),  # Am7
    (41, [53, 57, 60, 64]),  # Fmaj7
    (48, [55, 60, 64, 67]),  # C
    (43, [55, 59, 62, 67]),  # G
]
FINAL = (48, [55, 60, 64, 67, 72])  # C, held to the end


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1]:
        return
    sig = sig[: buf.shape[1] - i]
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    buf[0, i:i + len(sig)] += sig * gain * l
    buf[1, i:i + len(sig)] += sig * gain * r


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def pad_note(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * d * t + p) for d, p in ((1, 0), (1.0012, 1.3), (0.9988, 2.1)))
    s += 0.30 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    return s / 3.4 * env_adsr(len(t), 0.9, 1.4)


def piano_note(m, vel):
    t = np.arange(int(2.6 * SR)) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.25) \
        + 0.06 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.12)
    e = np.minimum(1, t / 0.006) * np.exp(-t / 0.7)
    return s * e * vel


def bass_note(m, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * hz(m) * t) + 0.15 * np.sin(2 * np.pi * 2 * hz(m) * t)
    return s * env_adsr(len(t), 0.25, 0.9) * (0.75 + 0.25 * np.exp(-t / 1.5))


def whoosh(dur=0.9, rising=True):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    # Swept one-pole low-pass: cutoff glides up (rising) for a soft "air" movement.
    cut = np.linspace(300, 3500, n) if rising else np.linspace(3500, 300, n)
    a = np.exp(-2 * np.pi * cut / SR)
    y, out = 0.0, np.empty(n)
    for i in range(n):
        y = (1 - a[i]) * noise[i] + a[i] * y
        out[i] = y
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    return out * shape / (np.abs(out).max() + 1e-9)


def reverb(x, seconds=2.6, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (seconds / 6.5))
    ir = np.convolve(ir, np.ones(12) / 12, mode="same")  # darken
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y / (np.abs(y).max() + 1e-9)


def main():
    tl = json.loads((ROOT / "build/timeline.json").read_text())
    total = tl["duration"]
    start = {s["id"]: s["start"] for s in tl["scenes"]}
    n = int((total + 0.5) * SR)
    pad, keys, bass, sfx = (np.zeros((2, n)) for _ in range(4))

    final_from = total - 5.0
    bars = int(np.ceil(final_from / BAR))
    for b in range(bars):
        t0 = b * BAR
        root, voicing = CHORDS[b % 4]
        for k, m in enumerate(voicing):
            add(pad, t0, pad_note(m, BAR + 1.4), 0.16, pan=(k - 1.5) * 0.35)
        add(bass, t0, bass_note(root, BAR + 0.9), 0.30)
        # Felt-piano arpeggio: quarter notes at first, eighth notes from the proposed solution onward.
        if t0 < start["s1"] - 0.2:
            continue
        lift = start["s4"] - 0.5 <= t0 < start["s8"]
        pattern = [0, 1, 2, 3, 2, 1, 2, 3]
        for i in range(8):
            if not lift and i % 2:
                continue
            at = t0 + i * BAR / 8
            if at >= final_from:
                break
            m = voicing[pattern[i] % len(voicing)] + 12
            vel = (0.55 if i % 2 else 0.8) * (0.85 + 0.3 * rng.random())
            add(keys, at + rng.normal(0, 0.006), piano_note(m, vel), 0.22, pan=0.25 if i % 2 else -0.2)
        if lift and b % 2 == 0:  # soft high sparkle on the lift
            add(keys, t0 + BAR * 0.75, piano_note(voicing[-1] + 24, 0.45), 0.12, pan=0.4)

    # Resolve: a held C chord under the objective's last words, with a final high note.
    root, voicing = FINAL
    end_len = total + 0.5 - final_from
    for k, m in enumerate(voicing):
        add(pad, final_from, pad_note(m, end_len), 0.15, pan=(k - 2) * 0.3)
    add(bass, final_from, bass_note(root, end_len), 0.30)
    for k, m in enumerate([67, 72, 76, 79]):
        add(keys, final_from + 0.35 * k, piano_note(m, 0.7), 0.2, pan=-0.3 + 0.2 * k)

    # Soft air whooshes into each scene change (rising), a fuller swell into the proposed solution.
    for s in tl["scenes"][1:]:
        big = s["id"] == "s4"
        w = whoosh(1.6 if big else 0.8)
        add(sfx, s["start"] - (1.2 if big else 0.55), w, 0.22 if big else 0.10, pan=0.0)

    wet_pad = np.stack([reverb(pad[0] + pad[1], seed=1), reverb(pad[0] + pad[1], seed=2)])
    wet_keys = np.stack([reverb(keys[0] + keys[1], seed=3), reverb(keys[0] + keys[1], seed=4)])
    mix = 0.55 * pad + 0.35 * wet_pad * np.abs(pad).max() + 0.6 * keys + 0.55 * wet_keys * np.abs(keys).max() \
        + bass + sfx

    # Gentle fade in/out, normalize to -3 dBFS peak.
    t = np.arange(n) / SR
    mix *= np.clip(t / 2.0, 0, 1) * np.clip((total + 0.4 - t) / 3.0, 0, 1)
    mix *= 10 ** (-3 / 20) / np.abs(mix).max()
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(ROOT / "build/music.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"music: {total:.1f}s, {bars} bars at {BPM} bpm → build/music.wav")


if __name__ == "__main__":
    main()
