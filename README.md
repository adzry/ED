# Where is the patient? — ED-to-ward visibility for Inpatient Pharmacy

A ~90-second explainer video built strictly from the poster *"The Problem / Why It Matters / Proposed Solution /
How to Update PHIS Location / Our Objective"*. It presents the PHIS workflow as a **proposed** solution, not an
approved policy.

**Output:** `out/ed-pharmacy-visibility.mp4` (1920×1080, 30 fps, H.264 + AAC, captions burned in) and
`out/captions.srt`.

## Pipeline

Everything is generated from one source of truth, `script/storyboard.json` (narration lines, pronunciation
overrides, caption highlight terms).

| Step | Tool | What it does |
|---|---|---|
| narrate | `tools/narrate.py` | Piper TTS (lessac voice) per line → measured durations set scene/line/caption timing → `build/timeline.json`, `build/narration.wav`, `out/captions.srt` |
| scenes | `scenes/index.html` | All 8 scenes as HTML/SVG with a deterministic `renderAt(t)`; animations are keyed to narration word timing |
| validate | `tools/check_layout.mjs`, `tools/check_text.py` | Frame-sampled layout checks + editorial checks (below) |
| render | `tools/render.mjs` | Headless Chromium captures every frame → `build/video.mp4` |
| mix | `tools/mix.sh` | Synthesized ambient pad, side-chain ducked under the voice, loudness-normalized to −16 LUFS, muxed |
| check:output | `tools/check_output.py` | Format, frame rate, duration vs timeline, audio present, loudness, SRT cue count |

```bash
npm install && npm run setup   # Node deps, piper-tts + pyspellchecker, voice model
npm run build                  # narrate → validate → render → mix → check:output → stills
```

### Validation

- **Layout** (every 0.2 s): text inside the safe area and inside its card, no overlapping text, captions on one
  line and clear of all content, narration and captions inside their scene, the "PROPOSED WORKFLOW" tag visible from
  scene 4 onwards, and **ED → ward logic**: PHIS never shows the ward location before the patient reaches the ward.
- **Text** (narration, captions and every on-screen string): spelling, the exact poster terms (e.g.
  `KECEMASAN & TRAUMA (ADMISSION)`, `Transfer Detail List`), wrong variants of those terms, and a list of claims the
  poster does not support: statistics, "eliminates calls", approved/policy, time saved, medication-error claims,
  real-time/automatic PHIS behaviour, and who performs the update.

## Content sources and limits

**Confirmed from the poster:** the problem (Pharmacy must call ED to know whether an admitted patient is still in
ED or in the ward), why it matters (order processing, verification, dispensing; delay, workload, outdated
information), the ED and ward PHIS states (Visit Type Inpatient, Department Gen Med, Location
Kecemasan & Trauma (Admission) → Actual Ward Location), the 8 update steps, and the objective.

**Proposed (labelled as proposed on screen and in narration):** registering patients under
Kecemasan & Trauma (Admission), updating the location on ward entry, and the update steps.

**Deliberately not stated, because the poster doesn't say:** who performs the update, whether this applies
beyond Gen Med, whether PHIS updates in real time, whether phone calls stop entirely, any figures or time savings,
and approval status. The PHIS interface is shown only as abstract cards, never as screenshots. The poster's phrase
"potential medication errors" is left out on purpose.

## Licensing notes

- Voice: Piper `en-us-lessac-medium`, trained on the Blizzard 2013 Lessac dataset, whose licence appears to be
  research/non-commercial. Confirm it suits your intended use (internal hospital training).
- Font: Inter (SIL OFL). Music is synthesized in `tools/mix.sh`, so there are no third-party audio assets.
