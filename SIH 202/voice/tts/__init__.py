"""
TTS (Text-to-Speech) subpackage for MandiQ Voice Module.
"""

from voice.tts.sarvam_tts import (
    SarvamTTS,
    MissingAPIKeyError,
    EmptyTextError,
    NetworkError,
    SarvamAPIError,
    synthesize_speech,
)

__all__ = [
    "SarvamTTS",
    "MissingAPIKeyError",
    "EmptyTextError",
    "NetworkError",
    "SarvamAPIError",
    "synthesize_speech",
]
