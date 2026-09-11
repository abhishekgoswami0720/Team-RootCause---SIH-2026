"""
Sarvam AI Speech-to-Text (ASR) integration for Hindi speech transcription.

MandiQ SIH26032 Project - Voice Module
Milestone 2: Hindi Audio -> Sarvam AI ASR -> Transcript Text
"""

import os
from pathlib import Path
from typing import Optional
import requests

# Try to load environment variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv

    # Search for .env file in current working directory and project root
    load_dotenv()
    project_root = Path(__file__).resolve().parent.parent.parent
    dotenv_path = project_root / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path)
except ImportError:
    pass


class ASRError(Exception):
    """Base exception for ASR operations."""
    pass


class MissingAPIKeyError(ASRError):
    """Raised when the SARVAM_API_KEY environment variable is not configured."""
    pass


class AudioFileNotFoundError(ASRError):
    """Raised when the specified audio file path does not exist."""
    pass


class InvalidAudioFormatError(ASRError):
    """Raised when the audio file extension is not supported by Sarvam ASR."""
    pass


class EmptyAudioError(ASRError):
    """Raised when the audio file is empty (0 bytes)."""
    pass


class NetworkError(ASRError):
    """Raised when a network or connection error occurs while calling the ASR API."""
    pass


class SarvamAPIError(ASRError):
    """Raised when the Sarvam AI API returns a non-200 error response."""

    def __init__(self, status_code: int, message: str, error_details: Optional[dict] = None):
        super().__init__(f"Sarvam API Error (HTTP {status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.error_details = error_details or {}


class EmptyTranscriptError(ASRError):
    """Raised when the API returns a response with an empty or whitespace-only transcript."""
    pass


class SarvamASR:
    """
    Client for transcribing speech via Sarvam AI's Speech-to-Text API.
    """

    API_ENDPOINT = "https://api.sarvam.ai/speech-to-text"
    DEFAULT_MODEL = "saaras:v3"
    DEFAULT_LANGUAGE_CODE = "hi-IN"
    DEFAULT_MODE = "transcribe"
    DEFAULT_TIMEOUT_SECONDS = 45

    SUPPORTED_EXTENSIONS = {
        ".wav",
        ".mp3",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".opus",
        ".webm",
        ".amr",
        ".wma",
        ".aiff",
    }

    # Map file extensions to MIME content-types
    MIME_TYPES = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".opus": "audio/opus",
        ".webm": "audio/webm",
        ".amr": "audio/amr",
        ".wma": "audio/x-ms-wma",
        ".aiff": "audio/aiff",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Sarvam ASR client.

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

    def _validate_audio_file(self, audio_path: Path) -> None:
        """Validate that the audio file exists, is non-empty, and has a supported extension."""
        if not audio_path.exists():
            raise AudioFileNotFoundError(f"Audio file not found at path: {audio_path}")

        if not audio_path.is_file():
            raise AudioFileNotFoundError(f"Path is not a regular file: {audio_path}")

        file_extension = audio_path.suffix.lower()
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            raise InvalidAudioFormatError(
                f"Unsupported audio format '{file_extension}'. Supported formats: {supported}"
            )

        if audio_path.stat().st_size == 0:
            raise EmptyAudioError(f"Audio file is empty (0 bytes): {audio_path}")

    def transcribe(
        self,
        audio_path: str,
        language_code: str = DEFAULT_LANGUAGE_CODE,
        model: str = DEFAULT_MODEL,
        mode: str = DEFAULT_MODE,
        with_timestamps: bool = False,
    ) -> str:
        """
        Transcribe an audio file into text using Sarvam AI Speech-to-Text.

        Args:
            audio_path: Path to the local audio file (WAV, MP3, M4A, etc.).
            language_code: Target BCP-47 language code (default: 'hi-IN').
            model: Model identifier (default: 'saaras:v3').
            mode: Transcription mode: 'transcribe', 'translate', 'verbatim',
                  'translit', or 'codemix' (default: 'transcribe').
            with_timestamps: Whether to request word-level timestamps (default: False).

        Returns:
            The recognized transcript as a Python string.

        Raises:
            MissingAPIKeyError: If SARVAM_API_KEY is unset or placeholder.
            AudioFileNotFoundError: If the audio file does not exist.
            InvalidAudioFormatError: If the audio file format is unsupported.
            EmptyAudioError: If the audio file size is 0 bytes.
            NetworkError: If connection fails or times out.
            SarvamAPIError: If the Sarvam API returns an HTTP error code.
            EmptyTranscriptError: If the API returns an empty transcript.
        """
        # 1. Validate API key
        api_key = self._validate_api_key()

        # 2. Validate audio file
        path_obj = Path(audio_path).resolve()
        self._validate_audio_file(path_obj)

        # 3. Prepare headers and multipart payload
        headers = {
            "api-subscription-key": api_key,
        }

        form_data = {
            "model": model,
            "mode": mode,
        }
        if language_code:
            form_data["language_code"] = language_code
        if with_timestamps:
            form_data["with_timestamps"] = "true"

        mime_type = self.MIME_TYPES.get(path_obj.suffix.lower(), "application/octet-stream")

        # 4. Open audio file and make POST request
        try:
            with open(path_obj, "rb") as audio_file:
                files = {
                    "file": (path_obj.name, audio_file, mime_type),
                }
                response = requests.post(
                    self.API_ENDPOINT,
                    headers=headers,
                    data=form_data,
                    files=files,
                    timeout=self.DEFAULT_TIMEOUT_SECONDS,
                )
        except requests.exceptions.Timeout as e:
            raise NetworkError(
                f"Request to Sarvam ASR timed out after {self.DEFAULT_TIMEOUT_SECONDS}s: {e}"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                f"Could not connect to Sarvam ASR API. Check your internet connection: {e}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error while calling Sarvam ASR API: {e}") from e

        # 5. Handle HTTP status code errors
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}"
            error_details = {}
            try:
                error_details = response.json()
                if "error" in error_details and isinstance(error_details["error"], dict):
                    error_msg = error_details["error"].get("message", error_msg)
                elif "message" in error_details:
                    error_msg = error_details["message"]
            except Exception:
                error_msg = response.text or error_msg

            if response.status_code in (401, 403):
                error_msg = f"Authentication / Permission failure: {error_msg}. Verify your SARVAM_API_KEY."

            raise SarvamAPIError(response.status_code, error_msg, error_details)

        # 6. Parse response JSON
        try:
            data = response.json()
        except Exception as e:
            raise SarvamAPIError(
                response.status_code, f"Failed to parse JSON response from Sarvam ASR: {e}"
            ) from e

        transcript = data.get("transcript")
        if transcript is None or not str(transcript).strip():
            raise EmptyTranscriptError(
                "Sarvam ASR returned an empty transcript. The audio may be silent or unintelligible."
            )

        return str(transcript).strip()


def transcribe_audio(
    audio_path: str,
    language_code: str = SarvamASR.DEFAULT_LANGUAGE_CODE,
    api_key: Optional[str] = None,
    model: str = SarvamASR.DEFAULT_MODEL,
    mode: str = SarvamASR.DEFAULT_MODE,
) -> str:
    """
    Convenience function to transcribe an audio file directly.

    Args:
        audio_path: Path to the local audio file.
        language_code: Target BCP-47 language code (default: 'hi-IN').
        api_key: Optional API key override (defaults to SARVAM_API_KEY env var).
        model: Sarvam model name (default: 'saaras:v3').
        mode: Recognition mode (default: 'transcribe').

    Returns:
        The recognized transcript string.
    """
    client = SarvamASR(api_key=api_key)
    return client.transcribe(
        audio_path=audio_path,
        language_code=language_code,
        model=model,
        mode=mode,
    )
