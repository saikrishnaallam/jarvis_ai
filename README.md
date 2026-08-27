# 🎙️ Jarvis: Low-Latency Local Voice AI Assistant

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=apple&logoColor=white)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C280ms-blueviolet.svg?style=for-the-badge)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=for-the-badge)](#)
[![Hardware Acceleration](https://img.shields.io/badge/Hardware-Apple%20MPS%20%7C%20NVIDIA%20CUDA-blue.svg?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

> **Jarvis** is an in-depth, low-latency, 100% local voice assistant designed for natural spoken dialogue. Operating entirely on consumer hardware (macOS Apple Silicon or Linux CUDA/CPU), Jarvis integrates edge Voice Activity Detection (VAD), CTranslate2-accelerated Speech-to-Text (STT), deterministic local LLM orchestration with live web search & stock lookups, streaming Kokoro Text-to-Speech (TTS), and a floating animated Siri-like desktop orb widget.

---

## 📐 System Architecture & Subsystem Pipeline

Jarvis uses an asynchronous, multi-threaded event-driven pipeline to minimize end-to-end latency while eliminating acoustic feedback loops and speaker self-transcription.

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
        
        LLMEngine <-->|Tool Invocation| Tools[🛠️ Python Tools\n(Web Search, Yahoo Finance, Google News, Weather)]
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

| Pipeline Stage | Engine / Model | Hardware Target | Execution Strategy | Latency Contribution |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | PyAudio / `sounddevice` | CPU | 32ms audio block frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence threshold | `< 5 ms` (inference) |
| **STT Transcription** | `faster-whisper` (`base.en`) | CTranslate2 `int8`/`fp16` | Greedy (`beam_size=1`), VAD-bypass (`vad_filter=False`) | `45 – 90 ms` |
| **LLM Time-To-First-Token**| Ollama (`llama3.2`) | MPS / CUDA | Context window: 1024 tokens, greedy decoding (`temperature=0.0`) | `70 – 120 ms` |
| **LLM Sentence Chunking**| Regex Match (`(?<!\d)[.!?]\s`) | CPU | Flushes sentences immediately as punctuation matches | `< 1 ms` |
| **TTS First Chunk Synthesis**| Kokoro v1.0 (`af_heart`) | MPS / CUDA | Generator yielding sentence audio chunks | `30 – 50 ms` |
| **Playback Buffer Delay** | PyAudio `OutputStream` | CPU | 4096-frame ring buffer | `< 10 ms` |
| **Total First-Syllable Latency**| **Entire System** | **MPS / CUDA** | **Parallelized streaming audio pipeline** | **~200 – 280 ms** |

---

## 🧵 Thread Concurrency Model

1. **Main Thread (Tkinter GUI & Signal Handlers)**:
   - macOS Cocoa requires native window management to execute on the main thread.
   - `UIEngine.start()` runs `self.root.mainloop()` on line [113 in main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py#L113).
   - Signal handlers (`SIGINT`, `SIGTERM`) intercept exit requests and execute cleanup callbacks thread-safely.

2. **Asyncio Event Loop Daemon Thread**:
   - Instantiated in `run_asyncio_thread()` on line [92 in main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py#L92).
   - Manages thread-safe queues: `raw_audio_queue`, `speech_buffer_queue`, `text_queue`, `tts_queue`, and `audio_playback_queue`.
   - Runs worker loops via `asyncio.gather()` for input capture, STT processing, LLM generation, TTS synthesis, and audio playback.

3. **PortAudio C-Callback Threads**:
   - `_audio_callback` (Microphone): Fired by `sounddevice` whenever a 32ms audio frame is ready. Pushes NumPy arrays into `raw_audio_queue` via `self.loop.call_soon_threadsafe`.
   - `_callback` (Speaker): Fired by `sounddevice` to fill output audio buffers. Evaluates real-time RMS amplitude and enforces echo locks.

4. **Background Synthesis Thread**:
   - `synthesis_worker` offloads heavy PyTorch Kokoro model generation to a worker thread using `asyncio.to_thread(_stream_synthesis)`.
   - Synthesized PCM chunks are safely dispatched back to the main event loop queue using `loop.call_soon_threadsafe`.

---

## 🔇 Echo Suppression & RMS Mathematical Model

Let $A_{\text{mic}}$ be the peak absolute amplitude of the incoming microphone chunk:
$$A_{\text{mic}} = \max(|x_{\text{mic}}|)$$

Let $A_{\text{speaker}}$ be the current peak amplitude of the speaker playback buffer:
$$A_{\text{speaker}} = \max(|x_{\text{speaker}}|)$$

The acoustic lock decision $\text{Lock}_{\text{mic}}$ is calculated as:
$$\text{Lock}_{\text{mic}} = \begin{cases} 
\text{True} & \text{if } \text{Mode} = \text{"disabled"} \\
\text{False} & \text{if } \text{Mode} = \text{"headphones"} \\
A_{\text{mic}} < \max\left(0.08, A_{\text{speaker}} \times 1.5\right) & \text{if } \text{Mode} = \text{"smart"}
\end{cases}$$

When $\text{Lock}_{\text{mic}} = \text{True}$, microphone audio buffers are cleared and transcription is suppressed. If $A_{\text{mic}}$ exceeds the threshold in `smart` mode, speech onset is registered, setting `barge_in_event` and stopping active TTS synthesis immediately.

---

## 🛠️ Deterministic Tool Routing & Execution

To eliminate tool calling hallucinations common in smaller LLMs, `LLMEngine.get_relevant_tools()` in [llm_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/llm_engine.py#L190) performs pre-filtering before invoking Ollama.

| Capability | Example Query | Tool Executed | Provider / Data Source |
| :--- | :--- | :--- | :--- |
| **📈 Real-Time Stocks** | *"What is Tesla's stock price today?"* | `search_web` | Yahoo Finance API (`TSLA`, `AAPL`, `MSFT`, etc.) |
| **🌐 Live Web Search** | *"Who won the game today?"* | `search_web` | DuckDuckGo Search API (`DDGS`) |
| **📰 Global Breaking News** | *"What is the latest breaking news?"* | `get_latest_news` | Google News RSS Feed |
| **📚 General Knowledge** | *"Tell me about Quantum Computing"* | `search_wikipedia` | Wikipedia REST API |
| **☀️ Live Weather** | *"What's the weather in Tokyo?"* | `get_weather` | OpenWeather API |
| **💡 Smart Home Control** | *"Turn off the living room lights"* | `toggle_smart_lights` | Smart Home REST API |
| **⏰ System Utilities** | *"What time is it right now?"* | `get_current_time` | System Clock (`%I:%M %p`) |

---

## 🎨 UI Render Loop & macOS Transparency Fix

The desktop widget (`UIEngine` in [ui_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/ui_engine.py)) renders a floating, borderless Tkinter window (`overrideredirect(True)`, `attributes("-topmost", True)`).

* **State Machine Transitions**: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`.
* **macOS Cocoa Transparency Fix**: Standard transparent Tkinter canvases composite alpha channels against transparent window backgrounds. Resolved by rendering a solid white canvas background (`canvas.create_oval`) matching the dynamic avatar scale factor $S = 0.9 + 0.35 \cdot A_{\text{speaker}} + 0.05\sin(0.3 \cdot t)$ directly behind the image.
* **Garbage Collection Protection**: `self.canvas.image = self.avatar_img` prevents Python GC sweeps from dropping image frame references.

---

## ⚡ Quick Start & Installation

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
```bash
ollama pull llama3.2
```

### 3. Launch Assistant
```bash
python main.py
```

### CLI Launch Flags & Testing
```bash
# Launch Smart Mode (Default RMS volume-gated barge-in)
python main.py

# Launch Headphones Mode (Full duplex open mic)
python main.py --barge-in headphones

# Custom Whisper STT Model Selection
python main.py --stt-model small.en

# Run Standalone UI Animation Test
python ui_engine.py

# Run Automated Test Suite
python -m unittest test_jarvis.py
```

---

## 📁 Codebase Directory Breakdown

* **[main.py](main.py)**: System orchestrator. Manages thread boundaries, signal handlers (`SIGINT`/`SIGTERM`), and Cocoa GUI execution.
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
