"""
MandiQ SIH26032 Voice Module.

This module handles speech input/output (TTS synthesis, ASR speech-to-text, deterministic NLU, and Fallback Input Ladder).
NOTE: The Voice module must NEVER directly make booking decisions.
"""

from voice.fallback import VoiceFallbackManager, VoiceResult

__version__ = "0.4.0"

__all__ = [
    "VoiceFallbackManager",
    "VoiceResult",
]




