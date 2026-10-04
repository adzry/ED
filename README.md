# Where is the patient? — ED-to-ward visibility for Inpatient Pharmacy

A ~97-second documentary-style explainer for HOD/leadership, Medical Officers, Inpatient Pharmacy and the IT/PHIS
team. It is meant to start a conversation, not sell a system. Its spine:

> The problem is not the admission. The problem is knowing where the admitted patient actually is.

The PHIS approach is presented throughout as an **INITIAL PROPOSAL — TO BE VALIDATED**, never as an approved or
final workflow.

**Output:** `out/ed-pharmacy-visibility.mp4` (1920×1080, 30 fps, H.264 + AAC, captions burned in) and
`out/captions.srt`.

## Story

| # | Beat | What the viewer sees |
|---|---|---|
| 0 | Hook | "Where is the patient?" lands word by word, then about 2.5 s of silence |
| 1 | Ambiguity | ADMITTED? *Yes.* · STILL IN ED? *Maybe.* · IN THE WARD? *Maybe.* The patient's dot smears across the ED–WARD line |
| 2 | Thesis | "The problem isn't the ~~admission~~" · physical location ≠ what the system shows |
| 3 | Human friction | Pharmacy's record shows Location "?" → the phone rings → *"Hi, patient A... masih di ED lagi ke dah masuk ward?"* → "someone has to ask" |
| 4 | Why it matters | Location → order processing → verification → dispensing |
| 5 | Initial proposal | "So what if the system itself could make that transition clearer?" → INITIAL PROPOSAL stamp → Visit Type INPATIENT, Department GEN MED, Location KECEMASAN & TRAUMA (ADMISSION) |
| 6 | Transition | The dot travels ED → WARD; the label "ED" becomes "WARD"; PHIS shows ACTUAL WARD only after arrival |
| 7 | Before vs proposal, caution | Before: Pharmacy → ? → Call ED. Initial proposal: PHIS → ED admission → physical transition → ward location → clearer visibility, stamped TO BE VALIDATED, with "correct PHIS mechanism?" circled |
| 8 | How the location would be updated | Labelled "Initial proposal · steps to be validated": the poster's 8 PHIS steps light up one by one as an abstract cursor clicks through them, ending with the location moving from ED admission to ward |

The closing scene shows the poster's 8 PHIS steps verbatim, as abstract cards (no screenshots), framed as steps still to be validated.

## Pipeline

`script/storyboard.json` is the single source for narration, pronunciation, caption highlights and pauses.

| Step | Tool | What it does |
|---|---|---|
| narrate | `tools/narrate.py` | Piper TTS per line; measured durations, per-line pauses and per-scene tails set the timeline → `build/timeline.json`, `build/narration.wav`, `out/captions.srt` |
| scenes | `scenes/index.html` | Nine custom compositions with a deterministic `renderAt(t)`, keyed to narration word timing. Also exports sound cues and the ED → ward logic state |
| validate | `tools/check_layout.mjs`, `tools/check_text.py` | Frame-sampled layout and logic checks + editorial/factual checks (below) |
| render | `tools/render.mjs` | Headless Chromium captures every frame → `build/video.mp4` (bitrate capped to stay under GitHub's 100 MB limit) |
| music | `tools/music.py` | Ambient bed (pad, bass, sparse piano) plus sound effects locked to the picture: soft impacts on key typography, UI ticks, a handset phone ring and pickup, pops, and a swell on "uncertainty". Silent under the hook, near-silent during the call |
| mix | `tools/mix.sh` | Music ducked under the voice; linear loudness normalization to −16 LUFS; muxed |
| check:output | `tools/check_output.py` | Format, frame rate, duration, audio, loudness, file size, SRT cue count |

```bash
npm install && npm run setup   # Node deps, piper-tts + pyspellchecker, voice model
npm run build                  # narrate → validate → render → mix → check:output → stills
```

### Validation

- **Layout** (every 0.2 s): text inside the safe area and inside its card, no overlapping text, captions on one
  line and clear of content, narration and captions inside their scene, the INITIAL PROPOSAL tag visible once the
  proposal is introduced, and the **ED → ward logic**: PHIS never shows the ward location before the patient arrives.
- **Text** (narration, captions, every on-screen string): spelling; exact poster terms; the narration must say
  "initial proposal", "must be validated" and question the "correct PHIS mechanism"; the transition must be
  described conditionally ("would"). The check also flags anything the poster and brief rule out: statistics,
  "eliminates calls", approved/final/mandatory, naming a transfer mechanism as confirmed, "solution/solves",
  measured improvements, medication-error claims, real-time/automatic PHIS behaviour, naming who performs the
  update, and blaming language.

## Visual language

Neutral paper and ink, with one accent (red) for uncertainty and the information gap, and green for the ward.
There is one recurring metaphor: the patient's location is a dot on an ED → WARD line. Serif display type carries
the story, Inter carries the labels, and handwritten notes are used sparingly. Scenes change with a directional
push. There are no screenshots, stock footage or third-party branding.

## Content sources and limits

**Confirmed from the poster:** the problem (Pharmacy calls ED to learn whether an admitted patient is still in ED
or already in the ward), why it matters (order processing, verification, dispensing; delay, workload, outdated
information), the ED-stage PHIS registration (Inpatient · Gen Med · Kecemasan & Trauma (Admission)), the ward state
(actual ward location), and the objective.

**Initial proposal (labelled as such):** using that registration while the patient remains in ED, and updating the
location when the patient physically enters the ward. Whether this is the correct PHIS mechanism is stated as
something still to validate.

**Not stated, because it isn't known:** who performs the update, whether this applies beyond Gen Med, real-time
behaviour, whether phone calls stop, any figures or outcomes, and approval status.

## Licensing notes

- Voice: Piper `en-us-lessac-medium`, trained on the Blizzard 2013 Lessac dataset, whose licence appears to be
  research/non-commercial. Confirm it suits your intended use (internal hospital use).
- Fonts: Inter, DM Serif Display, Caveat (all SIL OFL). All music and sound effects are synthesized in
  `tools/music.py`.
