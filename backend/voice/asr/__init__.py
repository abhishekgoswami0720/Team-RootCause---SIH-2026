"""
ASR (Speech-to-Text) subpackage for MandiQ Voice Module.
"""

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
    transcribe_audio,
)

__all__ = [
    "ASRError",
    "AudioFileNotFoundError",
    "EmptyAudioError",
    "EmptyTranscriptError",
    "InvalidAudioFormatError",
    "MissingAPIKeyError",
    "NetworkError",
    "SarvamAPIError",
    "SarvamASR",
    "transcribe_audio",
]
