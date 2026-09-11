"""
Unit tests for MandiQ Voice Deterministic NLU module (Milestone 3).

Verifies dictionary-based entity extraction, text normalization,
predictable schema compliance, and ambiguity handling without LLM or external APIs.
"""

import unittest
from voice.nlu.deterministic_nlu import DeterministicNLU, parse_transcript


class TestDeterministicNLU(unittest.TestCase):

    def setUp(self):
        self.nlu = DeterministicNLU()

    def test_normal_hindi_sentence_both_entities(self):
        """Verify standard Hindi sentence correctly extracts both village and crop."""
        text = "मेरा गाँव नांगल है और मेरी फसल गेहूँ है।"
        result = self.nlu.parse(text)

        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertEqual(result["crop"], "Wheat")
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(result["ambiguous_fields"], [])

    def test_natural_sentence_variations(self):
        """Verify conversational sentence variations extract correctly."""
        text1 = "मैं नांगल गाँव से हूँ और गेहूँ लेकर आया हूँ।"
        result1 = self.nlu.parse(text1)
        self.assertTrue(result1["success"])
        self.assertEqual(result1["village"], "Nangal")
        self.assertEqual(result1["crop"], "Wheat")

        text2 = "गाँव नांगल, फसल गेहूँ।"
        result2 = self.nlu.parse(text2)
        self.assertTrue(result2["success"])
        self.assertEqual(result2["village"], "Nangal")
        self.assertEqual(result2["crop"], "Wheat")

    def test_village_only_sentence(self):
        """Verify handling when only village is mentioned."""
        text = "हम इंद्री गाँव के निवासी हैं।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertEqual(result["village"], "Indri")
        self.assertIsNone(result["crop"])
        self.assertEqual(result["missing_fields"], ["crop"])
        self.assertEqual(result["ambiguous_fields"], [])

    def test_crop_only_sentence(self):
        """Verify handling when only crop is mentioned."""
        text = "मेरी फसल सरसों है।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertIsNone(result["village"])
        self.assertEqual(result["crop"], "Mustard")
        self.assertEqual(result["missing_fields"], ["village"])
        self.assertEqual(result["ambiguous_fields"], [])

    def test_neither_entity_found(self):
        """Verify handling when neither entity is present."""
        text = "नमस्ते भाई साहब, आज मंडी किस समय बंद होगी?"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertIsNone(result["village"])
        self.assertIsNone(result["crop"])
        self.assertEqual(set(result["missing_fields"]), {"village", "crop"})
        self.assertEqual(result["ambiguous_fields"], [])

    def test_hindi_spelling_variation(self):
        """Verify spelling variations like 'गेहूं' vs 'गेहूँ' both map to Wheat."""
        result_gehun1 = self.nlu.parse("गाँव असंध फसल गेहूँ")
        self.assertTrue(result_gehun1["success"])
        self.assertEqual(result_gehun1["village"], "Assandh")
        self.assertEqual(result_gehun1["crop"], "Wheat")

        result_gehun2 = self.nlu.parse("गाँव असंध फसल गेहूं")
        self.assertTrue(result_gehun2["success"])
        self.assertEqual(result_gehun2["village"], "Assandh")
        self.assertEqual(result_gehun2["crop"], "Wheat")

    def test_english_crop_name(self):
        """Verify English crop names (e.g. 'wheat', 'mustard', 'pearl millet')."""
        result1 = self.nlu.parse("Village Nissing and crop is wheat.")
        self.assertTrue(result1["success"])
        self.assertEqual(result1["village"], "Nissing")
        self.assertEqual(result1["crop"], "Wheat")

        result2 = self.nlu.parse("Village Gharaunda and crop pearl millet.")
        self.assertTrue(result2["success"])
        self.assertEqual(result2["village"], "Gharaunda")
        self.assertEqual(result2["crop"], "Pearl Millet")

    def test_case_insensitive_latin(self):
        """Verify case-insensitive matching for English/Latin input."""
        result = self.nlu.parse("VILLAGE NANGAL, CROP MUSTARD")
        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertEqual(result["crop"], "Mustard")

    def test_extra_whitespace_and_tabs(self):
        """Verify whitespace normalization (extra spaces, tabs, newlines)."""
        text = "   मेरा    गाँव\t\tनांगल\n\nहै  और   मेरी फसल   बाजरा   है।   "
        result = self.nlu.parse(text)

        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertEqual(result["crop"], "Pearl Millet")

    def test_punctuation_handling(self):
        """Verify Devanagari and Latin punctuation characters are handled cleanly."""
        text = "«गाँव: नांगल!», [फसल: 'गेहूँ']... ठीक है?"
        result = self.nlu.parse(text)

        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertEqual(result["crop"], "Wheat")

    def test_unknown_village(self):
        """Verify that an unlisted village is never guessed or hallucinated."""
        text = "मेरा गाँव रामपुर है और मेरी फसल गेहूँ है।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertIsNone(result["village"])
        self.assertEqual(result["crop"], "Wheat")
        self.assertEqual(result["missing_fields"], ["village"])

    def test_unknown_crop(self):
        """Verify that an unlisted crop is never guessed or hallucinated."""
        text = "मेरा गाँव नांगल है और मेरी फसल सेब है।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertIsNone(result["crop"])
        self.assertEqual(result["missing_fields"], ["crop"])

    def test_multiple_ambiguous_villages(self):
        """Verify multiple distinct known villages trigger ambiguity without guessing."""
        text = "हम नांगल और इंद्री दोनों जगह से आते हैं, फसल गेहूँ है।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertIsNone(result["village"])
        self.assertEqual(result["crop"], "Wheat")
        self.assertIn("village", result["ambiguous_fields"])
        self.assertIn("village", result["missing_fields"])

    def test_multiple_ambiguous_crops(self):
        """Verify multiple distinct known crops trigger ambiguity without guessing."""
        text = "गाँव नांगल है और मेरी फसल गेहूँ तथा सरसों दोनों हैं।"
        result = self.nlu.parse(text)

        self.assertFalse(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertIsNone(result["crop"])
        self.assertIn("crop", result["ambiguous_fields"])
        self.assertIn("crop", result["missing_fields"])

    def test_same_canonical_entity_repeated_not_ambiguous(self):
        """Verify that repeating the same canonical entity (e.g. 'गेहूँ' and 'wheat') is not ambiguous."""
        text = "गाँव नांगल, मेरी फसल गेहूँ (wheat) है।"
        result = self.nlu.parse(text)

        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Nangal")
        self.assertEqual(result["crop"], "Wheat")
        self.assertEqual(result["ambiguous_fields"], [])

    def test_empty_input(self):
        """Verify empty string or whitespace-only input returns failure with all missing fields."""
        result1 = self.nlu.parse("")
        self.assertFalse(result1["success"])
        self.assertIsNone(result1["village"])
        self.assertIsNone(result1["crop"])
        self.assertEqual(set(result1["missing_fields"]), {"village", "crop"})

        result2 = self.nlu.parse("     \n\t  ")
        self.assertFalse(result2["success"])
        self.assertIsNone(result2["village"])
        self.assertIsNone(result2["crop"])
        self.assertEqual(set(result2["missing_fields"]), {"village", "crop"})

    def test_invalid_input_type(self):
        """Verify non-string input raises TypeError."""
        with self.assertRaises(TypeError):
            self.nlu.parse(None)

        with self.assertRaises(TypeError):
            self.nlu.parse(12345)

        with self.assertRaises(TypeError):
            self.nlu.parse(["नांगल", "गेहूँ"])

    def test_convenience_function_parse_transcript(self):
        """Verify parse_transcript convenience helper works identically."""
        result = parse_transcript("गाँव असंध फसल सरसों")
        self.assertTrue(result["success"])
        self.assertEqual(result["village"], "Assandh")
        self.assertEqual(result["crop"], "Mustard")


if __name__ == "__main__":
    unittest.main()
