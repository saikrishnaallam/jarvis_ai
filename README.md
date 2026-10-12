
     ___  ___  ____  _  _  ____  ___
    (_  )/ _ \(  _ \( \/ )(_  _)/ __)
   .-_)( )___/ )   / \  /  _)(_ \__ \
   \____)(__)  (_)\_)  \/  (____)(___/

    Local Voice AI Assistant
    ~~~~~~~~~~~~~~~~~~~~~~~~
    Fully local. Fully private. Sub-100ms latency.


+------------------------------------------------------------------+
|  ABOUT                                                           |
+------------------------------------------------------------------+

  Jarvis is a voice assistant that runs 100% on your machine.

  No cloud services. No API keys for the core pipeline. No data
  ever leaves your computer. You speak, it listens, it thinks,
  it talks back.

  The pipeline:

    mic -> Silero VAD -> faster-whisper -> Ollama (Llama 3.2) -> Kokoro TTS -> speaker
     |                                                                          |
     +<---- echo suppression gate (stops it from hearing itself) ----<----------+

  Target: sub-100ms from end-of-speech to first audio syllable
  on Apple Silicon (MPS) or NVIDIA (CUDA) hardware.


+------------------------------------------------------------------+
|  CAPABILITIES                                                    |
+------------------------------------------------------------------+

  Core:
    * Real-time voice activity detection (Silero VAD)
    * Local speech-to-text (faster-whisper, base.en)
    * Local LLM reasoning (Ollama, Llama 3.2)
    * Local text-to-speech (Kokoro TTS, af_heart voice)
    * Floating animated desktop orb (Tkinter, drag anywhere)
    * Barge-in / interrupt mid-sentence
    * Echo loop suppression

  Live tools (invoked automatically when needed):
    * Stock prices ........... Yahoo Finance
    * Web search ............. DuckDuckGo
    * Breaking news .......... Google News RSS
    * Facts & knowledge ...... Wikipedia
    * Weather ................ OpenWeather API
    * Smart lights ........... REST API
    * Current time ........... System clock


+------------------------------------------------------------------+
|  SETUP                                                           |
+------------------------------------------------------------------+

  You need:
    - Python 3.11+
    - Ollama (https://ollama.com)
    - PortAudio + espeak-ng

  1) System deps:

     macOS:
       $ brew install portaudio espeak-ng

     Linux:
       $ sudo apt-get install -y portaudio19-dev alsa-utils \
             libasound2-dev espeak-ng

  2) Python deps:

       $ pip install -r requirements.txt

  3) Pull the model:

       $ ollama pull llama3.2

  4) Go:

       $ python main.py


+------------------------------------------------------------------+
|  PROJECT FILES                                                   |
+------------------------------------------------------------------+

  jarvis_ai/
  |
  +-- main.py               orchestrator, signal handling, UI loop
  +-- audio_engine.py        mic input, Silero VAD, echo gating
  +-- stt_engine.py          faster-whisper transcription worker
  +-- llm_engine.py          Ollama chat, memory, tool dispatch
  +-- tts_engine.py          Kokoro TTS, hw accel, audio streaming
  +-- ui_engine.py           desktop orb widget, animations
  +-- test_jarvis.py         unit tests for tools & memory
  +-- requirements.txt       python deps
  +-- Dockerfile             linux container w/ audio passthrough
  +-- .gitignore             excludes bytecode, venvs, os files


+------------------------------------------------------------------+
|  USAGE                                                           |
+------------------------------------------------------------------+

  Run:
    $ python main.py

  Barge-in modes:
    $ python main.py --barge-in smart        (default, RMS gated)
    $ python main.py --barge-in headphones   (full duplex)
    $ python main.py --barge-in disabled     (half duplex)

  Whisper model sizes: tiny.en, base.en, small.en, medium.en
    $ python main.py --stt-model small.en

  Test orb widget standalone:
    $ python ui_engine.py

  Unit tests:
    $ python -m unittest test_jarvis.py

  Docker (Linux):
    $ docker build -t local-voice-ai .
    $ docker run -it --device /dev/snd --network host local-voice-ai


+------------------------------------------------------------------+
|  PERFORMANCE NOTES                                               |
+------------------------------------------------------------------+

  * TTS runs in background thread, dispatches audio via
    loop.call_soon_threadsafe. Output startup: ~50ms.

  * Whisper VAD filter disabled (vad_filter=False). Silero
    already handles it. Saves 100-300ms per utterance.

  * Silence endpoint: 0.35s (was 1.2s). Transcription fires
    the instant you stop speaking.

  * Greedy LLM decoding: temperature=0.0, num_ctx=1024,
    num_predict=50. No sampling overhead.

  * macOS Cocoa fix: transparent Tkinter canvases break on
    macOS. Workaround: dynamic white oval behind avatar.

  * Tkinter GC fix: pin PhotoImage refs to canvas to prevent
    Python garbage collector from dropping them.


+------------------------------------------------------------------+
|  HARDWARE                                                        |
+------------------------------------------------------------------+

  Minimum:                      Recommended:
    8 GB RAM                      16 GB+ RAM (M-series / NVIDIA)
    5 GB disk                     10 GB disk
    Any mic                       USB mic or headset
    macOS 12+ / Linux             macOS 14+ Apple Silicon


+------------------------------------------------------------------+
|  CHANGELOG                                                       |
+------------------------------------------------------------------+

  2026-08-04  base.en default + --stt-model flag
  2026-08-04  deterministic tool routing (no hallucinated calls)
  2026-08-04  web search, stock quotes, breaking news integration
  2026-08-04  auto-route political/leader queries to search
  2026-08-04  orb drag, macOS fix, MPS/CUDA accel, memory pruning


+------------------------------------------------------------------+
|  LICENSE                                                         |
+------------------------------------------------------------------+

  MIT. See LICENSE file.


+------------------------------------------------------------------+
