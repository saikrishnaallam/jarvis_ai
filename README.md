# Jarvis Local Voice AI Assistant

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.11-blue)
![STT Engine](https://img.shields.io/badge/STT-faster--whisper%20(base.en)-blueviolet)
![LLM Model](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-orange)
![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20(af__heart)-ff69b4)
![License](https://img.shields.io/badge/License-MIT-green)

A low-latency, fully local voice assistant featuring Voice Activity Detection (VAD), Speech-to-Text (STT), Language Model (LLM) orchestration with Tool Calling, real-time Text-to-Speech (TTS) playback, and a floating Siri-like desktop orb widget.

---

## Features

- **🎙️ Real-time Audio & VAD**: Uses **Silero VAD** for sub-millisecond edge processing to detect speech onset and support dynamic barge-in (interruption).
- **👂 Speech-to-Text (STT)**: Powered by **faster-whisper** (`base.en` default, customizable via `--stt-model`) for fast, local English transcription.
- **🧠 LLM Orchestration & Tool Calling**: Utilizes Ollama (`llama3.2`) for real-time text generation (streaming sentence-by-sentence) and deterministic execution of local tools (Yahoo Finance stock quotes, DuckDuckGo web search, Google News RSS, Wikipedia lookup, weather, smart lights, and system time).
- **🔊 Text-to-Speech (TTS) & Playback**: Powered by **Kokoro TTS** (high-quality American English voice `af_heart`) with native Apple Silicon (`MPS`) and NVIDIA (`CUDA`) hardware acceleration.
- **🔮 Animated Desktop Widget**: A floating, borderless Tkinter orb that breathes when listening, sways when thinking, and scales dynamically with voice amplitude when speaking.
- **🛡️ Adaptive Echo Protection**: Dynamic acoustic gating and half-duplex options prevent the assistant from transcribing its own speaker output.
- **🐳 Containerized Deployment**: Complete `Dockerfile` setup installing necessary system audio backends (ALSA, PortAudio, `espeak-ng`).

---

## Project Structure

```
jarvis_ai/
│
├── audio_engine.py      # Microphone capture, queue management, and Silero VAD analysis
├── stt_engine.py        # faster-whisper transcription running in background threads
├── llm_engine.py        # Ollama async chat orchestrator with deterministic Tool Calling
├── tts_engine.py        # Kokoro TTS synthesizer and sounddevice audio playback
├── ui_engine.py         # Floating Siri-like desktop orb widget with dynamic state animations
├── main.py              # Central orchestrator gluing pipelines together asynchronously
├── test_jarvis.py       # Automated unit test suite for tool routing and memory management
│
├── requirements.txt     # Python package dependencies
├── Dockerfile           # Multi-step Docker deployment configuration
└── .gitignore           # Git ignore patterns for Python bytecode and OS files
```

---

## Requirements & Setup

### Local Installation
Ensure you have the PortAudio and system dependencies installed:

- **macOS (via Homebrew)**:
  ```bash
  brew install portaudio espeak-ng
  ```
- **Linux (Debian / Ubuntu)**:
  ```bash
  sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng
  ```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Ensure your local **Ollama** server is running, and pull the lightweight Llama 3.2 model:
```bash
ollama pull llama3.2
```

---

## Running Locally

### Start the full Assistant:
```bash
python main.py
```

### Barge-In Configuration Modes:
```bash
# Default Smart Mode (RMS volume-gated barge-in for speakers)
python main.py --barge-in smart

# Headphones Mode (Full-duplex open mic for headsets)
python main.py --barge-in headphones

# Disabled Mode (Traditional half-duplex mic lock during speech output)
python main.py --barge-in disabled
```

### Custom STT Model:
Choose from available Whisper model sizes (`tiny.en`, `base.en`, `small.en`, `medium.en`):
```bash
python main.py --stt-model small.en
```

### Standalone Desktop Widget Testing:
To test the floating desktop widget in isolation:
```bash
python ui_engine.py
```

### Running Unit Tests:
```bash
python -m unittest test_jarvis.py
```

---

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

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
