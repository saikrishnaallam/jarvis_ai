<div align="center">

<img src="avatar.png" width="160" alt="Jarvis Desktop Orb" />

# 🎙️ JARVIS: The Edge-Native Voice AI

### Ultra-Low Latency • 100% Private • Local-First Intelligence

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper%20(base.en)-8A2BE2.svg?style=for-the-badge)](#)
[![LLM Brain](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2%203B)-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20(af__heart)-FF69B4.svg?style=for-the-badge)](#)
[![Hardware Acceleration](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20CUDA-blue.svg?style=for-the-badge)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg?style=for-the-badge)](#)
[![Privacy Guarantee](https://img.shields.io/badge/Privacy-100%25%20On--Device-success.svg?style=for-the-badge)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](#)

<p align="center">
  <b>Jarvis is an edge-native voice intelligence platform designed for seamless spoken interaction on consumer hardware.</b><br>
  No cloud round-trips, no API fees, and zero telemetry.
</p>

[Quick Start](#-quick-start-in-3-steps) •
[Architecture](#-system-architecture) •
[Latency Breakdown](#-subsystem-latency-breakdown) •
[Tool Calling](#-live-web--tool-integrations) •
[Audio DSP](#-audio-dsp--echo-cancellation) •
[Desktop Orb UI](#-floating-desktop-orb-ui) •
[CLI & Flags](#-cli-usage--runtime-flags) •
[Codebase Map](#-project-structure--file-map) •
[Docker](#-docker-deployment) •
[Troubleshooting](#-troubleshooting--faq)

---

</div>

## 🌟 Core Philosophies & Highlights

1. **⚡ First-Syllable Speed (<280ms)**: Streaming sentence-level audio synthesis starts playing speech segments while the local LLM is still generating subsequent tokens.
2. **🔒 Absolute Edge Privacy**: Microphone ingestion, voice activity detection, speech recognition, language modeling, and voice generation execute 100% locally.
3. **🛠️ Deterministic Tool Routing**: Fast, keyword-gated function execution connects the assistant to live stock quotes (Yahoo Finance), web search (DuckDuckGo), real-time global news (Google News RSS), weather, and system utilities without LLM hallucinations.
4. **🔮 Siri-Style Desktop Orb**: Floating borderless desktop avatar with smooth breathing, listening, thinking, and speaking animations driven by real-time voice amplitude.
5. **🛡️ Smart Barge-In & Acoustic Shielding**: Dynamic acoustic energy gating ($\text{Lock}_{\text{mic}}$) eliminates speaker feedback loops while allowing instant conversational interruption.
6. **🍏 Hardware Acceleration**: Native Apple Silicon Metal Performance Shaders (`MPS`) and NVIDIA `CUDA` acceleration auto-detected on startup.

---

## ⚡ Quick Start in 3 Steps

### Step 1: Install System Audio Drivers & Python Packages

#### macOS (Homebrew)
```bash
# Install audio engine dependencies
brew install portaudio espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

#### Linux (Debian / Ubuntu / Pop!_OS)
```bash
# Install ALSA and PortAudio headers
sudo apt-get update && sudo apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

### Step 2: Pull Local LLM Model (Ollama)
Ensure [Ollama](https://ollama.com/) is installed and running, then pull the lightweight Llama 3.2 model:
```bash
ollama pull llama3.2
```

### Step 3: Launch Jarvis!
```bash
python main.py
```

---

## 📐 System Architecture

Jarvis orchestrates five dedicated thread loops communicating via thread-safe asynchronous queues:

```mermaid
flowchart TB
    subgraph Threads ["Thread Concurrency Isolation"]
        T1["🧵 Main GUI Thread\n(Tkinter root loop, Cocoa canvas, POSIX signal handlers)"]
        T2["🧵 Asyncio Event Loop Daemon\n(Task orchestrator, queue consumers, signal dispatch)"]
        T3["🧵 SoundDevice Mic Stream\n(16kHz float32 non-blocking chunk producer)"]
        T4["🧵 SoundDevice Speaker Stream\n(24kHz float32 audio consumer & ring buffer)"]
        T5["🧵 Neural Synthesis Worker\n(Kokoro PyTorch MPS/CUDA generator thread)"]
    end

    subgraph DataPipeline ["Data Stream & Processing Pipeline"]
        Mic[🎙️ Microphone Input] -->|16kHz PCM| T3
        T3 -->|loop.call_soon_threadsafe| Q1[(asyncio.Queue\nraw_audio_queue)]
        Q1 --> VAD[⚡ Silero VAD Edge Engine\nEndpointing (0.35s silence decay)]
        
        VAD -->|Speech Buffers| Q2[(asyncio.Queue\nspeech_buffer_queue)]
        Q2 --> STT[👂 faster-whisper STT\nCTranslate2 Greedy Decoding]
        
        STT -->|Transcribed Text| Q3[(asyncio.Queue\ntext_queue)]
        Q3 --> LLM[🧠 Ollama Llama 3.2\ntemperature=0.0, num_ctx=1024]
        
        LLM <-->|Deterministic Routing| Tools[🛠️ Local Python Tools\n(Stocks, DDG, News, Weather)]
        LLM -->|Regex Sentence Chunks| Q4[(asyncio.Queue\ntts_queue)]
        
        Q4 --> T5
        T5 -->|loop.call_soon_threadsafe| Q5[(asyncio.Queue\naudio_playback_queue)]
        Q5 --> T4
        T4 -->|24kHz float32 PCM| Spk[📢 Hardware Speakers]
        T4 -.->|RMS Amplitude| Orb[🔮 Desktop Orb Avatar]
        T4 -.->|Adaptive Echo Threshold| VAD
    end
```

---

## ⏱️ Subsystem Latency Breakdown

Pipelined streaming eliminates conversational turn-taking latency. Audio begins playback on the first completed clause:

| Subsystem | Model / Library | Engine Target | Strategy | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | `sounddevice` | Host CPU | 32ms frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Edge chunk scoring; `0.35s` silence decay | `< 5 ms` |
| **Speech Transcription** | `faster-whisper` (`base.en`) | CTranslate2 | Greedy decoding, `vad_filter=False` | `60 - 90 ms` |
| **First Token (TTFT)** | Ollama (`llama3.2:3b`) | Apple MPS / CUDA | `temperature=0.0`, `num_ctx=1024` | `40 - 70 ms` |
| **Sentence Chunking** | Python Regex Stream | Host CPU | Splitting on `.` `!` `?` `\n` boundaries | `< 1 ms` |
| **Speech Synthesis** | Kokoro TTS (`af_heart`) | PyTorch MPS / CUDA | Clause-level generation | `50 - 80 ms` |
| **Speaker Output** | Non-blocking callback | Host CPU | 24kHz float32 ring buffer | `< 5 ms` |
| **Total Voice Loop** | **Jarvis End-to-End** | **Hardware Accelerated** | **First audible spoken syllable** | **~200 - 280 ms** |

---

## 🛠️ Live Web & Tool Integrations

Jarvis pre-filters queries deterministically to invoke real-time tools without LLM hallucinations:

| Integration | Example Spoken Query | Invoked Tool Function | Data Provider |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `NVDA`, `MSFT`) |
| **🌐 Live Web Search** | *"Who won the game yesterday?"* | `search_web` | DuckDuckGo Search API |
| **🏛️ Political Leaders** | *"Who is the prime minister of the UK?"* | `search_web` | Real-time Search Engine |
| **📰 Breaking News** | *"What's the latest breaking news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 Encyclopedia** | *"Tell me about Quantum Entanglement"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Seattle?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home** | *"Turn on the desk lamp"* | `toggle_smart_lights` | Local HomeAssistant REST API |
| **⏰ System Clock** | *"What time is it right now?"* | `get_current_time` | System Clock & Timezones |

---

## 🎛️ Audio DSP & Echo Cancellation

### Dynamic Acoustic Energy Gating
To prevent the assistant's microphone from picking up and transcribing its own speaker output, `audio_engine.py` dynamically computes an energy rejection threshold:

$$\text{Lock}_{\text{mic}} = A_{\text{mic}} < \max\left(0.08,\; 1.5 \times A_{\text{speaker}}\right)$$

* **Spillover Rejection**: When Jarvis is speaking loudly, $A_{\text{speaker}}$ dynamically scales the mic threshold to ignore room reverberations.
* **Smart Barge-In**: When the user speaks firmly ($A_{\text{mic}} \ge 1.5 \times A_{\text{speaker}}$), Jarvis cuts audio playback instantly and transfers state to listening.
* **Console Cut-Off**: Pressing `<Enter>` in the terminal immediately triggers an interruption event.

```bash
# Smart Mode (Default: volume-gated interrupt for speakers)
python main.py --barge-in smart

# Headphones Mode (Full-duplex open mic; zero echo lock)
python main.py --barge-in headphones

# Disabled Mode (Traditional half-duplex walkie-talkie mode)
python main.py --barge-in disabled
```

---

## 🔮 Floating Desktop Orb UI

The floating desktop widget in `ui_engine.py` provides real-time ambient status feedback:

| Visual State | Color Signature | Animation Dynamic |
| :--- | :--- | :--- |
| **Idle / Listening** | Cyan Glow (`#06b6d4`) | Gentle breathing sine-wave oscillation (period: 2.0s) |
| **Thinking** | Shifting Purple (`#a855f7`) | Horizontal sway & pulsing compression wave |
| **Speaking** | Electric Blue (`#3b82f6`) | Real-time dynamic expansion scaled to TTS audio RMS amplitude |

### macOS Cocoa Transparency Fix
Standard Tkinter transparent canvases on macOS composite alpha channels against transparent windows, resulting in dark jagged borders. Jarvis resolves this by rendering a dynamic canvas background oval (`canvas.create_oval`) matching the moving avatar's exact scale and coordinates. Click and drag the orb anywhere on your screen.

---

## 🚀 CLI Usage & Runtime Flags

```bash
# Launch with default settings (smart barge-in, base.en STT)
python main.py

# Select custom Whisper model (tiny.en, base.en, small.en, medium.en)
python main.py --stt-model small.en

# Launch with headphone full-duplex open-mic mode
python main.py --barge-in headphones

# Run desktop widget standalone (visual animation testing)
python ui_engine.py

# Run unit tests
python -m unittest test_jarvis.py
```

---

## 🐳 Docker Deployment

To deploy Jarvis inside a Linux container with host audio device access:

```bash
# Build Docker image
docker build -t local-voice-ai .

# Run container with host audio device and host network
docker run -it --device /dev/snd --network host local-voice-ai
```

---

## 📁 Project Structure & File Map

| File | Purpose | Subsystem Layer |
| :--- | :--- | :--- |
| [main.py](main.py) | Application entry point, thread coordinator, signal handling | Core Orchestrator |
| [audio_engine.py](audio_engine.py) | SoundDevice mic streams, Silero VAD endpointing, and adaptive echo gating | DSP & Audio In |
| [stt_engine.py](stt_engine.py) | Async Speech-to-Text transcription powered by `faster-whisper` | Speech Recognition |
| [llm_engine.py](llm_engine.py) | Ollama Llama 3.2 integration, memory buffer, and deterministic tool router | Language & Reasoning |
| [tts_engine.py](tts_engine.py) | Sentence-streaming speech synthesis using Kokoro TTS (MPS/CUDA) | Voice Synthesis |
| [ui_engine.py](ui_engine.py) | Floating Tkinter desktop orb widget with dynamic state animations | User Interface |
| [avatar.png](avatar.png) | High-resolution graphical asset for desktop orb avatar scaling | UI Asset |
| [test_jarvis.py](test_jarvis.py) | Unit test suite for deterministic tool routing and memory management | Verification |
| [Dockerfile](Dockerfile) | Production Linux container configuration with host ALSA device access | Deployment |
| [requirements.txt](requirements.txt) | Pinned Python package dependencies | Environment |
| [.gitignore](.gitignore) | Git ignore rules for bytecode, virtual environments, and OS files | Hygiene |

---

## 💻 Hardware Requirements

| Specification | Minimum | Recommended (Optimal Experience) |
| :--- | :--- | :--- |
| **Processor** | Quad-core x86_64 or Apple Silicon M1 | Apple Silicon M2/M3/M4 or NVIDIA RTX 3060+ |
| **RAM** | 8 GB System Memory | 16 GB+ Unified Memory / System RAM |
| **Acceleration** | CPU fallback mode | Apple Metal (`MPS`) or NVIDIA `CUDA` |
| **Storage** | 5 GB free disk space | 15 GB free disk space (for multiple model sizes) |
| **Microphone** | Built-in mic | USB cardioid mic or low-latency headset |
| **OS** | macOS 12+ / Ubuntu 22.04 LTS | macOS 14+ Sonoma / Ubuntu 24.04 LTS |

---

## 🛠️ Troubleshooting & FAQ

<details>
<summary><b>1. PortAudio or sounddevice installation errors on macOS / Linux</b></summary>
<br>

Ensure system audio headers are installed before running pip:
- **macOS**: `brew install portaudio espeak-ng`
- **Linux**: `sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng`

Then install Python requirements:
```bash
pip install -r requirements.txt
```
</details>

<details>
<summary><b>2. Ollama connection refused (127.0.0.1:11434)</b></summary>
<br>

Make sure the Ollama daemon is running in the background:
```bash
ollama serve
# In another terminal verify:
ollama list
```
</details>

<details>
<summary><b>3. Kokoro TTS fallback to CPU instead of MPS/CUDA</b></summary>
<br>

Verify PyTorch sees your GPU accelerator:
```python
import torch
print("MPS Available:", torch.backends.mps.is_available())
print("CUDA Available:", torch.cuda.is_available())
```
If MPS is not detected on Apple Silicon, ensure you installed PyTorch via native arm64 Python.
</details>

<details>
<summary><b>4. Microphone self-transcription during speaker playback</b></summary>
<br>

Switch to `smart` barge-in mode (default) or `headphones` mode if using a headset:
```bash
python main.py --barge-in smart
```
You can also press `[Enter]` in the terminal to immediately cut off speech playback.
</details>

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
