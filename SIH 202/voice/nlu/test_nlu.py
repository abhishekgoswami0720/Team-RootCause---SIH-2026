"""
CLI test runner / demo for MandiQ Deterministic NLU (Milestone 3).

Usage:
    python voice/nlu/test_nlu.py
"""

import json
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for safe printing of Devanagari/Unicode in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from voice.nlu.deterministic_nlu import DeterministicNLU

DEMO_SENTENCES = [
    (
        "Standard Hindi sentence (Both entities)",
        "मेरा गाँव नांगल है और मेरी फसल गेहूँ है।",
    ),
    (
        "Conversational Hindi variation (Both entities)",
        "मैं नांगल गाँव से हूँ और गेहूँ लेकर आया हूँ।",
    ),
    (
        "Short phrase with punctuation (Both entities)",
        "गाँव नांगल, फसल गेहूँ।",
    ),
    (
        "Hindi spelling variation: 'गेहूं' with Barsana village",
        "गाँव बरसाना और फसल गेहूं है।",
    ),
    (
        "Mixed Hindi-English text (Govardhan + Mustard)",
        "गाँव गोवर्धन, crop mustard.",
    ),
    (
        "Village-only sentence (Missing crop)",
        "हम गोवर्धन गाँव के किसान हैं।",
    ),
    (
        "Crop-only sentence (Missing village)",
        "मेरी फसल सरसों और तिलहन में आती है।",
    ),
    (
        "Ambiguous sentence (Two different villages mentioned)",
        "नांगल और गोवर्धन के बीच में खेत है, फसल बाजरा है।",
    ),
    (
        "Unrecognized input (General Mandi inquiry, neither entity)",
        "नमस्ते बाबूजी, कल मंडी किस समय खुलेगी?",
    ),
]


def run_demo():
    print("=" * 70)
    print("MandiQ Voice Module - Milestone 3: Deterministic NLU Demo")
    print("Rule- & Dictionary-Based Entity Extraction (Zero LLM / Zero APIs)")
    print("=" * 70)

    nlu = DeterministicNLU()

    for idx, (label, text) in enumerate(DEMO_SENTENCES, start=1):
        print(f"\n[{idx}] Case: {label}")
        print(f"Input Text : \"{text}\"")
        result = nlu.parse(text)
        print("Output JSON:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 70)


if __name__ == "__main__":
    run_demo()
