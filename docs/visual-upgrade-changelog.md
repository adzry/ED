# V2 → V2 visual upgrade: change log

Same video, story, voice and message. Only visual layers (and one soft sound accent) were added.

## Preserved

- **Narration, script and voice timing are unchanged.** The upgrade was rendered from V2's exact narration
  track and timeline (`out/archive/narration-v2.wav`, `out/archive/timeline-v2.json`, checked byte-for-byte)
  with `npm run build:visual`, which skips narration synthesis.
- **Original V2 kept separately:** `out/archive/ed-pharmacy-visibility-v2.mp4` and `out/archive/captions-v2.srt`.
  Its source is commit `a287beb`, which also has the local tag `v2-base`.
- Scenes, scene order, captions, typography, colour system, transitions and the music bed are unchanged.

## Asset source

The pack's individual PNGs (`01_…`–`12_…`, 384×232) are offset crops that include neighbouring panels' headings
and edges. Each insert was re-cropped from `00_complete_visual_reference_board.png` at exact panel coordinates
(`tools/crop_assets.sh`), and baked-in text that would duplicate on-screen text was cropped out. The panels are
small (roughly 150–370 px wide), so they are used as framed inserts at up to about 2× scale, never full-screen, to
stay sharp at 1080p.

## Assets inserted (6)

| Asset | Beat / scene | Treatment |
|---|---|---|
| 01 hook (patient on trolley, without the baked "WHERE IS THE PATIENT?") | Hook (0–4 s) | **V2.2 hero:** split composition. "Where is the / patient?" sits on the left half of the paper. The patient image fills the right half full-bleed (50% of the frame, no border), super-resolved 4× with EDSR (`tools/upscale_hero.py`). It is revealed with a mask as "patient?" is spoken, then pushes in slowly (~4.5%) and the red dot lands above the patient's head. One soft "pop" accent |
| 02 admitted, still in ED | Ambiguity (≈4.5–7 s), while "A patient is admitted, and planned for the ward" is spoken | Tilted framed card ("Patient A · Admitted for ward · Still in ED") with a push-in. It leaves before "ADMITTED? Yes." so the Q&A rows keep the screen. "Illustration" label |
| 04 call ED (pharmacist on the phone, without the baked speech bubble) | Phone call (≈29 s) | Replaces the plain phone circle between the Pharmacy and ED cards as the phone rings. The red phone badge and its ring pulses move to the photo's corner. V2's Malay bubble is unchanged |
| 07 state: still in ED | ED → ward transition (≈56–61 s) | Thumbnail inside the PHIS location card next to "KECEMASAN & TRAUMA (ADMISSION)". "Illustration" label |
| 08 state: in ward | ED → ward transition (on arrival) | Mirrors 07 in the same frame and crossfades in at the exact moment the field changes to ACTUAL WARD, after the patient's dot reaches the ward |
| 09 ED → ward transition | Before vs initial proposal (≈66 s) | Fills the "Physical transition" node of the initial-proposal row (replacing the mini dot track) with a slow drift, a callback to the transition just shown |

## Motion added

Only small moves: 3–6% push-ins inside the photo frames, rise and fade reveals, one headline lift in the hook, and
the 07 → 08 crossfade locked to the PHIS field change. There are no new transitions or zooms.

## Timing adjustments

None. Scene timing comes from V2's timeline unchanged.

## Deliberately not used

- **03 information gap, 06 initial proposal, 11 current vs initial proposal:** V2 already draws these diagrams
  in crisp vector form. The low-resolution raster versions would add duplication and cognitive load.
- **10 PHIS update (simplified):** it reduces the poster's 8 steps to 6, including "Edit / Transfer", which would
  contradict the verbatim 8-step close and could read as a PHIS screen.
- **05 why it matters:** it would add density to a short scene whose point is already carried by the workflow
  cards.
- **12 objective:** the closing was set at your request to the 8 PHIS steps. Adding the objective card would
  change the ending and pacing. It can be added as a short held card after the steps if wanted.

## Fact safety

- Every insert showing a mock record card (02, 07, 08) carries an "Illustration" label, and none is presented as
  a PHIS screenshot.
- No new on-screen claims were added, and narration and captions are identical to V2.
- All existing checks pass on the upgraded build: layout, logic, wording and output.

## V2.2: intro hero correction

The V2.1 hook photo read as a thumbnail (341×469 px). It is now the hero visual of the opening, as described in
the table above. Only the opening composition changed: narration, opening text, timing and every other scene are
unchanged, and the build again used V2's archived narration and timeline. The hero source is the
patient region of the board, about 150 px wide, so it was super-resolved once with OpenCV EDSR ×4 rather than
simply enlarged.
