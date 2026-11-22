# Jarvis: Low-Latency Local Voice AI Assistant 🎙️🤖

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%2B-3776AB.svg?logo=python&logoColor=white)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper%20(base.en)-8A2BE2.svg)](#)
[![LLM Model](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-FF6F00.svg?logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20(af__heart)-FF69B4.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20CUDA-blue.svg)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg)](#)
[![Privacy Guarantee](https://img.shields.io/badge/Privacy-100%25%20On--Device-success.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

**Jarvis** is a low-latency, privacy-focused, local-first voice assistant engineered to run 100% locally on edge consumer hardware. Featuring ultra-fast Voice Activity Detection (VAD), high-accuracy Speech-to-Text (STT), deterministic local LLM orchestration with live web search and tool execution, real-time streaming Text-to-Speech (TTS), and an audio-reactive floating Siri-like desktop orb widget.

---

## ⚡ Quick Start (3 Steps)

### 1. Install System Dependencies & Python Requirements

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

### 2. Pull Local LLM Model (Ollama)
Ensure [Ollama](https://ollama.com/) is installed and running locally, then pull the lightweight Llama 3.2 model:
```bash
ollama pull llama3.2
```

### 3. Launch Jarvis!
```bash
python main.py
```

---

## 🛠️ Architecture & Audio Pipeline

Jarvis runs as an asynchronous, event-driven pipeline designed to minimize end-to-end latency while eliminating feedback loops and echo self-transcription.

```mermaid
flowchart LR
    subgraph Input ["1. Input Pipeline"]
        A[🎙️ Microphone Input] -->|16kHz PCM| B[⚡ Silero VAD]
        B -->|Speech Buffers| C[👂 faster-whisper STT]
    end

    subgraph Intelligence ["2. Orchestration & Intelligence"]
        C -->|Transcribed Text| D[🧠 Ollama / Llama 3.2]
        D <-->|Deterministic Routing| E[🛠️ Python Tools / Live Search]
    end

    subgraph Output ["3. Output & Feedback"]
        D -->|Sentence Stream| F[🔊 Kokoro TTS]
        F -->|Audio Segments| G[📢 Speaker Output]
        G -.->|RMS Amplitude| H[🔮 Desktop Orb Widget]
        G -.->|Adaptive Echo Lock| B
    end
```

### Data Flow Breakdown
1. **🎙️ Speech Detection & Endpointing**: Microphone input is continuously evaluated by **Silero VAD** for sub-millisecond edge endpointing, isolating human speech from ambient background noise.
2. **👂 Async Speech Transcription**: Completed speech segments are passed to **faster-whisper** for low-latency asynchronous transcription.
3. **🧠 Intelligence & Tool Routing**: **Ollama (Llama 3.2)** processes the user prompt. Relevant local Python tools (real-time DuckDuckGo search, Yahoo Finance stocks, Google News RSS, weather, Wikipedia, time, smart home) are invoked deterministically.
4. **🔊 Streaming Audio Synthesis**: **Kokoro TTS** synthesizes text chunks sentence-by-sentence into low-latency audio buffers, instantly queued for speaker playback via `sounddevice`.
5. **🔮 Dynamic Visuals & Echo Protection**: Speaker audio drives real-time scaling on the floating **Desktop Orb Widget** while maintaining adaptive echo gating to suppress self-hearing.

---

## 🌟 Core Features & Highlights

* **⚡ Sub-280ms First-Syllable Latency**: Optimized background audio chunking, sentence-level regex streaming, Whisper VAD bypass, and greedy LLM decoding provide near-instant responses.
* **🔮 Animated Siri-Like Desktop Orb**: Borderless floating Tkinter UI widget that breathes when listening, sways when thinking, and dynamically scales in response to speaker amplitude. Drag and drop anywhere on your desktop.
* **🔒 100% Private & Local-First**: Core speech processing and language models run entirely locally. Auto-detects hardware acceleration (`MPS` for Apple Silicon, `CUDA` for NVIDIA GPUs). Web access is strictly transparent and tool-driven.
* **🔄 Flexible Barge-In Modes**: Interrupt the assistant seamlessly mid-speech. Supports `smart` (RMS volume-gated), `headphones` (full-duplex open mic), and `disabled` (half-duplex mic lock).
* **⌨️ Manual Interruption**: Press `<Enter>` in your terminal anytime during speech to trigger an instant barge-in cut-off.
* **🛡️ Adaptive Echo & Loop Suppression**: Dynamic decay cooldown (`0.35s`) and amplitude gating prevent the assistant from transcribing its own output through microphone spillover.
* **🔧 Deterministic Tool Routing**: Tool execution layer eliminates hallucinated tool calls with fast pre-filtering for live search, financial market data, breaking news, weather, Wikipedia, smart home controls, and system utilities.

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

## ⏱️ Subsystem Latency & Component Specs

Through overlapping stream execution, Jarvis initiates voice synthesis before the LLM finishes generating the full response:

| Pipeline Stage | Engine / Model | Hardware Target | Execution Strategy | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | `sounddevice` / PortAudio | Host CPU | 32ms audio frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence decay | `< 5 ms` |
| **Speech-to-Text** | `faster-whisper` (`base.en`) | CTranslate2 | Greedy decoding, `vad_filter=False` | `60 - 90 ms` |
| **LLM First-Token** | Ollama (`llama3.2:3b`) | Apple MPS / CUDA | `temperature=0.0`, `num_ctx=1024` | `40 - 70 ms` |
| **Sentence Chunking** | Python regex stream | Host CPU | Punctuation boundary splitting (`.`, `!`, `?`, `\n`) | `< 1 ms` |
| **TTS Synthesis** | Kokoro TTS (`af_heart`) | PyTorch MPS / CUDA | Sentence-level streaming synthesis | `50 - 80 ms` |
| **Audio Playback** | `sounddevice` Output Stream | Host CPU | 24kHz float32 non-blocking queue | `< 5 ms` |
| **Cumulative Total** | **End-to-End Voice Loop** | **Hardware Accelerated** | **First audible spoken syllable** | **~200 - 280 ms** |

---

## 📁 Codebase Architecture & File Map

| File | Purpose | Subsystem Layer |
| :--- | :--- | :--- |
| [main.py](main.py) | Application entry point, thread coordinator, signal handling | Core Orchestrator |
| [audio_engine.py](audio_engine.py) | SoundDevice mic capture, Silero VAD endpointing, and adaptive echo gating | DSP & Audio In |
| [stt_engine.py](stt_engine.py) | Async Speech-to-Text transcription powered by `faster-whisper` | Speech Recognition |
| [llm_engine.py](llm_engine.py) | Ollama Llama 3.2 integration, memory buffer, and deterministic tool router | Language & Reasoning |
| [tts_engine.py](tts_engine.py) | Sentence-streaming speech synthesis using Kokoro TTS (MPS/CUDA) | Voice Synthesis |
| [ui_engine.py](ui_engine.py) | Floating Tkinter desktop orb widget with dynamic state animations | User Interface |
| [avatar.png](avatar.png) | High-resolution graphical asset for desktop orb avatar scaling | UI Asset |
| [test_jarvis.py](test_jarvis.py) | Unit test suite for deterministic tool routing and memory management | Verification |
| [Dockerfile](Dockerfile) | Production Linux container configuration with host ALSA device access | Deployment |
| [requirements.txt](requirements.txt) | Managed Python package dependencies | Environment |
| [.gitignore](.gitignore) | Git ignore patterns for Python bytecode, virtual environments, and OS files | Project Hygiene |

---

## 🏎️ Key Latency & Performance Optimizations

* **🎙️ Background Audio Chunk Streaming**: Kokoro TTS generation executes in a background thread and dispatches synthesized PCM frames via `loop.call_soon_threadsafe`, reducing audio output startup delay to under **50ms**.
* **🔇 Whisper VAD Bypass (`vad_filter=False`)**: Relying on primary Silero VAD endpoints for initial speech capture allows redundant second-pass filtering in Whisper to be disabled, eliminating **100–300ms** of transcription overhead.
* **⏳ Aggressive Silence Endpointing**: Silence threshold set to `0.35s` (down from `1.2s`), allowing transcription to initiate instantly upon speech completion.
* **🎨 macOS Cocoa Canvas Transparency Fix**: Standard transparent Tkinter canvases on macOS composite alpha channels against transparent windows. Resolved by rendering a dynamic canvas background oval (`canvas.create_oval`) matching the moving avatar's exact scale.
* **♻️ Tkinter Garbage Collection Preservation**: Prevents Python GC sweeps from dropping dynamic `PhotoImage` frame references by binding image instances directly to the canvas element (`self.canvas.image = self.avatar_img`).
* **⚡ Greedy LLM Inference**: Configured Ollama parameters with greedy decoding (`temperature: 0.0`), concise context (`num_ctx: 1024`), and bounded output length (`num_predict: 50`) to minimize generation latency.

---

## 🚀 Usage & Configuration Options

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

### Containerized Deployment (Docker)
Build and run the assistant container with host audio driver access (Linux):
```bash
docker build -t local-voice-ai .
docker run -it --device /dev/snd --network host local-voice-ai
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

## 📜 Version History & Changelog

* **2026-10-29**: Integrated `sounddevice` non-blocking audio engine, relative repository file links, and console barge-in interruption.
* **2026-08-04**: Upgraded default Whisper model to `base.en` and introduced the `--stt-model` CLI flag.
* **2026-08-04**: Implemented deterministic `get_relevant_tools` routing in `llm_engine.py` to eliminate tool calling hallucinations in Ollama / Llama 3.2.
* **2026-08-04**: Integrated real-time web search (`search_web`) via DuckDuckGo, stock lookups via Yahoo Finance, and live breaking news via Google News RSS (`get_latest_news`).
* **2026-08-04**: Added automatic web search routing for political leader queries and real-time facts.
* **2026-08-04**: Enhanced Desktop Orb UI with drag-to-repositioning, macOS Cocoa background transparency fix, MPS/CUDA auto-acceleration for Kokoro TTS, and conversation memory buffer pruning.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
