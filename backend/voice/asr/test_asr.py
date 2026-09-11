"""
CLI test runner for MandiQ Voice ASR module (Milestone 2).

Usage:
    python voice/asr/test_asr.py --audio voice/asr/samples/sample_farmer_input.wav
    python voice/asr/test_asr.py --generate-sample
"""

import argparse
import sys
import time
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

from voice.asr.sarvam_asr import (
    ASRError,
    AudioFileNotFoundError,
    EmptyAudioError,
    EmptyTranscriptError,
    InvalidAudioFormatError,
    MissingAPIKeyError,
    NetworkError,
    SarvamAPIError,
    SarvamASR,
)

DEFAULT_SAMPLE_TEXT = "मेरा गाँव नांगल है और मेरी फसल गेहूँ है।"
DEFAULT_SAMPLE_PATH = "voice/asr/samples/sample_farmer_input.wav"


def generate_convenience_sample(output_path: str, text: str) -> str:
    """
    Convenience helper to generate a sample audio file using Milestone 1 TTS.
    NOTE: Synthetic TTS audio is for pipeline connectivity verification only;
    it does NOT replace real human Hindi recordings for field testing.
    """
    try:
        from voice.tts.sarvam_tts import SarvamTTS

        print("\n[INFO] Generating convenience sample using Sarvam TTS...")
        print(f"Text: \"{text}\"")
        tts = SarvamTTS()
        saved = tts.synthesize(text=text, output_filepath=output_path)
        print(f"[SUCCESS] Convenience audio sample created at: {saved}\n")
        return saved
    except Exception as e:
        print(f"[ERROR] Could not generate sample with TTS: {e}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="MandiQ Voice ASR Test Runner (Sarvam AI Hindi Speech-to-Text)"
    )
    parser.add_argument(
        "--audio",
        "-a",
        default=None,
        help="Path to the Hindi audio file to transcribe (.wav, .mp3, .m4a, etc.)",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Synthesize a sample Hindi audio using TTS and transcribe it as a pipeline round-trip test.",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="hi-IN",
        help="BCP-47 language code (default: 'hi-IN')",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="saaras:v3",
        help="Sarvam ASR model (default: 'saaras:v3')",
    )

    args = parser.parse_args()

    audio_path = args.audio

    print("=" * 65)
    print("MandiQ Voice Module - Milestone 2: Hindi Speech-to-Text (ASR)")
    print("=" * 65)

    if args.generate_sample:
        print("> [NOTE] TTS-generated audio is used for pipeline verification only.")
        print("> Real farmer audio recordings should be used for field accuracy testing.")
        sample_file = Path(DEFAULT_SAMPLE_PATH).resolve()
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        generate_convenience_sample(str(sample_file), DEFAULT_SAMPLE_TEXT)
        audio_path = str(sample_file)

    if not audio_path:
        # Check if default sample exists
        candidate = Path(DEFAULT_SAMPLE_PATH).resolve()
        if candidate.is_file():
            audio_path = str(candidate)
            print(f"[INFO] Using existing default sample: {audio_path}")
        else:
            print("\n[USAGE ERROR] No audio file specified.", file=sys.stderr)
            print("Please provide an audio file with --audio <path> or use --generate-sample.", file=sys.stderr)
            print("\nExamples:")
            print("  python voice/asr/test_asr.py --audio path/to/my_recording.wav")
            print("  python voice/asr/test_asr.py --generate-sample\n")
            sys.exit(1)

    file_path = Path(audio_path).resolve()
    print(f"Target Audio : {file_path}")
    if file_path.is_file():
        print(f"File Size    : {file_path.stat().st_size:,} bytes")
    print(f"Language Code: {args.language}")
    print(f"Model        : {args.model}")
    print("-" * 65)

    try:
        asr = SarvamASR()
        print("Sending audio to Sarvam AI Speech-to-Text API...")
        start_time = time.time()
        transcript = asr.transcribe(
            audio_path=str(file_path),
            language_code=args.language,
            model=args.model,
        )
        elapsed = time.time() - start_time

        print("\n" + "=" * 65)
        print("[SUCCESS] Speech Recognized Successfully!")
        print("=" * 65)
        print(f"Transcript : {transcript}")
        print(f"Latency    : {elapsed:.2f} seconds")
        print("=" * 65)

    except MissingAPIKeyError as e:
        print("\n[CONFIG ERROR] Missing Sarvam API Key!", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("\nFix: Set SARVAM_API_KEY in your local .env file:\n  SARVAM_API_KEY=your_key_here\n", file=sys.stderr)
        sys.exit(1)

    except AudioFileNotFoundError as e:
        print(f"\n[FILE ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    except InvalidAudioFormatError as e:
        print(f"\n[FORMAT ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    except EmptyAudioError as e:
        print(f"\n[EMPTY AUDIO ERROR] {e}", file=sys.stderr)
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

    except EmptyTranscriptError as e:
        print(f"\n[EMPTY TRANSCRIPT] {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
