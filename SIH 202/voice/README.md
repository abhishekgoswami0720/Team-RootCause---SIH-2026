# MandiQ Voice Module (SIH26032)

## Overview

The `voice` module handles speech input and output interfaces for the MandiQ platform. 

This repository contains:
- **Milestone 1**: **HINDI TEXT → SARVAM AI TTS → AUDIO FILE** (`voice/tts/`)
- **Milestone 2**: **HINDI AUDIO → SARVAM AI ASR → TRANSCRIPT TEXT** (`voice/asr/`)
- **Milestone 3**: **HINDI TRANSCRIPT → DETERMINISTIC NLU → STRUCTURED FIELDS** (`voice/nlu/`)
- **Milestone 4**: **FALLBACK INPUT LADDER → SARVAM → BROWSER → KEYPAD** (`voice/fallback/`)

---

## ⚠️ Architectural Guardrail

> **CRITICAL ARCHITECTURAL RULE:**
> 
> **The Voice module must NEVER directly make booking decisions or invoke an LLM.**
>
> 1. **Zero LLM**: Entity extraction is 100% deterministic, rule- and dictionary-based. No calls to Gemini, OpenAI, or external models.
> 2. **Zero Booking Decisions**: The Voice module serves exclusively as an audio/speech and entity extraction adapter. It receives text to synthesize, audio to transcribe, and transcripts to extract known entities from.
> 3. **Strict Ambiguity Safety**: If an utterance contains multiple distinct villages or crops, the NLU never guesses. It marks the field as ambiguous and missing.
> 4. **Backend Boundary**: Business validation, availability checks, slot allocation, and booking decisions belong strictly to the central Booking Engine / backend service.

---

## Prerequisites & Installation

1. **Python**: Python 3.9+ is recommended.
2. **Install Dependencies**:
   Install the required libraries (`requests` and `python-dotenv`):

   ```bash
   pip install -r voice/requirements.txt
   ```

---

## Configuration

The Sarvam API key is read **only from an environment variable** (`SARVAM_API_KEY`). It is never hardcoded or tracked in Git.

### Option A: Using a `.env` file (Recommended)

1. Create a `.env` file in the project root by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and insert your actual Sarvam API subscription key:
   ```env
   SARVAM_API_KEY=your_actual_sarvam_api_key_here
   ```

### Option B: Export in Terminal

- **Windows (PowerShell):**
  ```powershell
  $env:SARVAM_API_KEY="your_actual_sarvam_api_key_here"
  ```
- **Windows (CMD):**
  ```cmd
  set SARVAM_API_KEY=your_actual_sarvam_api_key_here
  ```
- **Linux / macOS:**
  ```bash
  export SARVAM_API_KEY="your_actual_sarvam_api_key_here"
  ```

---

## Milestone 1: Running the TTS Test

Execute the test script to synthesize the default Hindi prompt:

```bash
python voice/tts/test_tts.py
```

### Default Test Phrase:
> `"स्लॉट बुक करना है, तो एक दबाइए।"`

### Expected Output:
- The script contacts `https://api.sarvam.ai/text-to-speech` using the `bulbul:v3` model with `language_code="hi-IN"`.
- It saves a playable audio file to:
  ```
  voice/tts/output/slot_booking_prompt.wav
  ```

### Custom Synthesis:
You can also specify custom Hindi text or custom output files via arguments:

```bash
python voice/tts/test_tts.py --text "आपकी मंडी पर्ची तैयार है।" --output "output/mandi_slip.wav" --speaker "shubh"
```

---

## Milestone 2: Running the ASR (Speech-to-Text) Test

### Quick Test with an Audio File:
Execute the ASR test runner with your Hindi audio file:

```bash
python voice/asr/test_asr.py --audio voice/asr/samples/sample_farmer_input.wav
```

### Optional Convenience Pipeline Test (TTS -> ASR):
To verify end-to-end API connectivity using a synthesized sample:

```bash
python voice/asr/test_asr.py --generate-sample
```

> [!NOTE]
> TTS-synthesized audio verifies API connectivity and technical pipeline flow, but does NOT replace real human Hindi recordings for evaluating real-world farmer dialect or background noise accuracy.

### Testing with Real Human Voice:
1. Record a voice clip (under 30s) on your phone or PC in Hindi.
2. Save it to `voice/asr/samples/my_recording.wav` (or `.mp3`, `.m4a`).
3. Run:
   ```bash
   python voice/asr/test_asr.py --audio voice/asr/samples/my_recording.wav
   ```

---

## Milestone 3: Running the Deterministic NLU Demo

Run the CLI demo to see entity extraction across several real-world Hindi farmer utterances:

```bash
python voice/nlu/test_nlu.py
```

### Predictable Output Schema:
```json
{
  "success": true,
  "village": "Nangal",
  "crop": "Wheat",
  "missing_fields": [],
  "ambiguous_fields": []
}
```

### Configurable Dictionaries:
Dictionaries are stored externally in JSON:
- `voice/nlu/dictionaries/villages.json`: Maps Hindi/English variants to canonical village names (e.g. `"नांगल"` / `"nangal"` -> `"Nangal"`).
- `voice/nlu/dictionaries/crops.json`: Maps Hindi/English variants to canonical crop names (e.g. `"गेहूँ"` / `"गेहूं"` / `"wheat"` -> `"Wheat"`).

---

## Python API Usage

### 1. Deterministic NLU
```python
from voice.nlu import DeterministicNLU, parse_transcript

# Method A: Using the DeterministicNLU instance
nlu = DeterministicNLU()
result = nlu.parse("मेरा गाँव नांगल है और मेरी फसल गेहूँ है।")
print(result)
# Output:
# {'success': True, 'village': 'Nangal', 'crop': 'Wheat', 'missing_fields': [], 'ambiguous_fields': []}

# Method B: Convenience function
result = parse_transcript("गाँव गोवर्धन फसल सरसों")
print(result)
```

### 2. Speech-to-Text (ASR)
```python
from voice.asr import SarvamASR, transcribe_audio

asr = SarvamASR()
transcript = asr.transcribe("path/to/farmer_voice.wav")
print(f"Recognized: {transcript}")
```

### 3. Text-to-Speech (TTS)
```python
from voice.tts import SarvamTTS, synthesize_speech

tts = SarvamTTS()
output_path = tts.synthesize(
    text="स्लॉट बुक करना है, तो एक दबाइए।",
    output_filepath="voice/tts/output/prompt.wav"
)
print(f"Generated: {output_path}")
```

### 4. Voice Input Fallback Ladder
```python
from voice.fallback import VoiceFallbackManager, get_fallback_input

# Method A: Using VoiceFallbackManager with injected providers
manager = VoiceFallbackManager(
    sarvam_asr=lambda audio: "मेरा गाँव नांगल है",
    browser_speech=lambda: "मेरा गाँव नांगल है",
    keypad=lambda: "1",
)
result = manager.get_input(audio_input="path/to/farmer_voice.wav")
print(result)
# Output:
# VoiceResult(success=True, text='मेरा गाँव नांगल है', method='sarvam', error=None)

# Method B: Module-level convenience helper
result = get_fallback_input(
    sarvam_asr=None,
    browser_speech=lambda: "मेरा गाँव नांगल है",
    keypad=lambda: "1",
)
print(result.method)  # 'browser'
```

---

## 🗣️ Spoken Hindi Prompt Rules

When crafting Hindi spoken voice prompts for IVR / farmer interaction:
1. **Never use standalone digits or numeric glyphs**:
   - ❌ `"1 दबाएँ"` or `"2 दबाएँ"`
2. **Always use natural Hindi words for numbers**:
   - ✅ `"स्लॉट बुक करना है, तो एक दबाइए।"`
   - ✅ `"स्थिति जानने के लिए दो दबाइए।"`
3. **Number Word Mapping**:
   - 1 ➔ **एक**
   - 2 ➔ **दो**
   - 3 ➔ **तीन**
   - 4 ➔ **चार**

---

## Unit Testing

Run all unit tests across all milestones (TTS + ASR + NLU + Fallback Ladder):

```bash
# Standalone Fallback Runner:
python voice/fallback/test_fallback.py

# Unittest discovery:
python -m unittest discover -s tests -p "test_*.py" -v

# Pytest suite:
python -m pytest voice tests -v
```

---

## Error Handling

### Fallback Ladder Guarantees:
- **Zero API Key Leakage**: Sensitive credentials, tokens, and query parameters are automatically redacted from error summaries.
- **Fail-Soft Degradation**: Provider exceptions never crash the process; execution seamlessly proceeds through `Sarvam -> Browser -> Keypad`.
- **Clean Text Invariant**: Returned transcripts have all leading and trailing whitespace stripped.

### NLU Guarantees:
- **Zero Hallucination**: Only matches verified dictionary keys.
- **Type Safety**: Non-string inputs raise a clear `TypeError`.
- **Ambiguity Detection**: Multiple distinct matches populate `ambiguous_fields` and `missing_fields`, setting the entity to `None`.

### ASR Exceptions (`voice.asr`):
- **`MissingAPIKeyError`**: When `SARVAM_API_KEY` is not found or is still the placeholder.
- **`AudioFileNotFoundError`**: When the audio file path does not exist on disk.
- **`InvalidAudioFormatError`**: When the file format is unsupported.
- **`EmptyAudioError`**: When the audio file is 0 bytes.
- **`NetworkError`**: When network connectivity fails or requests time out.
- **`SarvamAPIError`**: When Sarvam AI returns an HTTP error.
- **`EmptyTranscriptError`**: When the API returns an empty transcript.

### TTS Exceptions (`voice.tts`):
- **`MissingAPIKeyError`**: When `SARVAM_API_KEY` is not configured.
- **`EmptyTextError`**: When input text is empty or blank.
- **`NetworkError`**: When network connectivity fails or requests time out.
- **`SarvamAPIError`**: When Sarvam AI returns an HTTP error.



