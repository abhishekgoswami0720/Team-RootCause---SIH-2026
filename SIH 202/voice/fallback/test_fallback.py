"""
Tests for Voice Input Fallback Ladder (MandiQ Voice Module).

Verifies the strict fallback order:
1. Sarvam ASR
2. Browser Speech Recognition
3. Keypad Input

All tests run without requiring live microphones, browsers, or external API calls.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Ensure UTF-8 output encoding for safe printing of Devanagari/Unicode in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path so the module can be run directly from any directory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from voice.fallback.fallback_manager import (
    METHOD_BROWSER,
    METHOD_KEYPAD,
    METHOD_NONE,
    METHOD_SARVAM,
    VoiceFallbackManager,
    VoiceResult,
    get_fallback_input,
    sanitize_error,
)


class TestVoiceFallbackLadder(unittest.TestCase):
    """
    Test suite for VoiceFallbackManager verifying all fallback ladder scenarios.
    """

    def test_01_sarvam_success(self):
        """
        Test 1: Sarvam ASR succeeds on primary attempt.
        Expected: success=True, method='sarvam', browser and keypad are NOT called.
        """
        sarvam_mock = MagicMock(return_value="मेरा गाँव नांगल है")
        browser_mock = MagicMock(return_value="मेरा गाँव नांगल है")
        keypad_mock = MagicMock(return_value="1")

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input(audio_input="test_audio.wav")

        self.assertTrue(result.success)
        self.assertEqual(result.text, "मेरा गाँव नांगल है")
        self.assertEqual(result.method, METHOD_SARVAM)
        self.assertIsNone(result.error)

        sarvam_mock.assert_called_once_with("test_audio.wav")
        browser_mock.assert_not_called()
        keypad_mock.assert_not_called()

    def test_02_sarvam_fails_browser_succeeds(self):
        """
        Test 2: Sarvam fails (raises Exception), browser speech succeeds.
        Expected: success=True, method='browser', keypad is NOT called.
        """
        sarvam_mock = MagicMock(side_effect=RuntimeError("Sarvam service unavailable"))
        browser_mock = MagicMock(return_value="मेरा गाँव नांगल है")
        keypad_mock = MagicMock(return_value="1")

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input(audio_input="test_audio.wav")

        self.assertTrue(result.success)
        self.assertEqual(result.text, "मेरा गाँव नांगल है")
        self.assertEqual(result.method, METHOD_BROWSER)
        self.assertIsNone(result.error)

        sarvam_mock.assert_called_once()
        browser_mock.assert_called_once()
        keypad_mock.assert_not_called()

    def test_03_sarvam_and_browser_fail_keypad_succeeds(self):
        """
        Test 3: Both Sarvam and browser speech fail, keypad succeeds.
        Expected: success=True, method='keypad', text matches keypad input.
        """
        sarvam_mock = MagicMock(side_effect=ConnectionError("Network timeout to Sarvam"))
        browser_mock = MagicMock(side_effect=Exception("Browser speech recognition not supported"))
        keypad_mock = MagicMock(return_value="1")

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input(audio_input="test_audio.wav")

        self.assertTrue(result.success)
        self.assertEqual(result.text, "1")
        self.assertEqual(result.method, METHOD_KEYPAD)
        self.assertIsNone(result.error)

        sarvam_mock.assert_called_once()
        browser_mock.assert_called_once()
        keypad_mock.assert_called_once()

    def test_04_all_three_fail(self):
        """
        Test 4: All three providers fail (exceptions or unconfigured).
        Expected: success=False, method='none', text=None, error contains explanation.
        """
        sarvam_mock = MagicMock(side_effect=Exception("Sarvam HTTP 500"))
        browser_mock = MagicMock(side_effect=Exception("Permission denied for microphone"))
        keypad_mock = MagicMock(side_effect=Exception("Keypad timeout"))

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input(audio_input="test_audio.wav")

        self.assertFalse(result.success)
        self.assertIsNone(result.text)
        self.assertEqual(result.method, METHOD_NONE)
        self.assertIsNotNone(result.error)
        self.assertIn("sarvam", result.error)
        self.assertIn("browser", result.error)
        self.assertIn("keypad", result.error)

        sarvam_mock.assert_called_once()
        browser_mock.assert_called_once()
        keypad_mock.assert_called_once()

    def test_05_empty_sarvam_transcript_falls_back_to_browser(self):
        """
        Test 5: Sarvam returns whitespace or empty string.
        Must be treated as failure and fall back to browser.
        """
        sarvam_mock = MagicMock(return_value="   \t\n  ")
        browser_mock = MagicMock(return_value="गाँव नांगल फसल गेहूँ")
        keypad_mock = MagicMock(return_value="1")

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input()

        self.assertTrue(result.success)
        self.assertEqual(result.text, "गाँव नांगल फसल गेहूँ")
        self.assertEqual(result.method, METHOD_BROWSER)

        sarvam_mock.assert_called_once()
        browser_mock.assert_called_once()
        keypad_mock.assert_not_called()

    def test_06_empty_browser_transcript_falls_back_to_keypad(self):
        """
        Test 6: Sarvam fails and browser returns empty text.
        Must fall through to keypad.
        """
        sarvam_mock = MagicMock(side_effect=ValueError("Invalid audio"))
        browser_mock = MagicMock(return_value="")
        keypad_mock = MagicMock(return_value="2")

        manager = VoiceFallbackManager(
            sarvam_asr=sarvam_mock,
            browser_speech=browser_mock,
            keypad=keypad_mock,
        )

        result = manager.get_input()

        self.assertTrue(result.success)
        self.assertEqual(result.text, "2")
        self.assertEqual(result.method, METHOD_KEYPAD)

        sarvam_mock.assert_called_once()
        browser_mock.assert_called_once()
        keypad_mock.assert_called_once()

    def test_07_verify_strict_fallback_order_and_short_circuit(self):
        """
        Test 7: Verify execution order is strictly Sarvam -> Browser -> Keypad,
        and that later providers are never called once an earlier provider succeeds.
        """
        call_order = []

        def mock_sarvam(audio=None):
            call_order.append("sarvam")
            return None  # empty/fail

        def mock_browser():
            call_order.append("browser")
            return "मेरा गाँव नांगल है"  # succeeds

        def mock_keypad():
            call_order.append("keypad")
            return "1"

        manager = VoiceFallbackManager(
            sarvam_asr=mock_sarvam,
            browser_speech=mock_browser,
            keypad=mock_keypad,
        )

        result = manager.get_input()

        self.assertEqual(call_order, ["sarvam", "browser"])
        self.assertEqual(result.method, METHOD_BROWSER)
        self.assertNotIn("keypad", call_order)

    def test_08_text_whitespace_stripping(self):
        """
        Verify that leading and trailing whitespace are stripped across all providers.
        """
        manager = VoiceFallbackManager(
            sarvam_asr=lambda audio=None: "\n  मेरा गाँव नांगल है \t "
        )
        result = manager.get_input()
        self.assertEqual(result.text, "मेरा गाँव नांगल है")

        manager_keypad = VoiceFallbackManager(
            sarvam_asr=None,
            browser_speech=None,
            keypad=lambda: "  1   \n",
        )
        result_keypad = manager_keypad.get_input()
        self.assertEqual(result_keypad.text, "1")

    def test_09_no_api_key_leak_in_error_messages(self):
        """
        Verify that error messages sanitize sensitive API keys or tokens.
        """
        secret_key = "sk_live_secret_key_1234567890abcdef"
        raw_error = f"Failed contacting https://api.sarvam.ai with api_key={secret_key} 401 Unauthorized"
        sanitized = sanitize_error(raw_error)

        self.assertNotIn(secret_key, sanitized)
        self.assertIn("api_key=***", sanitized)

        # Also test via manager
        failing_sarvam = MagicMock(side_effect=RuntimeError(f"Bad request with api-key={secret_key}"))
        manager = VoiceFallbackManager(sarvam_asr=failing_sarvam)
        result = manager.get_input()

        self.assertFalse(result.success)
        self.assertNotIn(secret_key, result.error)

    def test_10_convenience_function_get_fallback_input(self):
        """
        Verify module-level get_fallback_input works correctly.
        """
        result = get_fallback_input(
            sarvam_asr=lambda audio=None: "मेरा गाँव नांगल है",
            browser_speech=lambda: "browser text",
            keypad=lambda: "1",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.text, "मेरा गाँव नांगल है")
        self.assertEqual(result.method, METHOD_SARVAM)

    def test_11_transcribe_object_support(self):
        """
        Verify support for objects with a .transcribe() method (like SarvamASR).
        """
        class MockASRObject:
            def transcribe(self, audio_path):
                return f"Transcribed {audio_path}"

        manager = VoiceFallbackManager(sarvam_asr=MockASRObject())
        result = manager.get_input(audio_input="sample.wav")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Transcribed sample.wav")
        self.assertEqual(result.method, METHOD_SARVAM)

    def test_12_keypad_numeric_integer_return(self):
        """
        Verify that keypad returning integer 1 converts safely to string '1'.
        """
        manager = VoiceFallbackManager(keypad=lambda: 1)
        result = manager.get_input()
        self.assertTrue(result.success)
        self.assertEqual(result.text, "1")
        self.assertEqual(result.method, METHOD_KEYPAD)


def run_tests():
    """Run tests directly with formatted output."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVoiceFallbackLadder)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
