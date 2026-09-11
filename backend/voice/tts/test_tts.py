"""
CLI test runner for MandiQ Voice TTS module (Milestone 1).

Usage:
    python voice/tts/test_tts.py
    python voice/tts/test_tts.py --text "कस्टम संदेश" --output "custom.wav"
"""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for safe printing of Devanagari/Unicode in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path so the module can be run directly from any directory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from voice.tts.sarvam_tts import (
    SarvamTTS,
    MissingAPIKeyError,
    EmptyTextError,
    NetworkError,
    SarvamAPIError,
)

DEFAULT_TEST_PHRASE = "स्लॉट बुक करना है, तो एक दबाइए।"
DEFAULT_OUTPUT_FILE = "voice/tts/output/slot_booking_prompt.wav"


def main():
    parser = argparse.ArgumentParser(
        description="MandiQ Voice TTS Test Runner (Sarvam AI Hindi Synthesis)"
    )
    parser.add_argument(
        "--text",
        "-t",
        default=DEFAULT_TEST_PHRASE,
        help=f"Hindi text to synthesize (default: '{DEFAULT_TEST_PHRASE}')",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Destination path for generated audio (default: '{DEFAULT_OUTPUT_FILE}')",
    )
    parser.add_argument(
        "--speaker",
        "-s",
        default="shubh",
        help="Speaker voice (default: 'shubh')",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MandiQ Voice Module - Milestone 1: TTS Generation")
    print("=" * 60)
    print(f"Input Text   : {args.text}")
    print(f"Target Output: {args.output}")
    print(f"Speaker Voice: {args.speaker}")
    print("-" * 60)

    try:
        tts = SarvamTTS()
        print("Sending synthesis request to Sarvam AI...")
        saved_file = tts.synthesize(
            text=args.text,
            output_filepath=args.output,
            speaker=args.speaker,
        )

        file_size_bytes = Path(saved_file).stat().st_size
        print("[SUCCESS] Audio file successfully generated and saved!")
        print(f"Saved Path : {saved_file}")
        print(f"File Size  : {file_size_bytes:,} bytes")
        print("=" * 60)

    except MissingAPIKeyError as e:
        print("\n[CONFIG ERROR] Missing Sarvam API Key!", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("\nFix: Add your key to .env file:\n  SARVAM_API_KEY=your_key_here\nor run in terminal:\n  set SARVAM_API_KEY=your_key_here  (Windows)\n  export SARVAM_API_KEY=your_key_here (Linux/Mac)\n", file=sys.stderr)
        sys.exit(1)

    except EmptyTextError as e:
        print(f"\n[VALIDATION ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    except NetworkError as e:
        print(f"\n[NETWORK ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    except SarvamAPIError as e:
        print(f"\n[API ERROR] Status code: {e.status_code}", file=sys.stderr)
        print(f"Message: {e.message}", file=sys.stderr)
        if e.error_details:
            print(f"Details: {e.error_details}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
