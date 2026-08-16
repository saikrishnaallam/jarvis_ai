# 🎙️ Jarvis: Low-Latency Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper-8A2BE2.svg?style=for-the-badge)](#)
[![LLM Model](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20v1.0-FF69B4.svg?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Jarvis** is a low-latency, privacy-first voice assistant engineered to run **100% locally** on your desktop. Combining edge Voice Activity Detection (VAD), faster-whisper Speech-to-Text (STT), deterministic local LLM orchestration with live web search & stock lookups, real-time streaming Kokoro Text-to-Speech (TTS), and a floating animated Siri-like desktop orb widget.

---

## 🔮 Animated Desktop Orb UI

Jarvis features a floating, borderless desktop orb widget built with Tkinter that provides dynamic visual feedback as you speak:

```
  +-----------------------------------------------------------------------+
  |  State      | Visual Animated Output                                  |
  +-------------+---------------------------------------------------------+
  | IDLE        |  ( ( ( ⚪ ) ) )  Soft breathing white glow ring         |
  | LISTENING   |  < < < 🔵 > > >  Pulsing cyan/blue audio capture ring   |
  | THINKING    |  / / / 🟣 \ \ \  Rotating morphing magenta sway ring    |
  | SPEAKING    |  { { { 🟢 } } }  Green ring dynamic volume amplitude bounce |
  +-----------------------------------------------------------------------+
```

* **Click & Drag Repositioning**: Click and drag the floating orb widget anywhere on your desktop screen.
* **macOS Transparency Fix**: Custom solid white oval background rendering eliminates macOS Cocoa alpha-channel compositing artifacts.
* **Volume Amplitude Reactive**: Scales dynamically in real time to the assistant's output audio volume.

---

## 📊 Feature Comparison: Jarvis vs. Traditional Voice Assistants

| Feature | 🎙️ **Jarvis (Local AI)** | 🍏 **Apple Siri** | 🔊 **Amazon Alexa** | ☁️ **Cloud AI (ChatGPT Voice)** |
| :--- | :---: | :---: | :---: | :---: |
| **100% Local & Private** | ✅ **Yes** | ❌ Partial | ❌ No | ❌ No |
| **Zero API / Subscription Fees** | ✅ **Yes** | ✅ Free | ✅ Free | ❌ $20+/mo |
| **Sub-300ms Audio Latency** | ✅ **Yes** | ⚠️ Varies | ⚠️ ~1–2s | ⚠️ ~1.5–3s |
| **Smart Barge-In (Mid-Speech Interrupt)** | ✅ **Yes** | ❌ No | ❌ No | ✅ Yes |
| **Live Web Search & Financial Tickers** | ✅ **Yes** | ⚠️ Basic | ⚠️ Basic | ✅ Yes |
| **Deterministic Local Tool Calling** | ✅ **Yes** | ❌ No | ❌ Custom Skills | ⚠️ Complex |
| **Hardware Acceleration (MPS/CUDA)** | ✅ **Yes** | N/A (Cloud) | N/A (Cloud) | N/A (Cloud) |
| **Floating Animated Desktop Widget** | ✅ **Yes** | ❌ No | ❌ No | ❌ No |

---

## ⚡ Quick Start Guide (3 Simple Steps)

### Step 1: Install System Dependencies & Python Packages
```bash
# macOS (via Homebrew)
brew install portaudio espeak-ng

# Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Start Ollama & Pull Model
Make sure your local [Ollama](https://ollama.com/) service is running, then pull the Llama 3.2 model:
```bash
ollama pull llama3.2
```

### Step 3: Launch Jarvis!
```bash
python main.py
```

---

## 🛠️ System Architecture & Data Flow

Jarvis operates as an asynchronous, non-blocking pipeline designed to keep audio streaming smooth without dropping mic frames or delaying voice output.

```mermaid
flowchart LR
    subgraph Input ["1. Input Pipeline"]
        A[🎙️ Microphone] -->|32ms Audio Chunks| B[⚡ Silero VAD]
        B -->|Endpointed Speech| C[👂 faster-whisper STT]
    end

    subgraph Core ["2. Local Intelligence & Tools"]
        C -->|Transcribed Text| D[🧠 Ollama / Llama 3.2]
        D <-->|Function Calling| E[🛠️ Local Tools / Live Web]
    end

    subgraph Output ["3. Streaming Audio Output"]
        D -->|Sentence Stream| F[🔊 Kokoro TTS]
        F -->|Audio Segments| G[📢 Speakers]
        G -.->|RMS Volume Amplitude| H[🔮 Desktop Orb UI]
        G -.->|Smart Echo Lock| B
    end
```

### Codebase Directory Map

* **[main.py](main.py)**: Orchestrator entry point initializing worker loops, managing global signal handlers (`SIGINT`/`SIGTERM`), and driving the main-thread Cocoa GUI loop.
* **[audio_engine.py](audio_engine.py)**: Handles PyAudio microphone input streams, Silero VAD edge endpointing, RMS volume calculations, and adaptive echo suppression gating.
* **[stt_engine.py](stt_engine.py)**: Asynchronously transcribes speech audio buffers using `faster-whisper` (CTranslate2 `int8`/`fp16`) with VAD filter bypass (`vad_filter=False`).
* **[llm_engine.py](llm_engine.py)**: Ollama chat orchestrator with conversation memory pruning (20 messages), regex sentence chunking, and deterministic keyword tool routing.
* **[tts_engine.py](tts_engine.py)**: Synthesizes high-quality spoken audio using Kokoro TTS (hardware-accelerated via MPS/CUDA) and streams segments to speaker playback queues.
* **[ui_engine.py](ui_engine.py)**: Floating Tkinter desktop widget rendering dynamic visual states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`) with click-and-drag movement.
* **[test_jarvis.py](test_jarvis.py)**: Unit test suite for deterministic tool routing, keyword matching, and conversation buffer pruning.
* **[Dockerfile](Dockerfile)**: Container setup for Linux deployments with host audio device passthrough.
* **[requirements.txt](requirements.txt)**: Python library dependencies manifest.

---

## 🌐 Real-Time Web Search & Tool Integration

Jarvis intelligently routes queries to local tools when real-time information or system control is needed:

| Capability | Example Prompt | Executed Tool | Provider / Data Source |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `MSFT`, `NVDA`, etc.) |
| **🌐 Live Web Search** | *"Who won the game today?"* | `search_web` | DuckDuckGo Search API |
| **🏛️ Political & Current Leaders** | *"Who is the prime minister of Canada?"* | `search_web` | Live Web Engine Lookup |
| **📰 Global Breaking News** | *"What is the latest breaking news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 General Knowledge** | *"Tell me about Quantum Computing"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Control** | *"Turn off the living room lights"* | `toggle_smart_lights` | Smart Home REST API |
| **⏰ System Utilities** | *"What time is it right now?"* | `get_current_time` | System Clock |

---

## 🚀 Running Modes & Configuration Options

### Assistant Launch Modes
```bash
# 1. Smart Mode (Default: RMS volume-gated barge-in for speaker playback)
python main.py

# 2. Headphones Mode (Recommended for headphones: full duplex open mic)
python main.py --barge-in headphones

# 3. Disabled Mode (Traditional half-duplex mic lock during voice output)
python main.py --barge-in disabled
```

### Custom Speech-to-Text Model
Select your preferred Whisper model size (`tiny.en`, `base.en`, `small.en`, `medium.en`):
```bash
python main.py --stt-model small.en
```

### Standalone Widget & Unit Testing
```bash
# Standalone visual UI animation test
python ui_engine.py

# Automated unit test suite
python -m unittest test_jarvis.py
```

### Docker Container Deployment (Linux)
```bash
docker build -t local-voice-ai .
docker run -it --device /dev/snd --network host local-voice-ai
```

---

## ❓ Frequently Asked Questions & Troubleshooting

<details>
<summary><b>1. How does Smart Barge-In stop the assistant from hearing itself?</b></summary>
<br>
Jarvis monitors the real-time RMS volume amplitude of speaker playback ($A_{\text{speaker}}$) and microphone input ($A_{\text{mic}}$). In <code>smart</code> mode, the microphone is locked only if user volume is quieter than $A_{\text{mic}} < \max(0.08, A_{\text{speaker}} \times 1.5)$. Speaking loudly or wearing headphones instantly breaks the lock and interrupts generation.
</details>

<details>
<summary><b>2. How do I fix PyAudio or PortAudio installation errors on macOS?</b></summary>
<br>
Ensure PortAudio is installed via Homebrew:
<code>brew install portaudio espeak-ng</code><br>
If PyAudio compilation fails during pip install, run:
<code>pip install --global-option=build_ext --global-option="-I$(brew --prefix)/include" --global-option="-L$(brew --prefix)/lib" pyaudio</code>
</details>

<details>
<summary><b>3. Why is Ollama returning model not found errors?</b></summary>
<br>
Make sure the Ollama application is running in the background and you have pulled the required model using:
<code>ollama pull llama3.2</code>
</details>

<details>
<summary><b>4. Is GPU hardware acceleration supported?</b></summary>
<br>
Yes! Jarvis automatically detects hardware acceleration on startup:
<ul>
  <li><b>macOS Apple Silicon</b>: Uses Metal Performance Shaders (<code>MPS</code>) for Kokoro TTS and PyTorch.</li>
  <li><b>NVIDIA GPUs</b>: Uses <code>CUDA</code> and <code>float16</code> compute for Kokoro TTS and faster-whisper STT.</li>
</ul>
</details>

---

## 📜 Version History & Changelog

* **2026-08-04**: Upgraded default Whisper STT model to `base.en`; added CLI flag `--stt-model`.
* **2026-08-04**: Introduced deterministic keyword tool pre-filtering (`get_relevant_tools`) in `llm_engine.py` to eliminate tool calling hallucinations in Ollama / Llama 3.2.
* **2026-08-04**: Integrated real-time web search (`search_web`), Yahoo Finance stock lookups, and Google News RSS feed parsing (`get_latest_news`).
* **2026-08-04**: Added macOS Cocoa window transparency fix, auto-hardware acceleration (MPS/CUDA) for Kokoro TTS, and floating desktop orb drag-to-repositioning.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
