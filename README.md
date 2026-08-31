# 🎙️ Jarvis: Low-Latency Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=for-the-badge)](#)
[![Hardware Acceleration](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20NVIDIA%20CUDA-blue.svg?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Production DevOps & Operations Handbook**: A guide to deploying, containerizing, tuning, and operating Jarvis in Linux/macOS environments with GPU hardware acceleration and host audio device passthrough.

---

## 🐳 Containerized Deployment (Docker & Linux)

Jarvis provides containerized deployment capabilities exposing host ALSA/PulseAudio drivers (`/dev/snd`) to the container environment.

### 1. Build Container Image
```bash
docker build -t local-voice-ai .
```

### 2. Run Container with Host Sound Access
```bash
docker run -it --device /dev/snd --network host local-voice-ai
```

### 3. Linux Non-Root User Audio Permissions
Ensure your local system user belongs to the `audio` and `dialout` system groups to access ALSA sound devices:
```bash
sudo usermod -aG audio,dialout $USER
```

---

## 🤖 Systemd Daemon Service Setup

To run Jarvis as a background system service on Linux desktop environments, create a systemd unit file at `/etc/systemd/system/jarvis.service`:

```ini
[Unit]
Description=Jarvis Local Voice AI Assistant Service
After=sound.target network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/jarvis_ai
ExecStart=/home/your_username/jarvis_ai/venv/bin/python main.py --barge-in smart
Restart=on-failure
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical.target
```

### Enable & Manage Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis.service
sudo systemctl status jarvis.service
```

---

## 🚀 Hardware Acceleration & Resource Budgets

Jarvis automatically detects hardware acceleration upon startup for Apple Silicon and NVIDIA GPUs.

| Resource Component | Engine / Target | Minimum Budget | Recommended Budget |
| :--- | :--- | :--- | :--- |
| **VAD Engine** | Silero VAD v4 (CPU) | ~50 MB RAM | ~100 MB RAM |
| **STT Engine** | `faster-whisper` (`base.en`) | ~300 MB VRAM / RAM | ~500 MB (CTranslate2 `int8`/`fp16`) |
| **LLM Engine** | Ollama (`llama3.2`) | ~2.0 GB VRAM / RAM | ~4.0 GB (1024 context window) |
| **TTS Engine** | Kokoro v1.0 (`af_heart`) | ~1.2 GB VRAM / RAM | ~2.0 GB (MPS / CUDA) |
| **System Memory** | Combined Process Memory | **8 GB RAM** | **16 GB RAM (Dedicated GPU/Apple Silicon)** |

### Hardware Accelerator Autodetect Logic
- **Apple Silicon (M-Series)**: Autodetects Metal Performance Shaders (`torch.backends.mps.is_available()`) for PyTorch and Kokoro TTS.
- **NVIDIA GPUs**: Autodetects CUDA (`torch.cuda.is_available()`) and executes `faster-whisper` in `float16` precision.

---

## 🏎️ Audio Buffer Tuning & Latency Specs

```
+-----------------------------------------------------------------------------------------+
| Pipeline Stage      | Hardware / Strategy            | Buffer Size / Latency            |
+---------------------+--------------------------------+----------------------------------+
| Mic Capture         | PyAudio InputStream            | 512 samples @ 16kHz (32ms chunk) |
| VAD Endpointing     | Silero VAD v4                  | < 5 ms inference; 0.35s silence |
| STT Transcription   | faster-whisper (CTranslate2)   | 45 – 90 ms (vad_filter=False)    |
| LLM TTFT            | Ollama Llama 3.2 (Greedy)      | 70 – 120 ms (temp=0.0, ctx=1024) |
| TTS First Chunk     | Kokoro v1.0 (Sentence Stream)  | 30 – 50 ms per sentence buffer   |
| Playback Ring Buffer| PyAudio OutputStream           | 4096 frames @ 24kHz (< 10ms)     |
+---------------------+--------------------------------+----------------------------------+
| TOTAL FIRST SYLLABLE LATENCY                                 ~200 – 280 ms              |
+-----------------------------------------------------------------------------------------+
```

### Acoustic Echo Lock Formula
In `smart` barge-in mode, microphone input is locked during speech output if:
$$\text{Lock}_{\text{mic}} = A_{\text{mic}} < \max(0.08, A_{\text{speaker}} \times 1.5)$$
Where $A_{\text{mic}} = \max(|x_{\text{mic}}|)$ and $A_{\text{speaker}} = \max(|x_{\text{speaker}}|)$.

---

## ⚡ Quick Start & Standard Local Execution

### 1. Install Dependencies
```bash
# macOS (via Homebrew)
brew install portaudio espeak-ng

# Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

### 2. Pull Local Model (Ollama)
```bash
ollama pull llama3.2
```

### 3. Launch Assistant Flags
```bash
# Default Smart Mode (RMS volume-gated acoustic lock)
python main.py

# Headphones Mode (Full duplex open mic - recommended for headsets)
python main.py --barge-in headphones

# Disabled Mode (Half-duplex mic lock during speech output)
python main.py --barge-in disabled

# Select STT Model Size
python main.py --stt-model small.en

# Run Standalone UI Animation Test
python ui_engine.py

# Run Automated Test Suite
python -m unittest test_jarvis.py
```

---

## 📁 Codebase Directory Breakdown

* **[main.py](main.py)**: System orchestrator. Manages thread boundaries, signal handlers (`SIGINT`/`SIGTERM`), and Cocoa GUI.
* **[audio_engine.py](audio_engine.py)**: PyAudio mic stream handler, Silero VAD endpointing, RMS volume, and acoustic echo locks.
* **[stt_engine.py](stt_engine.py)**: Asynchronous `faster-whisper` transcription engine running CTranslate2 `int8`/`fp16` with VAD bypass.
* **[llm_engine.py](llm_engine.py)**: Ollama chat orchestrator with memory buffer pruning (20 messages max), sentence regex chunking, and tool routing.
* **[tts_engine.py](tts_engine.py)**: Kokoro TTS pipeline wrapper (MPS/CUDA accelerated) streaming audio segments to playback queues.
* **[ui_engine.py](ui_engine.py)**: Floating Tkinter desktop widget rendering visual states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
* **[test_jarvis.py](test_jarvis.py)**: Automated unit test suite covering tool keyword routing and memory management logic.
* **[Dockerfile](Dockerfile)**: Linux container configuration exposing host audio devices (`/dev/snd`).

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
