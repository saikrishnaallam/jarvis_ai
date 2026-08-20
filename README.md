# 🎙️ Jarvis: Next-Gen Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=for-the-badge)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg?style=for-the-badge)](#)
[![Hardware Acceleration](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20NVIDIA%20CUDA-blue.svg?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Sub-280ms latency. Zero cloud dependencies. Complete data privacy.**  
> Jarvis is an ultra-fast, local-first voice AI assistant designed to run **100% on your machine**. Powered by edge Voice Activity Detection (VAD), faster-whisper Speech-to-Text (STT), deterministic local LLM orchestration with real-time web search & stock market tools, streaming Kokoro Text-to-Speech (TTS), and a floating animated Siri-like desktop orb widget.

---

## ✨ Key Feature Highlights

```
+-----------------------------------------------------------------------------------+
|  🔒 100% Local & Private     |  ⚡ Sub-280ms Latency     |  🔮 Siri-Like Desktop Orb |
|  Runs entirely on-device;    |  Real-time audio streaming|  Floating animated UI with|
|  zero cloud API data leaks.  |  with instant sentence TTS|  volume-reactive visuals. |
+-----------------------------------------------------------------------------------+
|  🔄 Smart Barge-In           |  🌐 Live Web & Tools      |  🚀 Hardware Accelerated  |
|  Interrupt mid-speech; RMS   |  Real-time Yahoo Finance, |  Auto-accelerated on Apple|
|  volume echo-suppression.    |  DuckDuckGo & RSS news.   |  Silicon MPS & NVIDIA CUDA|
+-----------------------------------------------------------------------------------+
```

---

## 📊 Feature Comparison Matrix

| Feature | 🎙️ **Jarvis (Local AI)** | 🍏 **Apple Siri** | 🔊 **Amazon Alexa** | ☁️ **ChatGPT Voice** |
| :--- | :---: | :---: | :---: | :---: |
| **100% Local & Offline Privacy** | ✅ **Yes** | ❌ Partial | ❌ No | ❌ No |
| **Zero Subscription Costs / Fees** | ✅ **Yes** | ✅ Free | ✅ Free | ❌ $20+/mo |
| **Sub-280ms First-Syllable Latency**| ✅ **Yes** | ⚠️ Varies | ⚠️ ~1–2s | ⚠️ ~1.5–3s |
| **Smart Mid-Speech Barge-In** | ✅ **Yes** | ❌ No | ❌ No | ✅ Yes |
| **Real-Time Web Search & Stocks** | ✅ **Yes** | ⚠️ Basic | ⚠️ Basic | ✅ Yes |
| **Deterministic Tool Keyword Routing**| ✅ **Yes** | ❌ No | ❌ Custom Skills | ⚠️ Complex |
| **Floating Animated Desktop Orb** | ✅ **Yes** | ❌ No | ❌ No | ❌ No |

---

## ⚡ Quick Start (3 Steps)

### Step 1: Install System Dependencies & Python Packages
```bash
# macOS (via Homebrew)
brew install portaudio espeak-ng

# Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

### Step 2: Start Ollama & Pull Llama 3.2
Ensure your local [Ollama](https://ollama.com/) service is running:
```bash
ollama pull llama3.2
```

### Step 3: Launch Jarvis
```bash
python main.py
```

---

## 🔮 Animated Siri-Like Desktop Orb UI

Jarvis includes a borderless, floating desktop orb widget built with Tkinter that dynamically adapts its visual state based on system processing:

```
  +-----------------------------------------------------------------------+
  | State       | Visual Animation Output                                 |
  +-------------+---------------------------------------------------------+
  | IDLE        |  ( ( ( ⚪ ) ) )  Soft breathing white glow ring         |
  | LISTENING   |  < < < 🔵 > > >  Pulsing cyan/blue audio capture ring   |
  | THINKING    |  / / / 🟣 \ \ \  Rotating morphing magenta sway ring    |
  | SPEAKING    |  { { { 🟢 } } }  Green ring reactive to volume amplitude|
  +-----------------------------------------------------------------------+
```

* **Click & Drag Repositioning**: Position the floating widget anywhere across your desktop screen.
* **macOS Transparency Fix**: Custom solid white oval canvas background rendering eliminates macOS Cocoa alpha-channel compositing artifacts.
* **Amplitude Reactive**: Avatar scale factor $S = 0.9 + 0.35 \cdot A_{\text{speaker}} + 0.05\sin(0.3 \cdot t)$ drives dynamic volume-responsive movement.

---

## 🛠️ End-to-End Pipeline Architecture

Jarvis uses an asynchronous, multi-threaded pipeline designed to stream audio without dropping microphone frames.

```mermaid
flowchart LR
    subgraph Input ["1. Speech Input"]
        A[🎙️ Microphone] -->|32ms Audio Frames| B[⚡ Silero VAD]
        B -->|Endpointed Speech| C[👂 faster-whisper STT]
    end

    subgraph Intelligence ["2. Intelligence & Tools"]
        C -->|Transcribed Text| D[🧠 Ollama / Llama 3.2]
        D <-->|Function Execution| E[🛠️ Local Tools / Live Web]
    end

    subgraph Output ["3. Streaming Audio Output"]
        D -->|Sentence Stream| F[🔊 Kokoro TTS]
        F -->|Audio Segments| G[📢 Speakers]
        G -.->|RMS Volume Amplitude| H[🔮 Desktop Orb UI]
        G -.->|Echo Lock| B
    end
```

---

## 🌐 Real-Time Integrated Tools

Jarvis performs deterministic keyword pre-filtering before passing tools to Ollama to prevent model confusion:

| Capability | Example Prompt | Executed Tool | Provider / Data Source |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `MSFT`, etc.) |
| **🌐 Live Web Search** | *"Who won the game today?"* | `search_web` | DuckDuckGo Search API (`DDGS`) |
| **📰 Global Breaking News** | *"What is the latest breaking news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 General Knowledge** | *"Tell me about Quantum Computing"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Control** | *"Turn off the living room lights"* | `toggle_smart_lights` | Smart Home REST API |
| **⏰ System Utilities** | *"What time is it right now?"* | `get_current_time` | System Clock (`%I:%M %p`) |

---

## ⚙️ CLI Launch Options & Flags

```bash
# Default Smart Mode (RMS volume-gated acoustic echo lock)
python main.py

# Headphones Mode (Full duplex open mic - recommended for headsets)
python main.py --barge-in headphones

# Disabled Mode (Traditional half-duplex mic lock during speech output)
python main.py --barge-in disabled

# Specify custom Whisper STT model size (tiny.en, base.en, small.en, medium.en)
python main.py --stt-model small.en

# Run UI widget animation test
python ui_engine.py

# Run automated test suite
python -m unittest test_jarvis.py
```

### Containerized Deployment (Docker)
```bash
docker build -t local-voice-ai .
docker run -it --device /dev/snd --network host local-voice-ai
```

---

## 📁 Codebase Directory Breakdown

* **[main.py](main.py)**: System orchestrator. Initializes worker loops, manages global signal handlers (`SIGINT`/`SIGTERM`), and drives main-thread Cocoa GUI loops.
* **[audio_engine.py](audio_engine.py)**: Handles PyAudio microphone streams, Silero VAD edge processing, RMS volume calculation, and acoustic echo gating.
* **[stt_engine.py](stt_engine.py)**: Asynchronously transcribes speech audio buffers using `faster-whisper` (CTranslate2 `int8`/`fp16`) with VAD filter bypass.
* **[llm_engine.py](llm_engine.py)**: Ollama chat orchestrator with memory buffer pruning (20 messages max), regex sentence chunking, and deterministic tool routing.
* **[tts_engine.py](tts_engine.py)**: Synthesizes high-quality speech using Kokoro TTS (MPS/CUDA accelerated) and streams audio segments to PyAudio speakers.
* **[ui_engine.py](ui_engine.py)**: Floating Tkinter desktop widget rendering visual states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`) with drag-and-drop movement.
* **[test_jarvis.py](test_jarvis.py)**: Automated unit test suite covering tool keyword routing, memory pruning, and parameter extraction.
* **[Dockerfile](Dockerfile)**: Linux container configuration exposing host audio devices (`/dev/snd`).

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
