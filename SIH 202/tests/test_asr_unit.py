"""
Unit tests for MandiQ Voice ASR module with mocked Sarvam API responses.
These tests verify validation, error handling, and transcription logic without live API credentials.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from voice.asr.sarvam_asr import (
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


class TestSarvamASR(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test audio files
        self.test_dir = tempfile.TemporaryDirectory()
        self.valid_wav_path = Path(self.test_dir.name) / "test_valid.wav"
        # Write dummy wav header bytes (non-empty)
        with open(self.valid_wav_path, "wb") as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00data\x00\x00\x00\x00")

    def tearDown(self):
        self.test_dir.cleanup()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Verify that MissingAPIKeyError is raised when SARVAM_API_KEY is not set."""
        asr = SarvamASR(api_key=None)
        with self.assertRaises(MissingAPIKeyError):
            asr.transcribe(str(self.valid_wav_path))

    @patch.dict(os.environ, {"SARVAM_API_KEY": "your_sarvam_api_key_here"}, clear=True)
    def test_placeholder_api_key(self):
        """Verify that MissingAPIKeyError is raised when SARVAM_API_KEY is the template placeholder."""
        asr = SarvamASR()
        with self.assertRaises(MissingAPIKeyError):
            asr.transcribe(str(self.valid_wav_path))

    def test_audio_file_not_found(self):
        """Verify that AudioFileNotFoundError is raised for non-existent paths."""
        asr = SarvamASR(api_key="mock_key")
        non_existent_file = Path(self.test_dir.name) / "does_not_exist.wav"
        with self.assertRaises(AudioFileNotFoundError):
            asr.transcribe(str(non_existent_file))

    def test_invalid_audio_format(self):
        """Verify that InvalidAudioFormatError is raised for unsupported file extensions."""
        asr = SarvamASR(api_key="mock_key")
        invalid_file = Path(self.test_dir.name) / "document.pdf"
        with open(invalid_file, "wb") as f:
            f.write(b"%PDF-1.4 dummy content")

        with self.assertRaises(InvalidAudioFormatError):
            asr.transcribe(str(invalid_file))

    def test_empty_audio_file(self):
        """Verify that EmptyAudioError is raised for 0-byte audio files."""
        asr = SarvamASR(api_key="mock_key")
        empty_file = Path(self.test_dir.name) / "empty.wav"
        empty_file.touch()

        with self.assertRaises(EmptyAudioError):
            asr.transcribe(str(empty_file))

    @patch("requests.post")
    def test_network_connection_error(self, mock_post):
        """Verify that NetworkError is raised on connection failure."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        asr = SarvamASR(api_key="mock_key")

        with self.assertRaises(NetworkError):
            asr.transcribe(str(self.valid_wav_path))

    @patch("requests.post")
    def test_network_timeout_error(self, mock_post):
        """Verify that NetworkError is raised on request timeout."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        asr = SarvamASR(api_key="mock_key")

        with self.assertRaises(NetworkError):
            asr.transcribe(str(self.valid_wav_path))

    @patch("requests.post")
    def test_api_auth_error_403(self, mock_post):
        """Verify that SarvamAPIError is raised on 403 Forbidden / Invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "code": "invalid_api_key",
                "message": "Invalid API key provided",
            }
        }
        mock_post.return_value = mock_response

        asr = SarvamASR(api_key="invalid_mock_key")
        with self.assertRaises(SarvamAPIError) as ctx:
            asr.transcribe(str(self.valid_wav_path))

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Authentication / Permission failure", str(ctx.exception))

    @patch("requests.post")
    def test_api_server_error_500(self, mock_post):
        """Verify that SarvamAPIError is raised on 500 internal server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_post.return_value = mock_response

        asr = SarvamASR(api_key="mock_key")
        with self.assertRaises(SarvamAPIError) as ctx:
            asr.transcribe(str(self.valid_wav_path))

        self.assertEqual(ctx.exception.status_code, 500)

    @patch("requests.post")
    def test_empty_transcript_error(self, mock_post):
        """Verify that EmptyTranscriptError is raised when API returns an empty transcript."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "req-999",
            "transcript": "   \n\t  ",
            "language_code": "hi-IN",
        }
        mock_post.return_value = mock_response

        asr = SarvamASR(api_key="mock_key")
        with self.assertRaises(EmptyTranscriptError):
            asr.transcribe(str(self.valid_wav_path))

    @patch("requests.post")
    def test_successful_transcription(self, mock_post):
        """Verify that a successful API response returns the recognized Hindi text."""
        expected_hindi_text = "मेरा गाँव नांगल है और मेरी फसल गेहूँ है।"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "req-12345",
            "transcript": expected_hindi_text,
            "language_code": "hi-IN",
        }
        mock_post.return_value = mock_response

        asr = SarvamASR(api_key="valid_mock_key")
        result = asr.transcribe(
            audio_path=str(self.valid_wav_path),
            language_code="hi-IN",
            model="saaras:v3",
        )

        self.assertEqual(result, expected_hindi_text)

        # Verify call details
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["api-subscription-key"], "valid_mock_key")
        self.assertEqual(kwargs["data"]["model"], "saaras:v3")
        self.assertEqual(kwargs["data"]["language_code"], "hi-IN")
        self.assertIn("file", kwargs["files"])

    @patch("requests.post")
    def test_transcribe_audio_convenience_function(self, mock_post):
        """Verify the module-level transcribe_audio convenience function works."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transcript": "स्लॉट बुक करना है",
            "language_code": "hi-IN",
        }
        mock_post.return_value = mock_response

        result = transcribe_audio(
            audio_path=str(self.valid_wav_path),
            api_key="mock_key",
        )
        self.assertEqual(result, "स्लॉट बुक करना है")


if __name__ == "__main__":
    unittest.main()
