#!/usr/bin/env bash
# Crop the visual-upgrade inserts from the supplied reference board (1536×1024).
# The pack's individual PNGs are offset crops that include neighbouring panel headings,
# so each insert is cropped here from the board with exact panel coordinates.
# Baked-in text that would duplicate on-screen text (hook title, phone speech bubble) is cropped out.
set -euo pipefail
cd "$(dirname "$0")/.."
B=assets/source/visual_reference_board.png
O=assets/inserts
crop() { ffmpeg -loglevel error -y -i "$B" -vf "crop=$2:$3:$4:$5" "$O/$1.png"; }
#     name               w    h    x     y
crop hook_patient        153  214  232   36    # 01 — patient on trolley, without baked "WHERE IS THE PATIENT?"
crop admitted_still_ed   370  214  395   36    # 02 — "Patient A · Admitted for ward · Still in ED"
crop call_pharmacist     170  214  1150  36    # 04 — pharmacist on the phone, without baked speech bubble
crop state_ed            353  226  796   292   # 07 — state 1, still in ED
crop state_ward          363  226  1158  292   # 08 — state 2, in ward
crop transition          352  144  16    566   # 09 — ED → ward transition
echo "inserts → $O"
