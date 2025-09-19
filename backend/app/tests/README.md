# Speech Service Integration Tests

This folder contains integration tests for the speech service that process test audio files and output transcribed text.

## 📁 Folder Structure

```
tests/
├── integration/           # Integration test files
├── output/               # Test results and transcripts
├── test_audio/          # Place your test audio files here
├── unit/               # Unit test files
├── test_config.py      # Configuration for test files
└── README.md          # This file
```

## 🎤 How to Use

### 1. Add Test Audio Files

Place your test audio files in the `test_audio/` folder:
- `test_recording_1.m4a` (already there)
- Add more files as needed

### 2. Configure Test Files

Edit `test_config.py` to add your test files:

```python
TEST_FILES = [
    {
        "filename": "test_recording_1.m4a",
        "language": Language.ENGLISH,
        "description": "Basic English test recording"
    },
    {
        "filename": "my_test.m4a",
        "language": Language.SPANISH,
        "description": "My Spanish test"
    }
]
```

### 3. Run the Test

**Option A: Using pytest (Recommended)**
```bash
cd backend
poetry run pytest app/tests/integration/test_speech_service.py -v
```

**Option B: Run specific test**
```bash
poetry run pytest app/tests/integration/test_speech_service.py::test_single_audio_file -v
```

**Option C: Manual runner (for detailed output)**
```bash
python run_speech_test.py
```

### 4. Check Results

Results will be saved in the `output/` folder:
- `{filename}_transcript.txt` - The transcribed text
- `{filename}_metadata.json` - Detailed metadata
- `test_summary.txt` - Summary of all tests

## 🎯 Supported Audio Formats

- **m4a** - Apple audio format (Sound Recorder default)
- **mp3** - Standard audio format
- **wav** - Uncompressed audio
- **webm** - Web audio format
- **mp4** - MP4 audio container
- **mpeg** - MPEG audio

## 📊 Test Output

The test will:
1. ✅ Process each audio file through the speech service
2. 📝 Display transcribed text in the console
3. 💾 Save transcripts and metadata to files
4. 📊 Generate a summary report

## 🔧 Troubleshooting

### Common Issues:

1. **File not found**: Make sure audio files are in `test_audio/` folder
2. **API key missing**: Set `OPENAI_API_KEY` in your environment
3. **Import errors**: Run from the `backend/` directory

### Adding More Tests:

1. Add audio file to `test_audio/` folder
2. Add entry to `TEST_FILES` in `test_config.py`
3. Run the test again

## 📝 Example Output

```
🎤 Starting Speech Service Integration Tests
==================================================

🔍 Testing: test_recording_1.m4a
   Language: English
   Description: Basic English test recording
   📁 File size: 45,123 bytes
   🎯 Transcribing with English context...
   ✅ Success!
   📝 Transcript: I want a Big Mac with no cheese
   🎯 Confidence: 0.95
   💾 Saved transcript: test_recording_1_transcript.txt
   💾 Saved metadata: test_recording_1_metadata.json

✅ All tests completed! Check the output folder for results.
```
