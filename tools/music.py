#!/usr/bin/env python3
"""Synthesize the score and sound design from build/timeline.json and build/cues.json.

- Ambient bed: warm pad + sub bass over Am7 – Fmaj7 – C – G (slow), with sparse felt-piano notes.
  It stays silent through the hook ("Where is the patient?"), enters with the ambiguity, drops almost
  to nothing during the phone call, lifts gently at the initial proposal, and resolves on the last line.
- Cue-locked sound design: soft impacts on key typography, UI ticks, a handset phone ring, a pickup
  click, small pops, and a swell when the uncertainty appears.
Everything is generated here; no third-party audio. Writes build/music.wav (44.1 kHz stereo).
"""
import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 44100
BAR = 60 / 72 * 4  # 72 bpm, unhurried
rng = np.random.default_rng(7)

CHORDS = [(45, [57, 60, 64, 67]), (41, [53, 57, 60, 64]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67])]
FINAL = (48, [55, 60, 64, 67, 72])


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    sig = sig[: buf.shape[1] - i]
    buf[0, i:i + len(sig)] += sig * gain * np.sqrt((1 - pan) / 2)
    buf[1, i:i + len(sig)] += sig * gain * np.sqrt((1 + pan) / 2)


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def pad_note(m, dur):
    t, f = tvec(dur), hz(m)
    s = sum(np.sin(2 * np.pi * f * d * t + p) for d, p in ((1, 0), (1.0011, 1.3), (0.9989, 2.1)))
    s += 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return s / 3.3 * env(len(t), 1.4, 1.8)


def piano(m, vel):
    t, f = tvec(3.0), hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.25)
    return s * np.minimum(1, t / 0.006) * np.exp(-t / 0.9) * vel


def bass(m, dur):
    t = tvec(dur)
    return (np.sin(2 * np.pi * hz(m) * t) + 0.12 * np.sin(4 * np.pi * hz(m) * t)) * env(len(t), 0.4, 1.0)


def onepole(x, cut):
    """Time-varying (or fixed) one-pole low-pass."""
    cut = np.broadcast_to(cut, x.shape)
    a = np.exp(-2 * np.pi * cut / SR)
    y, out = 0.0, np.empty_like(x)
    for i in range(len(x)):
        y = (1 - a[i]) * x[i] + a[i] * y
        out[i] = y
    return out


def impact():
    t = tvec(1.6)
    f = 95 * np.exp(-t / 0.18) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    click = onepole(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.02) * 2.5
    return body + click


def tick():
    t = tvec(0.12)
    return (np.sin(2 * np.pi * 1850 * t) * 0.7 + np.sin(2 * np.pi * 2900 * t) * 0.3) * np.exp(-t / 0.018)


def pop():
    t = tvec(0.35)
    f = 520 + 380 * np.minimum(1, t / 0.07)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)


def step():
    return 0.55 * impact()[: int(1.0 * SR)] + 0.5 * np.pad(tick(), (0, int(1.0 * SR) - len(tick())))


def ring():
    """One handset 'brr-brr' ring (two 0.4 s bursts), band-limited like a phone line."""
    t = tvec(1.2)
    tone = np.sin(2 * np.pi * 400 * t) + np.sin(2 * np.pi * 450 * t)
    gate = (((t >= 0) & (t < 0.4)) | ((t >= 0.6) & (t < 1.0))).astype(float)
    gate = onepole(gate, 60)
    y = tone * gate
    y = y - onepole(y, 300)                 # high-pass ~300 Hz
    return onepole(y, 3400) * 0.8           # low-pass ~3.4 kHz


def pickup():
    t = tvec(0.25)
    return onepole(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.03) * 1.6


def swell(dur=2.2):
    t = tvec(dur)
    n = onepole(rng.standard_normal(len(t)), np.linspace(200, 2200, len(t)))
    return n / (np.abs(n).max() + 1e-9) * np.sin(np.linspace(0, np.pi, len(t))) ** 2


def reverb(x, seconds=2.8, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (seconds / 6.5))
    ir = np.convolve(ir, np.ones(12) / 12, mode="same")
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y / (np.abs(y).max() + 1e-9)


def main():
    tl = json.loads((ROOT / "build/timeline.json").read_text())
    cue = json.loads((ROOT / "build/cues.json").read_text())
    total = tl["duration"]
    S = {s["id"]: s for s in tl["scenes"]}
    n = int((total + 0.5) * SR)
    bed, keys, sfx = (np.zeros((2, n)) for _ in range(3))

    bed_from = S["s1"]["start"] - 0.4          # silence through the hook
    final_from = S["s8"]["lines"][-1]["start"] - 0.6
    lift_from = S["s5"]["start"]
    b = 0
    while bed_from + b * BAR < final_from:
        t0 = bed_from + b * BAR
        root, voicing = CHORDS[b % 4]
        for k, m in enumerate(voicing):
            add(bed, t0, pad_note(m, BAR + 1.8), 0.15, pan=(k - 1.5) * 0.35)
        add(bed, t0, bass(root, BAR + 1.0), 0.26)
        # Sparse piano: one note per half bar, a little denser from the initial proposal on.
        per_bar = 4 if t0 >= lift_from else 2
        for i in range(per_bar):
            at = t0 + i * BAR / per_bar
            if at < final_from - 0.2:
                m = voicing[[3, 1, 2, 0][i % 4]] + 12
                add(keys, at + rng.normal(0, 0.006), piano(m, 0.75 * (0.85 + 0.3 * rng.random())), 0.2, pan=-0.2 + 0.4 * (i % 2))
        b += 1
    root, voicing = FINAL
    for k, m in enumerate(voicing):
        add(bed, final_from, pad_note(m, total + 0.5 - final_from), 0.15, pan=(k - 2) * 0.3)
    add(bed, final_from, bass(root, total + 0.5 - final_from), 0.26)
    for k, m in enumerate([67, 72, 76, 79]):
        add(keys, final_from + 0.6 + 0.4 * k, piano(m, 0.7), 0.2, pan=-0.3 + 0.2 * k)

    music = 0.6 * bed + 0.35 * np.stack([reverb(bed.sum(0), seed=1), reverb(bed.sum(0), seed=2)]) * np.abs(bed).max() \
        + 0.65 * keys + 0.55 * np.stack([reverb(keys.sum(0), seed=3), reverb(keys.sum(0), seed=4)]) * np.abs(keys).max()

    # Gain automation: fade in after the hook, near-silence under the phone call, fade out at the end.
    t = np.arange(n) / SR
    g = np.clip((t - bed_from) / 2.5, 0, 1)
    q0, q1 = cue["quiet"]
    g *= 1 - 0.85 * np.clip((t - q0) / 0.8, 0, 1) * np.clip((q1 + 1.5 - t) / 1.5, 0, 1)
    g *= np.clip((total + 0.3 - t) / 2.5, 0, 1)
    music *= g

    kinds = {"impact": (impact, 0.42), "tick": (tick, 0.16), "pop": (pop, 0.14), "step": (step, 0.34),
             "ring": (ring, 0.62), "pickup": (pickup, 0.22), "swell": (swell, 0.10)}
    for c in cue["cues"]:
        fn, gain = kinds[c["kind"]]
        add(sfx, c["t"] - (1.2 if c["kind"] == "swell" else 0), fn(), gain, pan=0.15 if c["kind"] == "ring" else 0)
    # A touch of room on the sound effects.
    wet = reverb(sfx.sum(0), 1.4, 9) * np.abs(sfx).max()
    # Normalize on the music alone so the sound effects keep a fixed level relative to the bed,
    # then protect against clipping.
    norm = 10 ** (-3 / 20) / np.abs(music).max()
    mix = (music + sfx + 0.12 * np.stack([wet, wet])) * norm
    mix /= max(1.0, np.abs(mix).max() / 0.98)
    with wave.open(str(ROOT / "build/music.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype(np.int16).tobytes())
    print(f"music: {total:.1f}s, {b} bars, {len(cue['cues'])} sound cues → build/music.wav")


if __name__ == "__main__":
    main()
