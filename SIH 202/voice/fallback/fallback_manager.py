"""
Voice Input Fallback Ladder for MandiQ Voice Module.

Provides fallback input resolution:
1. Sarvam ASR (Primary Speech-to-Text)
2. Browser Speech Recognition (Client-side / Web Speech API)
3. Keypad Input (DTMF / Touch-tone / Numeric input)

ARCHITECTURAL BOUNDARY:
The fallback manager only decides HOW user input is obtained.
It does NOT allocate slots, generate tokens, access the database,
call /book, implement HALT/rescheduling, or contain business logic.
"""

import inspect
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Canonical method names
METHOD_SARVAM = "sarvam"
METHOD_BROWSER = "browser"
METHOD_KEYPAD = "keypad"
METHOD_NONE = "none"


@dataclass
class VoiceResult:
    """
    Structured result returned by the VoiceFallbackManager.

    Attributes:
        success: Whether any input provider succeeded in acquiring valid non-empty text.
        text: The recognized transcript or keypad input (whitespace-stripped), or None.
        method: The method that succeeded ('sarvam', 'browser', 'keypad', or 'none').
        error: Error details if all providers failed or warnings encountered.
    """
    success: bool
    text: Optional[str]
    method: str
    error: Optional[str] = None


def sanitize_error(error_msg: str) -> str:
    """
    Strip potential API keys, credentials, and tokens from error messages.

    Args:
        error_msg: Raw error message string.

    Returns:
        Sanitized error message.
    """
    if not error_msg:
        return ""

    # Redact explicit token / key patterns
    sanitized = re.sub(
        r"(?i)(api[_-]?key|secret|token|authorization|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
        r"\1=***",
        error_msg,
    )

    # Redact active SARVAM_API_KEY environment variable if present
    env_key = os.environ.get("SARVAM_API_KEY")
    if env_key and len(env_key) > 4 and env_key in sanitized:
        sanitized = sanitized.replace(env_key, "***")

    return sanitized


def _invoke_provider(provider: Any, audio_input: Any = None) -> Optional[str]:
    """
    Invoke an input provider, supporting callables or objects with a transcribe method.

    Args:
        provider: Callable or instance to invoke.
        audio_input: Optional audio file path or bytes passed to ASR if accepted.

    Returns:
        Stripped string transcript/input on success, or None if empty/whitespace/None.
    """
    if provider is None:
        return None

    # If the provider is directly callable (functions, lambdas, callable mocks)
    if callable(provider):
        sig = None
        try:
            sig = inspect.signature(provider)
        except (ValueError, TypeError):
            sig = None

        if sig is not None:
            params = list(sig.parameters.values())
            if audio_input is not None and len(params) > 0:
                raw_result = provider(audio_input)
            elif len(params) == 0:
                raw_result = provider()
            elif audio_input is not None:
                raw_result = provider(audio_input)
            else:
                raw_result = provider()
        else:
            if audio_input is not None:
                try:
                    raw_result = provider(audio_input)
                except TypeError:
                    raw_result = provider()
            else:
                raw_result = provider()
    # Support object instances with .transcribe() (e.g. SarvamASR class instances)
    elif hasattr(provider, "transcribe") and callable(getattr(provider, "transcribe")):
        raw_result = provider.transcribe(audio_input)
    else:
        return None

    if raw_result is None:
        return None

    cleaned = str(raw_result).strip()
    return cleaned if cleaned else None


class VoiceFallbackManager:
    """
    Manages the input fallback ladder:
    1. Sarvam ASR
    2. Browser Speech Recognition
    3. Keypad Input

    Uses dependency injection so all providers can be mocked or swapped
    without requiring real microphones, browser APIs, or network credentials.
    """

    def __init__(
        self,
        sarvam_asr: Optional[Callable[..., Any]] = None,
        browser_speech: Optional[Callable[..., Any]] = None,
        keypad: Optional[Callable[..., Any]] = None,
    ):
        """
        Initialize VoiceFallbackManager with optional default providers.

        Args:
            sarvam_asr: Default Sarvam ASR provider (callable or SarvamASR instance).
            browser_speech: Default Browser Speech Recognition provider callable.
            keypad: Default Keypad input provider callable.
        """
        self.sarvam_asr = sarvam_asr
        self.browser_speech = browser_speech
        self.keypad = keypad

    def get_input(
        self,
        audio_input: Any = None,
        sarvam_asr: Optional[Callable[..., Any]] = None,
        browser_speech: Optional[Callable[..., Any]] = None,
        keypad: Optional[Callable[..., Any]] = None,
    ) -> VoiceResult:
        """
        Attempt to acquire user input following the strict fallback ladder:
        Sarvam ASR -> Browser Speech -> Keypad.

        Args:
            audio_input: Audio file path, audio bytes, or context for Sarvam ASR.
            sarvam_asr: Override for Sarvam ASR provider.
            browser_speech: Override for Browser Speech provider.
            keypad: Override for Keypad provider.

        Returns:
            VoiceResult with success flag, extracted text, method name, and error info.
        """
        active_sarvam = sarvam_asr if sarvam_asr is not None else self.sarvam_asr
        active_browser = browser_speech if browser_speech is not None else self.browser_speech
        active_keypad = keypad if keypad is not None else self.keypad

        failures: List[Tuple[str, str]] = []

        # ---------------------------------------------------------
        # Level 1: Sarvam ASR (Primary Speech-to-Text)
        # ---------------------------------------------------------
        if active_sarvam is not None:
            try:
                text = _invoke_provider(active_sarvam, audio_input=audio_input)
                if text:
                    logger.info("Input successfully acquired via Sarvam ASR.")
                    return VoiceResult(
                        success=True,
                        text=text,
                        method=METHOD_SARVAM,
                        error=None,
                    )
                failures.append((METHOD_SARVAM, "Empty or whitespace transcript returned."))
            except Exception as exc:
                err_msg = sanitize_error(str(exc)) or type(exc).__name__
                logger.warning(f"Sarvam ASR failed: {err_msg}")
                failures.append((METHOD_SARVAM, err_msg))
        else:
            failures.append((METHOD_SARVAM, "Provider not configured or unavailable."))

        # ---------------------------------------------------------
        # Level 2: Browser Speech Recognition (Fallback 1)
        # ---------------------------------------------------------
        if active_browser is not None:
            try:
                text = _invoke_provider(active_browser)
                if text:
                    logger.info("Input successfully acquired via Browser Speech.")
                    return VoiceResult(
                        success=True,
                        text=text,
                        method=METHOD_BROWSER,
                        error=None,
                    )
                failures.append((METHOD_BROWSER, "Empty or whitespace transcript returned."))
            except Exception as exc:
                err_msg = sanitize_error(str(exc)) or type(exc).__name__
                logger.warning(f"Browser speech recognition failed: {err_msg}")
                failures.append((METHOD_BROWSER, err_msg))
        else:
            failures.append((METHOD_BROWSER, "Provider not configured or unavailable."))

        # ---------------------------------------------------------
        # Level 3: Keypad Input (Fallback 2)
        # ---------------------------------------------------------
        if active_keypad is not None:
            try:
                text = _invoke_provider(active_keypad)
                if text:
                    logger.info("Input successfully acquired via Keypad.")
                    return VoiceResult(
                        success=True,
                        text=text,
                        method=METHOD_KEYPAD,
                        error=None,
                    )
                failures.append((METHOD_KEYPAD, "Empty or whitespace input returned."))
            except Exception as exc:
                err_msg = sanitize_error(str(exc)) or type(exc).__name__
                logger.warning(f"Keypad input failed: {err_msg}")
                failures.append((METHOD_KEYPAD, err_msg))
        else:
            failures.append((METHOD_KEYPAD, "Provider not configured or unavailable."))

        # ---------------------------------------------------------
        # Level 4: All Providers Failed
        # ---------------------------------------------------------
        error_summary = "; ".join(f"{method}: {reason}" for method, reason in failures)
        logger.error(f"All fallback input providers failed: {error_summary}")
        return VoiceResult(
            success=False,
            text=None,
            method=METHOD_NONE,
            error=f"All input methods failed: [{error_summary}]",
        )


def get_fallback_input(
    audio_input: Any = None,
    sarvam_asr: Optional[Callable[..., Any]] = None,
    browser_speech: Optional[Callable[..., Any]] = None,
    keypad: Optional[Callable[..., Any]] = None,
) -> VoiceResult:
    """
    Convenience function to execute the fallback ladder in a single call.

    Args:
        audio_input: Audio file path, audio bytes, or context for Sarvam ASR.
        sarvam_asr: Sarvam ASR provider callable or instance.
        browser_speech: Browser Speech Recognition provider callable.
        keypad: Keypad provider callable.

    Returns:
        VoiceResult with outcome.
    """
    manager = VoiceFallbackManager(
        sarvam_asr=sarvam_asr,
        browser_speech=browser_speech,
        keypad=keypad,
    )
    return manager.get_input(audio_input=audio_input)
