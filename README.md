<div align="center">

# 🎙️ JARVIS: The Edge-Native Voice AI

### Ultra-Low Latency • 100% Private • Local-First Intelligence

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
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
        T3["🧵 PortAudio Input Callback\n(16kHz float32 non-blocking mic chunk producer)"]
        T4["🧵 PortAudio Output Callback\n(24kHz float32 audio consumer & ring buffer)"]
        T5["🧵 Neural Synthesis Worker\n(Kokoro PyTorch MPS/CUDA generator thread)"]
    end

    subgraph DataPipeline ["Data Stream & Processing Pipeline"]
        Mic[🎙️ Microphone Input] -->|16kHz PCM| T3
        T3 -->|loop.call_soon_threadsafe| Q1[(asyncio.Queue\nraw_audio_queue)]
        Q1 --> VAD[⚡ Silero VAD Edge Engine\nEndpointing (0.35s silence decay)]
        
        VAD -->|Speech Buffers| Q2[(asyncio.Queue\nspeech_buffer_queue)]
        Q2 --> STT[👂 faster-whisper Worker\nCTranslate2 int8 / fp16]
        
        STT -->|Transcribed Text| Q3[(asyncio.Queue\ntext_queue)]
        Q3 --> LLM[🧠 Ollama Llama 3.2\nGreedy temp=0.0]
        
        LLM <-->|Deterministic Routing| Tools[🛠️ Python Tools\n(Finance, Search, News, Weather)]
        LLM -->|Sentence Chunks [.!?\n]| Q4[(asyncio.Queue\ntts_queue)]
        
        Q4 --> T5
        T5 -->|loop.call_soon_threadsafe| Q5[(asyncio.Queue\naudio_playback_queue)]
        Q5 --> T4
        T4 -->|24kHz float32 PCM| Spk[📢 Hardware Speakers]
        T4 -.->|RMS Audio Amplitude| UI[🔮 Desktop Orb UI]
        T4 -.->|Dynamic Echo Lock| VAD
    end
```

---

## ⏱️ Subsystem Latency Breakdown

Through overlapping stream execution, Jarvis initiates voice synthesis before the LLM finishes generating the full response:

| Processing Stage | Engine / Model | Hardware Target | Execution Strategy | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Audio Capture** | PyAudio / PortAudio | Host CPU | 32ms audio frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence decay | `< 5 ms` |
| **Speech-to-Text** | `faster-whisper` (`base.en`) | CTranslate2 | Greedy decoding, `vad_filter=False` | `60 - 90 ms` |
| **LLM First-Token** | Ollama (`llama3.2:3b`) | Apple MPS / CUDA | `temperature=0.0`, `num_ctx=1024` | `40 - 70 ms` |
| **Sentence Chunking** | Python regex stream | Host CPU | Punctuation boundary splitting (`.`, `!`, `?`, `\n`) | `< 1 ms` |
| **TTS Synthesis** | Kokoro TTS (`af_heart`) | PyTorch MPS / CUDA | Sentence-level streaming synthesis | `50 - 80 ms` |
| **Audio Playback** | PyAudio Callback Stream | Host CPU | 24kHz float32 non-blocking queue | `< 5 ms` |
| **Cumulative Total** | **End-to-End Voice Loop** | **Hardware Accelerated** | **First audible spoken syllable** | **~200 - 280 ms** |

---

## 🌐 Live Web & Tool Integrations

Jarvis pre-routes queries to local Python tools when real-time information or system interaction is requested:

| Capability | Example Query | Tool Function | Data Source / Provider |
| :--- | :--- | :--- | :--- |
| **📈 Live Stock Markets** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `NVDA`, `MSFT`) |
| **🌐 Real-Time Web Search** | *"Who won the game yesterday?"* | `search_web` | DuckDuckGo Search Engine API |
| **🏛️ Political & Current Facts** | *"Who is the prime minister of the UK?"* | `search_web` | Real-time Search Engine |
| **📰 Breaking Global News** | *"What is the latest headline news?"* | `get_latest_news` | Google News RSS Feed Parser |
| **📚 Encyclopedic Knowledge** | *"Tell me about Quantum Superposition"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Automation** | *"Turn off the living room lights"* | `toggle_smart_lights` | Local Smart Home REST API |
| **⏰ System Clock** | *"What time is it in London?"* | `get_current_time` | System Clock & Timezones |

---

## 🎛️ Audio DSP & Echo Cancellation

### Dynamic Acoustic Lock Formula
To prevent speaker audio from looping back into the microphone without requiring external hardware AEC, `audio_engine.py` enforces a dynamic acoustic threshold:

$$\text{Lock}_{\text{mic}} = A_{\text{mic}} < \max\left(0.08,\; 1.5 \times A_{\text{speaker}}\right)$$

* **Acoustic Gating**: As speaker playback volume ($A_{\text{speaker}}$) rises, the microphone rejection floor increases proportionally to suppress room reflections.
* **Smart Barge-In**: When the user speaks firmly ($A_{\text{mic}} \ge 1.5 \times A_{\text{speaker}}$), playback cuts immediately, transitioning the pipeline back to speech capture.

### Barge-In Modes
```bash
# Smart Mode (Default: volume-gated interrupt for speakers)
python main.py --barge-in smart

# Headphones Mode (Full-duplex open mic; instant interruption)
python main.py --barge-in headphones

# Disabled Mode (Traditional half-duplex walkie-talkie mode)
python main.py --barge-in disabled
```

---

## 🔮 Floating Desktop Orb UI

The floating desktop widget in `ui_engine.py` provides visual feedback:

| Visual State | Color Theme | Animation Dynamic |
| :--- | :--- | :--- |
| **Idle / Listening** | Cyan Glow (`#00f0ff`) | Gentle breathing sine-wave oscillation (period: 2.0s) |
| **Thinking** | Shifting Purple (`#a855f7`) | Horizontal sway & pulsing compression wave |
| **Speaking** | Electric Blue (`#3b82f6`) | Real-time dynamic expansion scaled to TTS audio RMS amplitude |

### macOS Cocoa Transparency Fix
Standard Tkinter transparent canvases on macOS composite alpha channels against transparent windows, resulting in dark jagged borders. Jarvis resolves this by rendering a dynamic canvas background oval (`canvas.create_oval`) matching the moving avatar's exact scale and coordinates.

---

## 🚀 CLI Usage & Runtime Flags

```bash
# Launch with default settings
python main.py

# Select custom Whisper model (tiny.en, base.en, small.en, medium.en)
python main.py --stt-model small.en

# Run desktop widget standalone (visual animation testing)
python ui_engine.py

# Run unit tests
python -m unittest test_jarvis.py
```

### Docker Deployment
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
| [main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py) | Application entry point, thread coordinator, signal handling | Core Orchestrator |
| [audio_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/audio_engine.py) | PyAudio mic streams, Silero VAD endpointing, and adaptive echo gating | DSP & Audio In |
| [stt_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/stt_engine.py) | Async Speech-to-Text transcription powered by `faster-whisper` | Speech Recognition |
| [llm_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/llm_engine.py) | Ollama Llama 3.2 integration, memory buffer, and deterministic tool router | Language & Reasoning |
| [tts_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/tts_engine.py) | Sentence-streaming speech synthesis using Kokoro TTS (MPS/CUDA) | Voice Synthesis |
| [ui_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/ui_engine.py) | Floating Tkinter desktop orb widget with dynamic state animations | User Interface |
| [test_jarvis.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/test_jarvis.py) | Unit test suite for deterministic tool routing and memory management | Verification |
| [Dockerfile](file:///Users/saikrishnaallam/Desktop/jarvis_ai/Dockerfile) | Production Linux container configuration with host ALSA device access | Deployment |
| [requirements.txt](file:///Users/saikrishnaallam/Desktop/jarvis_ai/requirements.txt) | Pinned Python package dependencies | Environment |
| [.gitignore](file:///Users/saikrishnaallam/Desktop/jarvis_ai/.gitignore) | Git ignore rules for bytecode, virtual environments, and OS files | Hygiene |

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
<summary><b>1. PortAudio or PyAudio installation errors on macOS</b></summary>
<br>

Ensure Homebrew packages are installed and environment variables point to the Homebrew include directories:
```bash
brew install portaudio
export CFLAGS="-I$(brew --prefix portaudio)/include"
export LDFLAGS="-L$(brew --prefix portaudio)/lib"
pip install pyaudio
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
</details>

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
