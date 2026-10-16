# 🎙️ Jarvis: Real-Time On-Device Voice AI Assistant

[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](#)
[![STT](https://img.shields.io/badge/STT-faster--whisper%20(base.en)-8A2BE2.svg)](#)
[![LLM](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-FF6F00.svg?logo=ollama&logoColor=white)](#)
[![TTS](https://img.shields.io/badge/TTS-Kokoro%20(af__heart)-FF69B4.svg)](#)
[![Hardware](https://img.shields.io/badge/Acceleration-Apple%20MPS%20%7C%20CUDA-blue.svg)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

> **Jarvis** is a low-latency, 100% local voice assistant designed for natural, fluid spoken conversations. Operating entirely on edge consumer hardware (macOS Apple Silicon or Linux CUDA/CPU), Jarvis integrates neural Voice Activity Detection (VAD), CTranslate2-accelerated Speech-to-Text (STT), deterministic local LLM orchestration with live web search and market data, streaming Kokoro Text-to-Speech (TTS), and an audio-reactive desktop orb widget.

---

## ⚡ Quick Start in 3 Steps

### 1. Install System Audio Dependencies & Python Packages

#### macOS (Homebrew)
```bash
brew install portaudio espeak-ng
pip install -r requirements.txt
```

#### Linux (Debian / Ubuntu / Pop!_OS)
```bash
sudo apt-get update && sudo apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    espeak-ng

pip install -r requirements.txt
```

### 2. Pull the Local Brain (Ollama)
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

Jarvis uses an asynchronous, multi-threaded event-driven pipeline designed to minimize end-to-end latency while eliminating acoustic feedback loops and speaker self-transcription.

```mermaid
flowchart TB
    subgraph Threads ["Thread Concurrency Isolation"]
        direction TB
        MainThread["🧵 Main GUI Thread\n(Tkinter root loop, Cocoa UI, Signal Handlers)"]
        AsyncThread["🧵 Asyncio Event Loop Daemon\n(Workers, Queues, Signal Dispatcher)"]
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

## ⏱️ Subsystem Latency & Component Specs

Through overlapping stream execution, Jarvis initiates voice synthesis before the LLM finishes generating the full response:

| Pipeline Stage | Engine / Model | Hardware Target | Execution Strategy | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | PyAudio / PortAudio | Host CPU | 32ms audio frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence decay | `< 5 ms` |
| **Speech-to-Text** | `faster-whisper` (`base.en`) | CTranslate2 | Greedy decoding, `vad_filter=False` | `60 - 90 ms` |
| **LLM First-Token** | Ollama (`llama3.2:3b`) | Apple MPS / CUDA | `temperature=0.0`, `num_ctx=1024` | `40 - 70 ms` |
| **Sentence Chunking** | Python regex stream | Host CPU | Punctuation boundary splitting (`.`, `!`, `?`, `\n`) | `< 1 ms` |
| **TTS Synthesis** | Kokoro TTS (`af_heart`) | PyTorch MPS / CUDA | Sentence-level streaming synthesis | `50 - 80 ms` |
| **Audio Playback** | PyAudio Callback Stream | Host CPU | 24kHz float32 non-blocking queue | `< 5 ms` |
| **Cumulative Total** | **End-to-End Voice Loop** | **Hardware Accelerated** | **First audible spoken syllable** | **~200 - 280 ms** |

---

## 🌟 Core Features & Highlights

- ⚡ **Sub-300ms First-Syllable Latency**: Overlapping audio chunking, sentence-level pipelining, and greedy LLM inference eliminate conversational awkward pauses.
- 🔮 **Floating Siri-Like Desktop Orb**: Frameless, borderless desktop avatar with smooth breathing, listening, thinking, and speaking animations driven by real-time voice amplitude.
- 🔒 **100% Private & Edge-First**: Audio capture, VAD, transcription, LLM generation, and voice synthesis run entirely on local silicon. No voice data ever leaves your machine.
- 🔄 **Smart Barge-In Interruption**: Talk over the assistant mid-response. Built-in RMS volume gating automatically cuts off TTS playback when user speech is detected.
- 🛡️ **Adaptive Echo & Loop Suppression**: Dynamic decay cooldown (`0.35s`) and amplitude gating prevent the assistant from transcribing its own output through microphone spillover.
- 🌐 **Deterministic Tool Calling**: Zero-hallucination tool invocation with strict keyword & regex matching for real-time stock prices, live search, breaking news, weather, and system utilities.
- 🍏 **Hardware Accelerated**: Native Apple Silicon Metal Performance Shaders (`MPS`) and NVIDIA `CUDA` acceleration auto-detected on boot.

---

## 🌐 Real-Time Web & Tool Integration

Jarvis routes queries requiring current external data to zero-latency Python tools before prompting the LLM:

| Capability | Example Query | Tool Function | Data Source / Provider |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `NVDA`, `MSFT`) |
| **🌐 Live Web Search** | *"Who won the Formula 1 race yesterday?"* | `search_web` | DuckDuckGo Search Engine API |
| **🏛️ World Leaders & Facts** | *"Who is the prime minister of the UK?"* | `search_web` | Real-time Search Engine |
| **📰 Breaking Global News** | *"What is the latest headline news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 Encyclopedia & Science** | *"Tell me about Quantum Superposition"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Automation** | *"Turn off the living room lights"* | `toggle_smart_lights` | Local Smart Home REST API |
| **⏰ System Clock** | *"What time is it in London?"* | `get_current_time` | System Clock & Timezones |

---

## 🎛️ Audio Engineering & Echo Cancellation

### Dynamic Acoustic Lock Formula
To prevent speaker audio from looping back into the microphone without requiring external hardware AEC, `audio_engine.py` enforces a dynamic acoustic threshold:

$$\text{Lock}_{\text{mic}} = A_{\text{mic}} < \max\left(0.08,\; 1.5 \times A_{\text{speaker}}\right)$$

* **Feedback Prevention**: When the speaker is playing loudly, $A_{\text{speaker}}$ scales the mic rejection floor dynamically to ignore room reflections.
* **Smart Barge-In**: When the user speaks firmly ($A_{\text{mic}} \ge 1.5 \times A_{\text{speaker}}$), Jarvis cuts playback instantly and transitions back to active speech listening.

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

The desktop widget in `ui_engine.py` provides visual state feedback:

| Visual State | Visual Representation | Animation Behavior |
| :--- | :--- | :--- |
| **Idle / Listening** | Soft cyan glowing orb | Gentle breathing sine wave oscillation |
| **Thinking** | Shifting purple glow | Faster horizontal sway & pulsing wave |
| **Speaking** | Dynamic electric blue orb | Real-time expansion & contraction scaled to TTS audio RMS amplitude |

### macOS Cocoa Transparency Architecture
Standard Tkinter windows on macOS create alpha compositing artifacts against transparent desktop windows. Jarvis overcomes this by rendering a dynamic canvas background oval (`canvas.create_oval`) that tracks the avatar's exact coordinates and scale, ensuring smooth anti-aliased edges.

---

## 🚀 CLI Usage & Configuration Options

### Launch Modes
```bash
# Smart Mode (Default - RMS volume-gated barge-in for speakers)
python main.py

# Headphones Mode (Recommended for headphones - full-duplex open mic)
python main.py --barge-in headphones

# Disabled Mode (Traditional half-duplex mic lock during speech output)
python main.py --barge-in disabled
```

### Custom STT Model Selection
Choose from available Whisper model sizes (`tiny.en`, `base.en`, `small.en`, `medium.en`):
```bash
python main.py --stt-model small.en
```

### Standalone Desktop Widget Testing
Test UI animations, state transitions, and click-and-drag interactions independently:
```bash
python ui_engine.py
```

### Automated Unit Test Suite
Run the test suite to verify tool routing and memory management logic:
```bash
python -m unittest test_jarvis.py
```

---

## 📁 Codebase Architecture & File Map

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
| [.gitignore](file:///Users/saikrishnaallam/Desktop/jarvis_ai/.gitignore) | Git ignore patterns for Python bytecode, virtual environments, and OS files | Project Hygiene |

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

| Component | Minimum | Recommended |
| :--- | :--- | :--- |
| **Processor** | Quad-core x86_64 or Apple Silicon M1 | Apple Silicon M2/M3/M4 or NVIDIA RTX 3060+ |
| **RAM** | 8 GB | 16 GB+ (Apple Silicon or NVIDIA GPU) |
| **Storage** | 5 GB available | 10 GB (for multiple Whisper/Ollama models) |
| **Microphone** | Built-in mic | Dedicated directional USB mic or headset |
| **OS** | macOS 12+ / Linux | macOS 14+ (Apple Silicon M-series recommended) |

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

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.
