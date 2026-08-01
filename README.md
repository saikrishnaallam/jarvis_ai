# Jarvis Local Voice AI Assistant

A low-latency, fully local voice assistant featuring Voice Activity Detection (VAD), Speech-to-Text (STT), Language Model (LLM) orchestration with Tool Calling, and Text-to-Speech (TTS) playback.

## Features

- **🎙️ Real-time Audio & VAD**: Uses **Silero VAD** for sub-millisecond edge processing to detect speech onset and support dynamic barge-in (interruption).
- **👂 Speech-to-Text (STT)**: Powered by **faster-whisper** for fast, local English transcription.
- **🧠 LLM Orchestration & Tool Calling**: Utilizes Ollama's asynchronous client (`AsyncClient`) for real-time text generation (streaming sentence-by-sentence) and execution of local tools (such as fetching weather and controlling smart home devices).
- **🔊 Text-to-Speech (TTS) & Playback**: Powered by **Kokoro TTS** (high-quality American English voice `af_heart`) streaming audio to speakers via PortAudio (`sounddevice`).
- **🐳 Containerized Deployment**: Complete `Dockerfile` setup installing necessary system audio backends (ALSA, PortAudio, `espeak-ng`).

## Project Structure

```
jarvis_ai/
│
├── audio_engine.py      # Microphone capture, queue management, and Silero VAD analysis
├── stt_engine.py        # faster-whisper transcription running in background threads
├── llm_engine.py        # Ollama async chat orchestrator with custom Tool Calling logic
├── tts_engine.py        # Kokoro TTS synthesizer and sounddevice audio playback
├── main.py              # Central orchestrator gluing pipelines together asynchronously
│
├── requirements.txt     # Python package dependencies
└── Dockerfile           # Multi-step Docker deployment configuration
```

## Requirements & Setup

### Local Installation
Ensure you have the PortAudio and system dependencies installed:
- **macOS**: `brew install portaudio`
- **Linux (Ubuntu/Debian)**: `sudo apt-get install portaudio19-dev alsa-utils libasound2-dev espeak-ng`

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Ensure your local **Ollama** server is running, and pull the required model (default is `llama3.1`):
```bash
ollama pull llama3.1
```

### Running Locally
Run the orchestrator:
```bash
python main.py
```

## Docker Deployment

To build the local Docker image:
```bash
docker build -t local-voice-ai .
```

To run the container (exposing your host's audio hardware device and using host networking for Ollama connectivity):
```bash
docker run -it \
  --device /dev/snd \
  --network host \
  local-voice-ai
```
