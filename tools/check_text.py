#!/usr/bin/env python3
"""Editorial validation of every word the viewer reads or hears.

Inputs: script/storyboard.json, build/timeline.json, build/screen_text.json (from check_layout.mjs).
Checks: spelling, exact PHIS terminology from the poster, and claims the poster does not support.
"""
import json
import re
import sys
from pathlib import Path

from spellchecker import SpellChecker

ROOT = Path(__file__).resolve().parent.parent

# Proper nouns / terms taken from the poster.
GLOSSARY = {"phis", "kecemasan", "ed", "gen", "med", "inpatient", "workflow"}

# Exact poster terms that must appear on screen.
REQUIRED_ON_SCREEN = [
    "KECEMASAN & TRAUMA (ADMISSION)", "Kecemasan & Trauma (Admission)", "ACTUAL WARD LOCATION",
    "INPATIENT", "GEN MED", "Patient Management → Visit Management", "Transfer Detail List",
    "new ward location", "Proposed solution", "STILL IN ED", "PATIENT IN WARD", "PHIS LOCATION",
    "PHARMACY VISIBILITY",
]

# Variants that would misstate a poster term.
WRONG_TERMS = [
    r"Trauma\s*&\s*Kecemasan", r"Kecemasan\s+and\s+Trauma", r"General Medicine", r"\bKecemasan\b(?!\s*&\s*Trauma)",
    r"Transfer Details? Lists\b", r"Transfer Details List", r"\bPHIS system\b",
]

# Claims the poster does not support (statistics, outcomes, approval status, system behaviour).
UNSUPPORTED = {
    r"\d+\s*%|\bpercent": "statistic",
    r"\beliminat": "claims calls are eliminated",
    r"\bno (more|longer) (need|call)": "claims calls are eliminated",
    r"\bapproved\b|\bpolicy\b|\bmandatory\b|\bSOP\b|\bofficial": "presents proposal as approved",
    r"\bsaves?\b(?! *$)|\btime sav|\bfaster\b|\breduc": "claims a measured improvement",
    r"\berrors?\b|\bunsafe\b|\bdanger|\blife-threatening|\bharm\b": "medication-safety claim",
    r"\breal[- ]time\b|\bautomatic|\binstant": "invented PHIS behaviour",
    r"\bguarantee|\balways\b|\bnever\b|\bevery patient\b": "absolute claim",
    r"\bnurse|\bclerk|\bdoctor|\bregistrar": "invents who performs the update",
}
# "Click Save" / "and save." are poster workflow steps, not a time-saving claim.
ALLOWED_SAVE = {"Click Save", "Save", "and save."}


def main():
    board = json.loads((ROOT / "script/storyboard.json").read_text())
    tl = json.loads((ROOT / "build/timeline.json").read_text())
    screen = json.loads((ROOT / "build/screen_text.json").read_text())
    narration = [l["text"] for s in board["scenes"] for l in s["lines"]]
    captions = [c["text"] for s in tl["scenes"] for l in s["lines"] for c in l["captions"]]
    corpus = [("narration", t) for t in narration] + [("caption", t) for t in captions] + [("screen", t) for t in screen]
    problems = []

    spell = SpellChecker()
    spell.word_frequency.load_words(GLOSSARY)
    for src, text in corpus:
        words = re.findall(r"[A-Za-z][A-Za-z'’.-]*[A-Za-z]|[A-Za-z]", text)
        for w in words:
            parts = [p for p in re.split(r"[-’'.]", w.lower()) if p and p not in {"s"}]
            for p in parts:
                if len(p) > 1 and p not in GLOSSARY and spell.unknown([p]):
                    problems.append(f"spelling [{src}] '{w}' in: {text}")

    screen_blob = "\n".join(screen)
    for term in REQUIRED_ON_SCREEN:
        if term not in screen_blob:
            problems.append(f"terminology: required on-screen term missing: {term}")
    for src, text in corpus:
        for pat in WRONG_TERMS:
            if re.search(pat, text):
                problems.append(f"terminology [{src}] /{pat}/ in: {text}")
        for pat, why in UNSUPPORTED.items():
            for m in re.finditer(pat, text, flags=re.I):
                if "save" in m.group(0).lower() and (text.strip() in ALLOWED_SAVE or text.rstrip().endswith("and save.")):
                    continue
                problems.append(f"unsupported claim ({why}) [{src}] '{m.group(0)}' in: {text}")

    # Proposed framing must be stated in narration for the solution and result.
    for sid in ("s4", "s6", "s7"):
        lines = " ".join(l["text"] for s in board["scenes"] if s["id"] == sid for l in s["lines"])
        if not re.search(r"propos", lines, re.I):
            problems.append(f"framing: scene {sid} narration does not say the workflow is proposed")

    # Captions must reproduce the narration exactly.
    for s in tl["scenes"]:
        for l in s["lines"]:
            if " ".join(c["text"] for c in l["captions"]) != l["text"]:
                problems.append(f"captions do not match narration: {l['text']}")

    problems = sorted(set(problems))
    for p in problems:
        print(p)
    print(f"text: {'OK' if not problems else f'{len(problems)} problem(s)'} "
          f"({len(narration)} narration lines, {len(captions)} captions, {len(screen)} on-screen strings)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
