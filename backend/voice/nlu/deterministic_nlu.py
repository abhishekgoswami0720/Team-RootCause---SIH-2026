"""
Deterministic NLU (Natural Language Understanding) for MandiQ Voice Module.

Milestone 3: Hindi Transcript -> Deterministic Entity Extraction -> Structured Fields
Extracts known 'village' and 'crop' entities without any LLM or external APIs.
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class DeterministicNLU:
    """
    Deterministic rule- and dictionary-based entity extractor for Mandi voice transcripts.
    Converts recognized Hindi/Latin text into structured booking fields.
    """

    DEFAULT_VILLAGES_PATH = Path(__file__).resolve().parent / "dictionaries" / "villages.json"
    DEFAULT_CROPS_PATH = Path(__file__).resolve().parent / "dictionaries" / "crops.json"

    # Punctuation characters to remove/replace with spaces
    # Includes Devanagari danda (।), double danda (॥), quotes, brackets, and standard Latin punctuation
    PUNCTUATION_REGEX = re.compile(r'[।,॥.!?,;:\-"\'’‘“”()[\]{}<>/\\|@#$%^&*+=_~`]')

    def __init__(
        self,
        villages_path: Optional[str] = None,
        crops_path: Optional[str] = None,
    ):
        """
        Initialize the deterministic NLU engine by loading village and crop dictionaries.

        Args:
            villages_path: Optional path to villages.json dictionary.
            crops_path: Optional path to crops.json dictionary.
        """
        self.villages_path = Path(villages_path) if villages_path else self.DEFAULT_VILLAGES_PATH
        self.crops_path = Path(crops_path) if crops_path else self.DEFAULT_CROPS_PATH

        self.villages_dict: Dict[str, str] = self._load_dictionary(self.villages_path)
        self.crops_dict: Dict[str, str] = self._load_dictionary(self.crops_path)

    def _load_dictionary(self, path: Path) -> Dict[str, str]:
        """
        Load a JSON entity dictionary and normalize keys for fast matching.
        Keys are normalized with Unicode NFC and lowercased.
        """
        if not path.is_file():
            raise FileNotFoundError(f"Dictionary file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        normalized_dict = {}
        for key, canonical_value in raw_data.items():
            norm_key = self._normalize_token(key)
            if norm_key:
                normalized_dict[norm_key] = canonical_value

        return normalized_dict

    def _normalize_token(self, text: str) -> str:
        """Normalize a single token/phrase: Unicode NFC, lowercase, whitespace stripped."""
        text = unicodedata.normalize("NFC", text)
        return text.strip().lower()

    def normalize_text(self, text: str) -> str:
        """
        Full text normalization pipeline:
        1. Type checking (ensures string)
        2. Unicode NFC normalization
        3. Punctuation replaced with whitespace (to prevent accidental word concatenations)
        4. Lowercase conversion (for Latin text)
        5. Whitespace consolidation (multiple spaces/newlines/tabs to single space)
        """
        if not isinstance(text, str):
            raise TypeError(f"Input text must be a string, got {type(text).__name__}")

        # Unicode NFC normalization
        text = unicodedata.normalize("NFC", text)

        # Replace punctuation with spaces
        text = self.PUNCTUATION_REGEX.sub(" ", text)

        # Lowercase Latin characters
        text = text.lower()

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_entities_from_text(
        self, normalized_text: str, entity_dict: Dict[str, str]
    ) -> List[Tuple[str, str]]:
        """
        Find all dictionary entities present in normalized text.
        Matches longer multi-word keys first to avoid subphrase conflicts.
        Matches on word boundaries by checking space-padded text.

        Returns list of tuples: [(matched_key, canonical_name), ...]
        """
        if not normalized_text:
            return []

        # Pad with spaces so first and last words have bounding whitespace
        padded_text = f" {normalized_text} "

        # Sort keys by token count (descending), then character length (descending)
        sorted_keys = sorted(
            entity_dict.keys(),
            key=lambda k: (len(k.split()), len(k)),
            reverse=True,
        )

        matched: List[Tuple[str, str]] = []

        for key in sorted_keys:
            needle = f" {key} "
            if needle in padded_text:
                canonical = entity_dict[key]
                matched.append((key, canonical))

        return matched

    def parse(self, text: str) -> dict:
        """
        Parse an input Hindi/Latin text transcript and extract structured entities.

        Args:
            text: Recognized speech transcript.

        Returns:
            Dictionary following the predictable MandiQ schema:
            {
                "success": bool,
                "village": Optional[str],
                "crop": Optional[str],
                "missing_fields": List[str],
                "ambiguous_fields": List[str]
            }

        Raises:
            TypeError: If input is not a string.
        """
        normalized_text = self.normalize_text(text)

        # 1. Extract matches
        village_matches = self._extract_entities_from_text(normalized_text, self.villages_dict)
        crop_matches = self._extract_entities_from_text(normalized_text, self.crops_dict)

        # 2. Distinct canonical values
        distinct_villages: Set[str] = {canonical for _, canonical in village_matches}
        distinct_crops: Set[str] = {canonical for _, canonical in crop_matches}

        missing_fields: List[str] = []
        ambiguous_fields: List[str] = []

        # 3. Resolve village entity
        resolved_village: Optional[str] = None
        if len(distinct_villages) == 1:
            resolved_village = next(iter(distinct_villages))
        elif len(distinct_villages) > 1:
            ambiguous_fields.append("village")
            missing_fields.append("village")
        else:
            missing_fields.append("village")

        # 4. Resolve crop entity
        resolved_crop: Optional[str] = None
        if len(distinct_crops) == 1:
            resolved_crop = next(iter(distinct_crops))
        elif len(distinct_crops) > 1:
            ambiguous_fields.append("crop")
            missing_fields.append("crop")
        else:
            missing_fields.append("crop")

        # 5. Success is True only when all mandatory fields are resolved with zero ambiguity
        success = (len(missing_fields) == 0 and len(ambiguous_fields) == 0)

        return {
            "success": success,
            "village": resolved_village,
            "crop": resolved_crop,
            "missing_fields": missing_fields,
            "ambiguous_fields": ambiguous_fields,
        }


def parse_transcript(text: str) -> dict:
    """
    Convenience function to parse a transcript directly using default dictionaries.

    Args:
        text: Input transcript string.

    Returns:
        Structured entity dictionary.
    """
    nlu = DeterministicNLU()
    return nlu.parse(text)
