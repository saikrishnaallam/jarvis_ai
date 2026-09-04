# 🎙️ Jarvis: Low-Latency Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper%20(base.en)-8A2BE2.svg?style=for-the-badge)](#)
[![LLM Model](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20(af__heart)-FF69B4.svg?style=for-the-badge)](#)
[![Hardware Acceleration](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20NVIDIA%20CUDA-blue.svg?style=for-the-badge)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg?style=for-the-badge)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=for-the-badge)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Jarvis** is an ultra-responsive, privacy-focused, 100% local voice assistant engineered for natural spoken conversations. Operating entirely on edge consumer hardware (macOS Apple Silicon or Linux CUDA/CPU), Jarvis integrates real-time Voice Activity Detection (VAD), CTranslate2-accelerated Speech-to-Text (STT), deterministic local LLM orchestration with live web search & market data, streaming Kokoro Text-to-Speech (TTS), and a floating animated Siri-like desktop orb widget.

---

## 📑 Table of Contents

- [⚡ Quick Start (3 Steps)](#-quick-start-3-steps)
- [📐 System Architecture & Concurrency Pipeline](#-system-architecture--concurrency-pipeline)
- [⏱️ End-to-End Latency Breakdown](#-end-to-end-latency-breakdown)
- [🌟 Core Features & Capabilities](#-core-features--capabilities)
- [🌐 Real-Time Web & Tool Integration](#-real-time-web--tool-integration)
- [🎛️ Audio Engineering & Echo Cancellation](#-audio-engineering--echo-cancellation)
- [🔮 Floating Desktop Orb UI](#-floating-desktop-orb-ui)
- [🚀 CLI Usage & Configuration](#-cli-usage--configuration)
- [📁 Project Structure & File Map](#-project-structure--file-map)
- [🐳 Docker & Container Deployment](#-docker--container-deployment)
- [💻 Hardware Requirements](#-hardware-requirements)
- [🛠️ Troubleshooting & FAQ](#️-troubleshooting--faq)
- [📜 Changelog & License](#-changelog--license)

---

## ⚡ Quick Start (3 Steps)

### 1. Install System Dependencies & Python Requirements

#### macOS (via Homebrew)
```bash
brew install portaudio espeak-ng
pip install -r requirements.txt
```

#### Linux (Debian / Ubuntu)
```bash
sudo apt-get update && sudo apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    espeak-ng

pip install -r requirements.txt
```

### 2. Pull Local LLM Model (Ollama)
Ensure [Ollama](https://ollama.com/) is installed and running, then pull the lightweight Llama 3.2 model:
```bash
ollama pull llama3.2
```

### 3. Launch Jarvis!
```bash
python main.py
```

---

## 📐 System Architecture & Concurrency Pipeline

Jarvis uses an asynchronous, multi-threaded event-driven architecture designed to minimize latency while eliminating acoustic feedback loops and self-transcription.

```mermaid
flowchart TB
    subgraph Threads ["Thread & Concurrency Boundaries"]
        direction TB
        MainThread["🧵 Main GUI Thread\n(Tkinter root loop, Cocoa UI, Signal Handlers)"]
        AsyncThread["🧵 Asyncio Event Loop Thread\n(Workers, Queues, Signal Dispatcher)"]
        MicThread["🧵 PortAudio Mic Callback\n(Chunk Producer @ 16kHz float32)"]
        SpeakerThread["🧵 PortAudio Speaker Callback\n(Audio Consumer @ 24kHz float32)"]
        TTSWorkerThread["🧵 Kokoro Synthesis Thread\n(PyTorch MPS/CUDA Generator)"]
    end

    subgraph DataPipeline ["Data Stream & Processing Pipeline"]
        MicInput[🎙️ Mic Audio] -->|16kHz float32| MicThread
        MicThread -->|loop.call_soon_threadsafe| RawQueue[(asyncio.Queue\nraw_audio_queue)]
        RawQueue --> VADEngine[⚡ Silero VAD Edge Engine\n(Chunk size: 32ms, Threshold: 0.5)]
        
        VADEngine -->|Speech Buffer| SpeechQueue[(asyncio.Queue\nspeech_buffer_queue)]
        SpeechQueue --> STTEngine[👂 faster-whisper STT\n(beam_size=1, vad_filter=False)]
        
        STTEngine -->|Transcribed Text| TextQueue[(asyncio.Queue\ntext_queue)]
        TextQueue --> LLMEngine[🧠 Ollama Llama 3.2\n(greedy temp=0.0, num_ctx=1024)]
        
        LLMEngine <-->|Deterministic Routing| Tools[🛠️ Python Tools\n(Web Search, Yahoo Finance, Google News, Weather)]
        LLMEngine -->|Regex Sentence Chunks| TTSQueue[(asyncio.Queue\ntts_queue)]
        
        TTSQueue --> TTSWorkerThread
        TTSWorkerThread -->|loop.call_soon_threadsafe| PlaybackQueue[(asyncio.Queue\naudio_playback_queue)]
        PlaybackQueue --> SpeakerThread
        SpeakerThread -->|24kHz float32 PCM| SpeakerOutput[📢 Speakers]
        SpeakerThread -.->|RMS Amplitude| UIWidget[🔮 Desktop Orb UI]
        SpeakerThread -.->|Adaptive Echo Lock| VADEngine
    end
```

---

## ⏱️ End-to-End Latency Breakdown

Through parallel background audio streaming, sentence-level regex parsing, Whisper VAD bypass, and greedy decoding, Jarvis produces spoken audio within **~200–280ms** of the user finishing their sentence:

| Stage | Engine / Technology | Hardware Target | Execution Strategy | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | PyAudio / `sounddevice` | CPU | 32ms block frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence decay | `< 5 ms` |
| **Speech-to-Text** | `faster-whisper` (`base.en`) | CTranslate2 (int8 / fp16) | Greedy `beam_size=1`, second-pass VAD disabled | `60 - 90 ms` |
| **LLM First-Token** | Ollama (`llama3.2`) | MPS / CUDA | `temperature=0.0`, `num_ctx=1024`, greedy decoding | `40 - 70 ms` |
| **Sentence Chunking** | Python regex stream | CPU | Punctuation boundary detection (`.`, `!`, `?`, `\n`) | `< 1 ms` |
| **TTS Synthesis** | Kokoro TTS (`af_heart`) | PyTorch MPS / CUDA | Sentence-level streaming synthesis | `50 - 80 ms` |
| **Speaker Playback** | PyAudio output ring buffer | CPU | Non-blocking callback stream (24kHz float32) | `< 5 ms` |
| **Total Response Time** | **Full Pipeline** | **End-to-End** | **First audible spoken syllable** | **~200 - 280 ms** |

---

## 🌟 Core Features & Capabilities

- ⚡ **Sub-300ms First-Syllable Latency**: Overlapping audio chunking, sentence-level pipelining, and greedy LLM inference eliminate conversational awkward pauses.
- 🔮 **Floating Siri-Like Desktop Orb**: Frameless, borderless desktop avatar with smooth breathing, listening, thinking, and speaking animations driven by real-time voice amplitude.
- 🔒 **100% Private & Edge-First**: Audio capture, VAD, transcription, LLM generation, and voice synthesis run entirely on local silicon. No voice data ever leaves your machine.
- 🔄 **Smart Barge-In Interruption**: Talk over the assistant mid-response. Built-in RMS volume gating automatically cuts off TTS playback when user speech is detected.
- 🛡️ **Acoustic Echo Self-Hearing Suppression**: Multi-tiered RMS gating and dynamic cooldown decay (`0.35s`) prevent the assistant from hearing and transcribing its own speaker output.
- 🌐 **Deterministic Tool Calling**: Zero hallucination tool invocation with strict keyword & regex matching for real-time stock prices, live search, global news, weather, and system utilities.
- 🍏 **Hardware Accelerated**: Native Apple Silicon Metal Performance Shaders (`MPS`) and NVIDIA `CUDA` acceleration auto-detected on boot.

---

## 🌐 Real-Time Web & Tool Integration

Jarvis routes queries requiring current external data to zero-latency Python tools before prompting the LLM:

| Capability | Example Query | Tool Function | Data Source / Provider |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `NVDA`, `MSFT`) |
| **🌐 Live Web Search** | *"Who won the Formula 1 race yesterday?"* | `search_web` | DuckDuckGo Search Engine API |
| **🏛️ World Leaders & Facts** | *"Who is the current prime minister of the UK?"* | `search_web` | Real-time Search Engine |
| **📰 Breaking Global News** | *"What is the latest headline news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 Encyclopedia & Science** | *"Tell me about Quantum Superposition"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Automation** | *"Turn off the living room lights"* | `toggle_smart_lights` | Local Smart Home REST API |
| **⏰ System Clock** | *"What time is it in London?"* | `get_current_time` | System Clock & Timezones |

---

## 🎛️ Audio Engineering & Echo Cancellation

### Adaptive Echo Lock Formula
To prevent speaker-to-microphone feedback loops during TTS playback, `audio_engine.py` applies a dynamic acoustic threshold:

$$\text{Lock}_{\text{mic}} = A_{\text{mic}} < \max\left(0.08,\; A_{\text{speaker}} \times 1.5\right)$$

- When speaker output amplitude ($A_{\text{speaker}}$) is high, the microphone sensitivity threshold scales dynamically, preventing self-transcription.
- If the user speaks firmly to interrupt ($A_{\text{mic}} > 1.5 \times A_{\text{speaker}}$), barge-in interrupts TTS instantly.

### Barge-In Modes
- **`smart` (Default)**: Volume-gated interrupt for speaker use.
- **`headphones`**: Full-duplex open mic; instant interruption without amplitude gating.
- **`disabled`**: Half-duplex lock; microphone is disabled during speech playback.

---

## 🔮 Floating Desktop Orb UI

The desktop widget in `ui_engine.py` provides visual state feedback:

| Visual State | Visual Representation | Animation Behavior |
| :--- | :--- | :--- |
| **Idle / Listening** | Soft cyan glowing orb | Gentle breathing sine wave oscillation |
| **Thinking** | Shifting purple glow | Faster horizontal sway & pulsing wave |
| **Speaking** | Dynamic electric blue orb | Real-time expansion & contraction scaled to TTS audio RMS amplitude |

### macOS Cocoa Transparency Architecture
Standard Tkinter windows on macOS create alpha compositing artifacts against transparent desktop windows. Jarvis overcomes this by rendering a dynamic canvas background oval (`canvas.create_oval`) that tracks the avatar's exact coordinates and scale, ensuring smooth anti-aliased edges.

---

## 🚀 CLI Usage & Configuration

### Launch Flags
```bash
# Default Smart Mode
python main.py

# Headphones Mode (Recommended for headsets)
python main.py --barge-in headphones

# Disabled Mode (Half-duplex)
python main.py --barge-in disabled

# Specify custom Whisper model (tiny.en, base.en, small.en, medium.en)
python main.py --stt-model small.en
```

### Standalone Widget Preview
```bash
python ui_engine.py
```

### Automated Unit Test Suite
```bash
python -m unittest test_jarvis.py
```

---

## 📁 Project Structure & File Map

| File | Purpose | Subsystem Layer |
| :--- | :--- | :--- |
| [main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py) | Main application entry point, thread coordinator, signal handling | Orchestration |
| [audio_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/audio_engine.py) | Microphone input capture, Silero VAD endpointing, RMS echo gating | Audio Input & DSP |
| [stt_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/stt_engine.py) | Speech-to-Text transcription worker using `faster-whisper` | Speech Recognition |
| [llm_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/llm_engine.py) | Ollama Llama 3.2 integration, conversation memory, tool routing | Language & Reasoning |
| [tts_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/tts_engine.py) | Sentence-streaming speech synthesis using Kokoro TTS (MPS/CUDA) | Voice Synthesis |
| [ui_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/ui_engine.py) | Floating Siri-style desktop orb widget built with Tkinter | Visual Interface |
| [test_jarvis.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/test_jarvis.py) | Unit test suite for deterministic tool routing and memory management | Testing & Verification |
| [Dockerfile](file:///Users/saikrishnaallam/Desktop/jarvis_ai/Dockerfile) | Production Linux container configuration with host ALSA device access | Deployment |
| [requirements.txt](file:///Users/saikrishnaallam/Desktop/jarvis_ai/requirements.txt) | Managed Python dependencies and package specifications | Configuration |

---

## 🐳 Docker & Container Deployment

To run Jarvis inside a Linux container with host audio passthrough:

```bash
# Build the Docker image
docker build -t local-voice-ai .

# Run container with ALSA audio device and host networking
docker run -it \
    --device /dev/snd \
    --network host \
    local-voice-ai
```

---

## 💻 Hardware Requirements

| Specification | Minimum | Recommended (Optimal Experience) |
| :--- | :--- | :--- |
| **Processor** | Quad-core x86_64 or Apple Silicon M1 | Apple Silicon M2/M3/M4 or NVIDIA RTX 3060+ |
| **RAM** | 8 GB System Memory | 16 GB+ Unified Memory / System RAM |
| **GPU / Acceleration** | CPU fallback mode | Apple Metal (`MPS`) or NVIDIA `CUDA` |
| **Storage** | 5 GB free disk space | 15 GB free disk space (for multiple model sizes) |
| **Audio Input** | Integrated microphone | USB cardioid mic or low-latency headset |
| **OS** | macOS 12+ / Ubuntu 22.04 LTS | macOS 14+ Sonoma / Ubuntu 24.04 LTS |

---

## 🛠️ Troubleshooting & FAQ

<details>
<summary><b>1. PortAudio or PyAudio installation errors on macOS</b></summary>

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

Make sure the Ollama daemon is running in the background:
```bash
ollama serve
# In another terminal verify:
ollama list
```
</details>

<details>
<summary><b>3. Kokoro TTS fallback to CPU instead of MPS/CUDA</b></summary>

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

Switch to `smart` barge-in mode (default) or `headphones` mode if using a headset:
```bash
python main.py --barge-in smart
```
</details>

---

## 📜 Changelog & License

- **v1.2.0**: Added dynamic barge-in modes (`smart`, `headphones`, `disabled`), `--stt-model` selector, and real-time Yahoo Finance / Google News tool integration.
- **v1.1.0**: Implemented Cocoa desktop canvas alpha channel fix, Kokoro TTS MPS/CUDA auto-detection, and sentence regex streaming.
- **v1.0.0**: Initial release featuring Silero VAD, `faster-whisper`, Ollama Llama 3.2, and Tkinter floating orb widget.

Distributed under the **MIT License**. See `LICENSE` for details.
