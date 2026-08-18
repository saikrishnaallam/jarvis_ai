# 🎙️ Jarvis: Low-Latency Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper-8A2BE2.svg?style=for-the-badge)](#)
[![LLM Model](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-FF6F00.svg?style=for-the-badge&logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20v1.0-FF69B4.svg?style=for-the-badge)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Jarvis** is an extensible, low-latency, 100% local voice assistant designed for natural spoken dialogue. Powered by Silero Voice Activity Detection (VAD), CTranslate2-accelerated Speech-to-Text (STT), deterministic local LLM orchestration with custom tool plugins, streaming Kokoro Text-to-Speech (TTS), and a floating animated Siri-like desktop orb widget.

---

## ⚡ Quick Start (3 Steps)

### 1. Install System Dependencies & Python Packages
```bash
# macOS (via Homebrew)
brew install portaudio espeak-ng

# Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

### 2. Pull Local LLM Model (Ollama)
Ensure [Ollama](https://ollama.com/) is running locally, then pull the lightweight Llama 3.2 model:
```bash
ollama pull llama3.2
```

### 3. Launch Jarvis
```bash
python main.py
```

---

## 🔮 Animated Desktop Orb UI

Jarvis features a floating, borderless desktop orb widget built with Tkinter that dynamically visualizes audio processing states:

```
  +-----------------------------------------------------------------------+
  | State       | Animation & Ring Dynamics                               |
  +-------------+---------------------------------------------------------+
  | IDLE        |  ( ( ( ⚪ ) ) )  Soft breathing white/gray glow ring     |
  | LISTENING   |  < < < 🔵 > > >  Pulsing cyan/blue audio capture ring   |
  | THINKING    |  / / / 🟣 \ \ \  Rotating morphing magenta sway ring    |
  | SPEAKING    |  { { { 🟢 } } }  Green ring reactive to volume amplitude|
  +-----------------------------------------------------------------------+
```

* **Click & Drag Repositioning**: Position the floating widget anywhere across your desktop screen.
* **macOS Transparency Fix**: Custom solid white oval canvas background rendering eliminates Cocoa window transparency compositing artifacts.
* **Volume Amplitude Reactive**: Avatar scale factor $S = 0.9 + 0.35 \cdot A_{\text{speaker}} + 0.05\sin(0.3 \cdot t)$ drives dynamic volume-responsive movement.

---

## 📊 Feature Comparison Matrix

| Feature | 🎙️ **Jarvis (Local AI)** | 🍏 **Apple Siri** | 🔊 **Amazon Alexa** | ☁️ **ChatGPT Voice** |
| :--- | :---: | :---: | :---: | :---: |
| **100% Local & Offline Privacy** | ✅ **Yes** | ❌ Partial | ❌ No | ❌ No |
| **Zero Monthly Subscription Fees** | ✅ **Yes** | ✅ Free | ✅ Free | ❌ $20+/mo |
| **Sub-280ms First-Syllable Latency**| ✅ **Yes** | ⚠️ Varies | ⚠️ ~1–2s | ⚠️ ~1.5–3s |
| **Smart Mid-Speech Barge-In** | ✅ **Yes** | ❌ No | ❌ No | ✅ Yes |
| **Real-Time Web Search & Stocks** | ✅ **Yes** | ⚠️ Basic | ⚠️ Basic | ✅ Yes |
| **Custom Plugin Tool Creation** | ✅ **Yes (Python)**| ❌ No | ❌ Custom Skills | ⚠️ Complex |
| **Hardware Acceleration (MPS/CUDA)**| ✅ **Yes** | N/A (Cloud) | N/A (Cloud) | N/A (Cloud) |

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

## 🔌 Plugin Developer Guide: Adding Custom Tools

Extending Jarvis with new custom Python tools is straightforward. Ollama automatically inspects Python function signatures, docstrings, and type hints to generate tool JSON schemas.

### Step 1: Write Your Tool Function in `llm_engine.py`
Define your Python function with clear type annotations and a descriptive docstring:

```python
# In llm_engine.py
def get_system_battery() -> str:
    """Get the current battery level and charging status of the device."""
    import psutil
    battery = psutil.sensors_battery()
    if battery:
        status = "charging" if battery.power_plugged else "discharging"
        return f"Battery level is {battery.percent}% and currently {status}."
    return "Battery information is unavailable."
```

### Step 2: Register Tool in `LLMEngine.__init__`
Add your function reference to `self.tools`:

```python
self.tools = [
    get_weather, 
    toggle_smart_lights, 
    get_current_time, 
    search_wikipedia, 
    get_latest_news, 
    search_web,
    get_system_battery  # <--- Added tool
]
```

### Step 3: Add Keyword Extraction to `get_relevant_tools`
Add deterministic keyword triggers in `get_relevant_tools()` to prevent false activations:

```python
if any(kw in text_lower for kw in ["battery", "charge", "power level"]):
    return [get_system_battery]
```

---

## ⚙️ CLI Configuration & Launch Options

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
* **[llm_engine.py](llm_engine.py)**: Ollama chat orchestrator with memory buffer pruning (20 messages max), regex sentence chunking, and tool routing.
* **[tts_engine.py](tts_engine.py)**: Synthesizes high-quality speech using Kokoro TTS (MPS/CUDA accelerated) and streams audio segments to PyAudio speakers.
* **[ui_engine.py](ui_engine.py)**: Floating Tkinter desktop widget rendering visual states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`) with drag-and-drop movement.
* **[test_jarvis.py](test_jarvis.py)**: Automated unit test suite covering tool keyword routing, memory pruning, and parameter extraction.
* **[Dockerfile](Dockerfile)**: Linux container configuration exposing host audio devices (`/dev/snd`).

---

## ❓ Troubleshooting & FAQs

<details>
<summary><b>1. How do I fix PyAudio compilation errors on macOS?</b></summary>
<br>
Ensure PortAudio system headers are installed via Homebrew:
<code>brew install portaudio espeak-ng</code><br>
If pip fails during PyAudio installation, specify include directories explicitly:
<code>pip install --global-option=build_ext --global-option="-I$(brew --prefix)/include" --global-option="-L$(brew --prefix)/lib" pyaudio</code>
</details>

<details>
<summary><b>2. How does Smart Barge-In stop acoustic feedback loops?</b></summary>
<br>
Jarvis monitors speaker playback volume ($A_{\text{speaker}}$) and microphone volume ($A_{\text{mic}}$). In <code>smart</code> mode, microphone input is locked only when $A_{\text{mic}} < \max(0.08, A_{\text{speaker}} \times 1.5)$. Speaking loudly or wearing headphones breaks the lock and interrupts active speech synthesis immediately.
</details>

<details>
<summary><b>3. Is GPU hardware acceleration supported?</b></summary>
<br>
Yes! Jarvis auto-detects hardware acceleration on startup:
<ul>
  <li><b>macOS Apple Silicon</b>: Uses Metal Performance Shaders (<code>MPS</code>) for PyTorch & Kokoro TTS.</li>
  <li><b>NVIDIA GPUs</b>: Uses <code>CUDA</code> and <code>float16</code> compute for Kokoro TTS and <code>faster-whisper</code> STT.</li>
</ul>
</details>

---

## 🤝 Contributing Guidelines

Contributions are welcome! Follow these steps to submit changes:

1. Fork the repository and create a feature branch (`git checkout -b feature/amazing-tool`).
2. Run unit tests to verify changes: `python -m unittest test_jarvis.py`.
3. Commit changes (`git commit -m "feat: add battery level plugin tool"`).
4. Push to your branch and open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
