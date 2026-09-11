"""
Sarvam AI Text-to-Speech (TTS) integration for Hindi speech synthesis.

MandiQ SIH26032 Project - Voice Module
Milestone 1: Hindi Text -> Sarvam AI TTS -> Audio File
"""

import base64
import os
from pathlib import Path
from typing import Optional
import requests

# Try to load environment variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv

    # Search for .env file in current working directory and project root
    load_dotenv()
    # Also attempt loading from project root explicitly if exists
    project_root = Path(__file__).resolve().parent.parent.parent
    dotenv_path = project_root / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path)
except ImportError:
    pass


class TTSError(Exception):
    """Base exception for TTS operations."""
    pass


class MissingAPIKeyError(TTSError):
    """Raised when the SARVAM_API_KEY environment variable is not configured."""
    pass


class EmptyTextError(TTSError):
    """Raised when the input text is empty or contains only whitespace."""
    pass


class NetworkError(TTSError):
    """Raised when a network or connection error occurs while calling the TTS API."""
    pass


class SarvamAPIError(TTSError):
    """Raised when the Sarvam AI API returns a non-200 error response."""

    def __init__(self, status_code: int, message: str, error_details: Optional[dict] = None):
        super().__init__(f"Sarvam API Error (HTTP {status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.error_details = error_details or {}


class SarvamTTS:
    """
    Client for synthesizing speech via Sarvam AI's Text-to-Speech API.
    """

    API_ENDPOINT = "https://api.sarvam.ai/text-to-speech"
    DEFAULT_MODEL = "bulbul:v3"
    DEFAULT_LANGUAGE_CODE = "hi-IN"
    DEFAULT_SPEAKER = "shubh"
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Sarvam TTS client.

        Args:
            api_key: Optional API key. If not provided, reads exclusively
                     from the SARVAM_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")

    def _validate_api_key(self) -> str:
        """Ensure a valid API key is present."""
        if not self.api_key or not self.api_key.strip():
            raise MissingAPIKeyError(
                "Sarvam API key is missing. Please set the 'SARVAM_API_KEY' environment variable "
                "or define it in your '.env' file. See '.env.example' for reference."
            )
        key = self.api_key.strip()
        if key == "your_sarvam_api_key_here":
            raise MissingAPIKeyError(
                "SARVAM_API_KEY is still set to the placeholder 'your_sarvam_api_key_here'. "
                "Please replace it with your actual Sarvam API key in the '.env' file."
            )
        return key

    def synthesize(
        self,
        text: str,
        output_filepath: str = "output.wav",
        language_code: str = DEFAULT_LANGUAGE_CODE,
        speaker: str = DEFAULT_SPEAKER,
        model: str = DEFAULT_MODEL,
        pace: float = 1.0,
        temperature: float = 0.6,
    ) -> str:
        """
        Synthesize text into speech and save as an audio file.

        Args:
            text: Input Hindi (or Indic) text to synthesize.
            output_filepath: Destination file path for the generated audio (default: 'output.wav').
            language_code: Target BCP-47 language code (default: 'hi-IN').
            speaker: Speaker voice name (default: 'shubh' for bulbul:v3).
            model: Model identifier (default: 'bulbul:v3').
            pace: Speech pace between 0.5 and 2.0 (default: 1.0).
            temperature: Randomness/expressiveness between 0.01 and 2.0 (default: 0.6).

        Returns:
            The resolved absolute path of the saved audio file.

        Raises:
            MissingAPIKeyError: If SARVAM_API_KEY is not set.
            EmptyTextError: If text is empty or only whitespace.
            NetworkError: If connection/network fails or times out.
            SarvamAPIError: If the Sarvam API returns an HTTP error status.
        """
        # 1. Validate API key
        api_key = self._validate_api_key()

        # 2. Validate input text
        if not text or not text.strip():
            raise EmptyTextError("Cannot synthesize speech: input text is empty.")

        cleaned_text = text.strip()

        # 3. Prepare headers and payload per official Sarvam documentation
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": cleaned_text,
            "language_code": language_code,
            "model": model,
            "speaker": speaker,
            "pace": pace,
            "temperature": temperature,
        }

        # 4. Make HTTP request to Sarvam TTS endpoint
        try:
            response = requests.post(
                self.API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request to Sarvam TTS timed out after {self.DEFAULT_TIMEOUT_SECONDS}s: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Could not connect to Sarvam TTS API. Check your internet connection: {e}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error while calling Sarvam TTS API: {e}") from e

        # 5. Handle HTTP status code errors
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}"
            error_details = {}
            try:
                error_details = response.json()
                # Sarvam returns {"error": {"code": "...", "message": "..."}}
                if "error" in error_details and isinstance(error_details["error"], dict):
                    error_msg = error_details["error"].get("message", error_msg)
                elif "message" in error_details:
                    error_msg = error_details["message"]
            except Exception:
                error_msg = response.text or error_msg

            if response.status_code == 403:
                error_msg = f"Authentication / Permission failure: {error_msg}. Verify your SARVAM_API_KEY."

            raise SarvamAPIError(response.status_code, error_msg, error_details)

        # 6. Parse response JSON
        try:
            data = response.json()
        except Exception as e:
            raise SarvamAPIError(response.status_code, f"Failed to parse JSON response from Sarvam API: {e}") from e

        audios = data.get("audios")
        if not audios or not isinstance(audios, list) or len(audios) == 0:
            raise SarvamAPIError(response.status_code, "Sarvam API response did not contain any audio data.", data)

        # 7. Decode base64 audio and save to disk
        audio_base64 = audios[0]
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            raise SarvamAPIError(response.status_code, f"Failed to decode base64 audio string: {e}") from e

        output_path = Path(output_filepath).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return str(output_path)


def synthesize_speech(
    text: str,
    output_filepath: str = "output.wav",
    api_key: Optional[str] = None,
    speaker: str = SarvamTTS.DEFAULT_SPEAKER,
) -> str:
    """
    Convenience function to synthesize speech directly.

    Args:
        text: Hindi text to synthesize.
        output_filepath: Target file path for the .wav output.
        api_key: Optional API key override (defaults to SARVAM_API_KEY env var).
        speaker: Voice speaker name (default: 'shubh').

    Returns:
        Path to the saved audio file.
    """
    client = SarvamTTS(api_key=api_key)
    return client.synthesize(text=text, output_filepath=output_filepath, speaker=speaker)
