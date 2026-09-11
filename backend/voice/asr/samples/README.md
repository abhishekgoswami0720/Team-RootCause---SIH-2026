# ASR Audio Samples Directory

This directory contains audio samples for testing the MandiQ Voice Speech-to-Text (ASR) module.

## Supported Formats
Sarvam AI supports the following audio formats:
- `.wav` (recommended for uncompressed PCM, 16kHz)
- `.mp3`
- `.m4a` / `.mp4`
- `.aac`
- `.flac`
- `.ogg` / `.opus`
- `.webm`

> [!NOTE]
> **Audio Length Constraint**: The synchronous REST API endpoint handles recordings under 30 seconds (ideal for slot booking voice commands).

---

## How to Provide a Real Human Recording

1. **Record on Phone or Computer:**
   - Record a brief voice prompt in Hindi (e.g. using Windows Voice Recorder, iPhone Voice Memos, or WhatsApp voice note).
   - Sample Mandi farmer phrases:
     - *"मेरा गाँव नांगल है और मेरी फसल गेहूँ है।"*
     - *"मुझे 50 क्विंटल गेहूँ के लिए कल सुबह का स्लॉट चाहिए।"*
     - *"धान बेचने के लिए स्लॉट बुक करना है।"*
2. **Save to this Directory:**
   - Save or export the audio file as `voice/asr/samples/my_recording.wav` (or `.mp3`, `.m4a`).
3. **Run ASR Test:**
   ```bash
   python voice/asr/test_asr.py --audio voice/asr/samples/my_recording.wav
   ```

---

## Synthetic / Convenience Samples
To generate a synthetic Hindi audio sample using the Milestone 1 TTS module for round-trip pipeline connectivity testing:
```bash
python voice/asr/test_asr.py --generate-sample
```
> [!IMPORTANT]
> TTS-synthesized audio tests API connectivity and pipeline functionality, but does not represent real-world acoustic conditions (farmer dialect, background noise in Mandi, varied microphones). Field accuracy must be tested with human voice recordings.
