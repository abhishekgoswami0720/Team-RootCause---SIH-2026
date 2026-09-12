"""
Fallback input ladder subpackage for MandiQ Voice Module.

Provides fallback input resolution: Sarvam ASR -> Browser Speech -> Keypad.
"""

from voice.fallback.fallback_manager import (
    VoiceFallbackManager,
    VoiceResult,
)

__all__ = [
    "VoiceFallbackManager",
    "VoiceResult",
]
