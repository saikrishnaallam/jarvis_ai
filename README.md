# Jarvis: Low-Latency Local Voice AI Assistant 🎙️🤖

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](#)
[![Audio Pipeline](https://img.shields.io/badge/Audio-PyAudio%20%7C%20sounddevice-008080.svg)](#)
[![VAD Engine](https://img.shields.io/badge/VAD-Silero%20VAD%20v4-FF6F00.svg)](#)
[![STT Engine](https://img.shields.io/badge/STT-faster--whisper%20(CTranslate2)-8A2BE2.svg)](#)
[![LLM Engine](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-00599C.svg?logo=ollama&logoColor=white)](#)
[![TTS Engine](https://img.shields.io/badge/TTS-Kokoro%20v1.0%20(MPS%2FCUDA)-FF69B4.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

**Jarvis** is a low-latency, privacy-preserving, local-first voice AI assistant designed for real-time natural spoken dialogue. Running 100% locally on consumer hardware (macOS Apple Silicon or Linux CUDA/CPU), Jarvis integrates edge Voice Activity Detection (VAD), CTranslate2-accelerated Speech-to-Text (STT), deterministic tool calling with an Ollama LLM orchestrator, streaming Kokoro Text-to-Speech (TTS), and a Tkinter-based floating desktop widget.

---

## 📐 Deep-Dive Architecture & Data Pipeline

Jarvis uses an asynchronous, multi-threaded event-driven pipeline to minimize end-to-end latency while preventing acoustic feedback loops and speaker-to-microphone self-transcription.

```mermaid
flowchart TB
    subgraph Threads ["Thread & Execution Boundaries"]
        direction TB
        MainThread["🧵 Main GUI Thread\n(Tkinter root loop, Cocoa UI, Signal Handlers)"]
        AsyncThread["🧵 Asyncio Event Loop Thread\n(Workers, Queues, Signal Dispatcher)"]
        MicThread["🧵 PortAudio Mic InputStream Callback\n(Chunk Producer @ 16kHz float32)"]
        SpeakerThread["🧵 PortAudio Speaker OutputStream Callback\n(Audio Consumer @ 24kHz float32)"]
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

## ⏱️ Latency Benchmarks & Component Specs

The table below details component-level execution specs and latency contributions measured on Apple Silicon (M-series MPS):

| Pipeline Stage | Engine / Model | Hardware Target | Processing Strategy | Latency Contribution |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Capture** | PyAudio / `sounddevice` | CPU | 32ms audio block frames (512 samples @ 16kHz) | `32 ms` |
| **VAD Endpointing** | Silero VAD v4 | PyTorch (CPU) | Chunk probability scoring; `0.35s` silence endpoint | `< 5 ms` (inference) |
| **STT Transcription** | `faster-whisper` (`base.en`) | CTranslate2 `int8`/`fp16` | Greedy decoding (`beam_size=1`), VAD-bypass (`vad_filter=False`) | `45 – 90 ms` |
| **LLM Time-To-First-Token**| Ollama (`llama3.2`) | MPS / CUDA | Context window: 1024 tokens, greedy decoding (`temperature=0.0`) | `70 – 120 ms` |
| **LLM Sentence Chunking**| Regex Match (`(?<!\d)[.!?]\s`) | CPU | Flushes sentences immediately as punctuation matches | `< 1 ms` |
| **TTS First Chunk Synthesis**| Kokoro v1.0 (`af_heart`) | MPS / CUDA | Generator yielding sentence audio chunks | `30 – 50 ms` |
| **Playback Buffer Delay** | PyAudio `OutputStream` | CPU | 4096-frame ring buffer | `< 10 ms` |
| **Total First-Syllable Latency**| **Entire System** | **MPS / CUDA** | **Parallelized streaming audio pipeline** | **~200 – 280 ms** |

---

## 🧵 Concurrency & Multithreading Architecture

Jarvis avoids blocking the event loop or main thread by partitioning execution across distinct execution contexts:

1. **Main Thread (Tkinter GUI & Signal Handlers)**:
   - macOS Cocoa requires native window management to execute on the main thread.
   - `UIEngine.start()` runs `self.root.mainloop()` on line [113 in main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py#L113).
   - Signal handlers (`SIGINT`, `SIGTERM`) intercept exit requests and execute cleanup callbacks thread-safely.

2. **Asyncio Event Loop Daemon Thread**:
   - Instantiated in `run_asyncio_thread()` on line [92 in main.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/main.py#L92).
   - Manages asynchronous queues: `raw_audio_queue`, `speech_buffer_queue`, `text_queue`, `tts_queue`, and `audio_playback_queue`.
   - Runs concurrent tasks via `asyncio.gather()` for input capture, STT processing, LLM generation, TTS synthesis, and audio playback.

3. **PortAudio C-Callback Threads**:
   - `_audio_callback` (Microphone): Fired by `sounddevice` whenever a 32ms audio frame is ready. Pushes NumPy arrays into `raw_audio_queue` via `self.loop.call_soon_threadsafe`.
   - `_callback` (Speaker): Fired by `sounddevice` to fill output audio buffers. Evaluates real-time RMS amplitude and enforces echo locks.

4. **Background Synthesis Thread**:
   - `synthesis_worker` offloads heavy PyTorch Kokoro model generation to a worker thread using `asyncio.to_thread(_stream_synthesis)`.
   - Synthesized PCM chunks are safely dispatched back to the main event loop queue using `loop.call_soon_threadsafe`.

---

## 🔇 Echo Suppression & Smart Barge-In Mechanics

To prevent the assistant from hearing and transcribing its own voice output while allowing natural user interruptions, Jarvis implements an adaptive echo-suppression model.

```
       +--------------------------------------------------------+
       |               Microphone Input Frame                   |
       +--------------------------------------------------------+
                                   |
                                   v
                    +------------------------------+
                    |  Is TTS Engine Playing Audio?|
                    +------------------------------+
                               /        \
                             Yes         No
                             /            \
                            v              v
         +------------------------+   +-------------------------------+
         | Check Barge-In Mode    |   | Is Echo Cooldown Active?      |
         +------------------------+   | (Time since playback < 0.35s) |
          /          |         \      +-------------------------------+
    "disabled"    "smart"  "headphones"      /               \
        |            |          |          Yes                No
        v            v          v          /                   \
    Lock Mic     Compare RMS  No Lock  Lock Mic           Process Silero
                Amplitude               & Discard           VAD Chunk
```

### Mathematical Model for Smart Barge-In
Let $A_{\text{mic}}$ be the peak absolute amplitude of the incoming microphone chunk:
$$A_{\text{mic}} = \max(|x_{\text{mic}}|)$$

Let $A_{\text{speaker}}$ be the current peak amplitude of the speaker playback buffer:
$$A_{\text{speaker}} = \max(|x_{\text{speaker}}|)$$

The acoustic lock decision $\text{Lock}_{\text{mic}}$ is evaluated as follows:
$$\text{Lock}_{\text{mic}} = \begin{cases} 
\text{True} & \text{if } \text{Mode} = \text{"disabled"} \\
\text{False} & \text{if } \text{Mode} = \text{"headphones"} \\
A_{\text{mic}} < \max\left(0.08, A_{\text{speaker}} \times 1.5\right) & \text{if } \text{Mode} = \text{"smart"}
\end{cases}$$

When $\text{Lock}_{\text{mic}} = \text{True}$, microphone audio buffers are cleared, VAD state is reset, and transcription is suppressed. If $A_{\text{mic}}$ exceeds the threshold in `smart` mode, speech onset is registered, setting `barge_in_event` and stopping active TTS synthesis immediately.

---

## 🛠️ Deterministic Tool Routing Engine

To eliminate tool calling hallucinations common in smaller open-weights LLMs, `LLMEngine.get_relevant_tools()` in [llm_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/llm_engine.py#L190) performs deterministic pre-filtering before invoking Ollama.

```mermaid
graph TD
    UserQuery["User Input Query"] --> FilterGreeting{"Is Greeting?\n('how are you', 'whats up')"}
    FilterGreeting -- Yes --> PassNoTools["Pass Empty Tool List []\n(Pure Chat Response)"]
    FilterGreeting -- No --> CheckWeather{"Contains Weather Keywords?\n('weather', 'forecast', 'temp')"}
    
    CheckWeather -- Yes --> ToolWeather["Bind get_weather Tool"]
    CheckWeather -- No --> CheckLights{"Contains Smart Home Keywords?\n('light', 'lamp', 'switch')"}
    
    CheckLights -- Yes --> ToolLights["Bind toggle_smart_lights Tool"]
    CheckLights -- No --> CheckTime{"Contains Clock/Time Keywords?\n('time', 'clock', 'date')"}
    
    CheckTime -- Yes --> ToolTime["Bind get_current_time Tool"]
    CheckTime -- No --> CheckNews{"Contains Breaking News Keywords?\n('news', 'happen today')"}
    
    CheckNews -- Yes --> ToolNews["Bind get_latest_news Tool"]
    CheckNews -- No --> CheckSearch{"Contains Search / Info Keywords?\n('who', 'what', 'stock', 'price', '?')"}
    
    CheckSearch -- Yes --> ToolSearch["Bind search_web Tool"]
    CheckSearch -- No --> PassNoTools
```

### Available Plugin Tools

1. **`search_web(query: str)`**:
   - Parses stock ticker queries against Yahoo Finance API (`TSLA`, `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `META`, `NFLX`, `AMD`, `INTC`).
   - Executes live DuckDuckGo text searches via `duckduckgo_search` (`DDGS`).
2. **`get_latest_news()`**:
   - Parses Google News RSS XML (`https://news.google.com/rss`) for live headlines and timestamps.
3. **`search_wikipedia(query: str)`**:
   - Two-step REST lookup: queries search endpoints for top matching page titles, then fetches article extracts via Wikipedia REST API (`/api/rest_v1/page/summary`).
4. **`get_weather(location: str)`**:
   - Returns real-time weather metrics for target location.
5. **`toggle_smart_lights(room: str, state: str)`**:
   - Controls smart home lighting states via HomeAssistant/REST API integration.
6. **`get_current_time()`**:
   - Formats localized system clock timestamps (`%I:%M %p`).

---

## 🎨 UI Render Loop & Dynamic Orb Mechanics

The desktop widget (`UIEngine` in [ui_engine.py](file:///Users/saikrishnaallam/Desktop/jarvis_ai/ui_engine.py)) renders a floating, borderless Tkinter window (`overrideredirect(True)`, `attributes("-topmost", True)`).

### State Machine Transitions
* **`IDLE`**: Soft breathing white ring ($R = 58 + 2\sin(0.05 \cdot t)$).
* **`LISTENING`**: Dual cyan/blue glowing rings ($R = 62 + 8\sin(0.15 \cdot t)$).
* **`THINKING`**: Rotating magenta/purple morphing rings ($R = 64 + 5\sin(0.25 \cdot t)$).
* **`SPEAKING`**: Dynamic teal/green rings scaling proportionally with speaker RMS volume:
$$R_{\text{speaking}} = 58 + 35 \cdot \min(A_{\text{speaker}}, 1.0) + 3\sin(0.1 \cdot t)$$

```
               [ User Speech Onset ]
       +-----------------------------------+
       |                                   v
   +-------+   [VAD Endpoint]   +----------+
   | IDLE  | -----------------> |LISTENING |
   +-------+                    +----------+
       ^                                 |
       |                         [STT Complete]
  [Turn End]                             v
       |                        +----------+
       +----------------------- | THINKING |
       |                        +----------+
       |                                 |
   +----------+                  [TTS Playback]
   | SPEAKING | <------------------------+
   +----------+
```

### macOS Alpha Channel Compositing Fix
Standard transparent Tkinter windows on macOS Cocoa composite transparent PNG alpha channels against empty window backgrounds, creating grey box artifacts. Fixed by rendering a solid white circular canvas background (`canvas.create_oval`) matching the dynamic avatar scale factor $S = 0.9 + 0.35 \cdot A_{\text{speaker}} + 0.05\sin(0.3 \cdot t)$ directly behind the image.

---

## 📁 Codebase Directory Breakdown

* **[main.py](main.py)**: System orchestrator. Manages thread initialization, signal handlers (`SIGINT`/`SIGTERM`), and main-thread Tkinter execution.
* **[audio_engine.py](audio_engine.py)**: Microphone input pipeline. Runs Silero VAD, calculates RMS chunk amplitude, and enforces barge-in locks.
* **[stt_engine.py](stt_engine.py)**: Async wrapper for `faster-whisper`. Consumes audio buffers and yields transcribed text offloaded to worker threads.
* **[llm_engine.py](llm_engine.py)**: Ollama client orchestrator. Manages conversation memory buffer (pruned to 20 messages), regex sentence splitting, and tool routing.
* **[tts_engine.py](tts_engine.py)**: Kokoro TTS pipeline wrapper. Synthesizes audio segments on MPS/CUDA and feeds `sounddevice` playback queues.
* **[ui_engine.py](ui_engine.py)**: Animated Tkinter desktop widget supporting drag-and-drop repositioning and state-driven ring synthesis.
* **[test_jarvis.py](test_jarvis.py)**: Unit test suite for deterministic tool routing, keyword extraction, and conversation memory pruning.
* **[Dockerfile](Dockerfile)**: Container manifest exposing Linux host sound devices (`/dev/snd`).
* **[requirements.txt](requirements.txt)**: Python dependency specifications.

---

## 🚀 Installation & Command Line Interface

### 1. Prerequisites
```bash
# macOS (Homebrew)
brew install portaudio espeak-ng

# Debian/Ubuntu Linux
sudo apt-get update && sudo apt-get install -y portaudio19-dev alsa-utils libasound2-dev espeak-ng

# Install Python requirements
pip install -r requirements.txt
```

### 2. Pull Ollama Model
```bash
ollama pull llama3.2
```

### 3. Launch Command Syntax
```bash
python main.py [OPTIONS]
```

| Flag | Choices | Default | Description |
| :--- | :--- | :--- | :--- |
| `--barge-in` | `smart`, `headphones`, `disabled` | `smart` | **`smart`**: RMS volume-gated acoustic lock.<br>**`headphones`**: Open-mic full duplex.<br>**`disabled`**: Mic lock during speech output. |
| `--stt-model` | `tiny.en`, `base.en`, `small.en`, `medium.en` | `base.en` | Selects `faster-whisper` transcription model size. |

### 4. Running Unit Tests
```bash
python -m unittest test_jarvis.py
```

### 5. Docker Container Deployment (Linux)
```bash
docker build -t local-voice-ai .
docker run -it --device /dev/snd --network host local-voice-ai
```

---

## 📜 Version History & Major Changelogs

- **2026-08-04**: Default Whisper model updated to `base.en`; added CLI flag `--stt-model`.
- **2026-08-04**: Added deterministic keyword pre-filtering (`get_relevant_tools`) in `llm_engine.py`.
- **2026-08-04**: Integrated real-time web search (`search_web`), Yahoo Finance stock lookup, and Google News RSS feed parsing (`get_latest_news`).
- **2026-08-04**: Optimized desktop widget canvas rendering for macOS Cocoa window transparency; added MPS/CUDA hardware autodetect for Kokoro TTS.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
