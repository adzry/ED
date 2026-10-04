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

# Proper nouns / terms from the poster, British spelling used in the brief, and the Malay phone line.
GLOSSARY = {"phis", "kecemasan", "ed", "gen", "med", "inpatient", "workflow", "standardise",
            "masih", "di", "lagi", "ke", "dah", "masuk",
            "isn"}  # contraction stem: "isn't" is split at the apostrophe

# Exact terms that must appear on screen.
REQUIRED_ON_SCREEN = [
    "INITIAL PROPOSAL", "TO BE VALIDATED", "KECEMASAN & TRAUMA", "(ADMISSION)", "KECEMASAN & TRAUMA (ADMISSION)",
    "ACTUAL WARD", "INPATIENT", "GEN MED", "STILL IN ED", "Call ED", "correct PHIS mechanism?",
    "Initial proposal · steps to be validated",
    # The poster's eight update steps.
    "Patient Management → Visit Management", "Kecemasan & Trauma (Admission)", "for the patient", "Double-click",
    "the patient’s name", "Edit", "Transfer Detail List", "new ward location", "Save",
]

# Variants that would misstate a poster term.
WRONG_TERMS = [
    r"Trauma\s*&\s*Kecemasan", r"Kecemasan\s+and\s+Trauma", r"General Medicine",
    r"\bKecemasan\b(?!\s*&\s*(Trauma|TRAUMA))", r"\bKECEMASAN\b(?!\s*&\s*TRAUMA)", r"\bPHIS system\b",
]

# Claims the poster and brief do not support, and language the brief rules out.
UNSUPPORTED = {
    r"\d+\s*%|\bpercent": "statistic",
    r"\beliminat|\bno (more|longer) (need|call)": "claims calls are eliminated",
    r"\bapproved\b|\bpolicy\b|\bmandatory\b|\bSOP\b|\bofficial|\bfinal workflow": "presents proposal as approved/final",
    # "Transfer Detail List" is the poster's PHIS screen name; any other "transfer" wording is not allowed.
    r"\btransfer\b(?! Detail List)": "names a PHIS mechanism as if confirmed",
    r"\bsolves?\b|\bsolution\b": "presents proposal as a proven solution",
    r"\btime sav|\bfaster\b|\breduc": "claims a measured improvement",
    r"\berrors?\b|\bunsafe\b|\bdanger|\blife-threatening|\bharm\b": "medication-safety claim",
    r"\breal[- ]time\b|\bautomatic|\binstant": "invented PHIS behaviour",
    r"\bguarantee|\balways\b|\bnever\b|\bevery patient\b": "absolute claim",
    r"\bnurse|\bclerk|\bdoctors?\b|\bregistrar": "invents who performs the update",
    r"\bfault|\bblame|\bmistake|\bnegligen|\bcareless|\bfail": "blames a team",
}
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
                problems.append(f"unsupported claim ({why}) [{src}] '{m.group(0)}' in: {text}")

    # Framing: the narration must call it an initial proposal and say it needs validation,
    # including whether it is the correct PHIS mechanism.
    spoken = " ".join(narration)
    for must, why in [(r"initial proposal", "names it an initial proposal"),
                      (r"must be validated", "says it must be validated"),
                      (r"correct PHIS mechanism", "questions whether it is the correct PHIS mechanism")]:
        if not re.search(must, spoken, re.I):
            problems.append(f"framing: narration never {why}")
    # Proposal-stage verbs must stay conditional in the transition scene.
    for s in board["scenes"]:
        # The transition scene, and the framing lines around the step list, must stay conditional.
        framing = s["lines"] if s["id"] == "s6" else [s["lines"][0], s["lines"][-1]] if s["id"] == "s8" else []
        if not all(re.search(r"\bwould\b", l["text"]) for l in framing):
            problems.append(f"framing: {s['id']} must describe the proposal conditionally ('would')")

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
