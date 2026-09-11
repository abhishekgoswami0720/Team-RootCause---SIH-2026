"""
Unit tests for MandiQ Voice TTS module with mocked Sarvam API responses.
These tests verify error handling and synthesis logic without needing live API credentials.
"""

import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from voice.tts.sarvam_tts import (
    EmptyTextError,
    MissingAPIKeyError,
    NetworkError,
    SarvamAPIError,
    SarvamTTS,
    synthesize_speech,
)


class TestSarvamTTS(unittest.TestCase):

    def setUp(self):
        # Create a temp directory for test audio outputs
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_file = Path(self.test_dir.name) / "test_output.wav"

    def tearDown(self):
        self.test_dir.cleanup()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Verify that MissingAPIKeyError is raised when SARVAM_API_KEY is unset."""
        tts = SarvamTTS(api_key=None)
        with self.assertRaises(MissingAPIKeyError):
            tts.synthesize("स्लॉट बुक करना है, तो एक दबाइए।", str(self.output_file))

    def test_empty_text_error(self):
        """Verify that EmptyTextError is raised when text is empty or blank."""
        tts = SarvamTTS(api_key="mock_key")
        with self.assertRaises(EmptyTextError):
            tts.synthesize("", str(self.output_file))

        with self.assertRaises(EmptyTextError):
            tts.synthesize("   \n\t  ", str(self.output_file))

    @patch("requests.post")
    def test_network_connection_error(self, mock_post):
        """Verify that NetworkError is raised on connection failure."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        tts = SarvamTTS(api_key="mock_key")

        with self.assertRaises(NetworkError):
            tts.synthesize("स्लॉट बुक करना है", str(self.output_file))

    @patch("requests.post")
    def test_network_timeout_error(self, mock_post):
        """Verify that NetworkError is raised on request timeout."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        tts = SarvamTTS(api_key="mock_key")

        with self.assertRaises(NetworkError):
            tts.synthesize("स्लॉट बुक करना है", str(self.output_file))

    @patch("requests.post")
    def test_api_auth_error_403(self, mock_post):
        """Verify that SarvamAPIError is raised on 403 Forbidden / Invalid key."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "code": "invalid_api_key_error",
                "message": "Invalid API key provided",
            }
        }
        mock_post.return_value = mock_response

        tts = SarvamTTS(api_key="invalid_mock_key")
        with self.assertRaises(SarvamAPIError) as ctx:
            tts.synthesize("स्लॉट बुक करना है", str(self.output_file))

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Authentication / Permission failure", str(ctx.exception))

    @patch("requests.post")
    def test_successful_synthesis(self, mock_post):
        """Verify that a successful API response decodes audio and saves to file."""
        fake_pcm_wav = b"RIFF____WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b64_audio = base64.b64encode(fake_pcm_wav).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "req-12345",
            "audios": [b64_audio],
        }
        mock_post.return_value = mock_response

        tts = SarvamTTS(api_key="valid_mock_key")
        saved_path = tts.synthesize(
            text="स्लॉट बुक करना है, तो एक दबाइए।",
            output_filepath=str(self.output_file),
            speaker="shubh",
        )

        self.assertTrue(Path(saved_path).is_file())
        with open(saved_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, fake_pcm_wav)

        # Verify call payload
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["api-subscription-key"], "valid_mock_key")
        self.assertEqual(kwargs["json"]["text"], "स्लॉट बुक करना है, तो एक दबाइए।")
        self.assertEqual(kwargs["json"]["language_code"], "hi-IN")
        self.assertEqual(kwargs["json"]["model"], "bulbul:v3")
        self.assertEqual(kwargs["json"]["speaker"], "shubh")


if __name__ == "__main__":
    unittest.main()
