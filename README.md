
                    ____  ___  ____  _  _  ____  ___
                   (_  _)/ _ \(  _ \( \/ )(_  _)/ __)
                  .-_)(  )___/ )   / \  /  _)(_ \__ \
                  \____)(__)  (_)\_)  \/  (____)(___/

                   LOCAL VOICE AI ASSISTANT v1.0
                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
              "Your own private AI, running on your machine."


========================================================================
  WHAT IS THIS?
========================================================================

  Jarvis is a voice assistant that runs entirely on your local machine.
  No cloud. No API keys for core functionality. No data leaves your
  computer. You talk, it listens, it thinks, it speaks back.

  It chains together four open-source engines in a tight loop:

      Microphone --> Silero VAD --> faster-whisper --> Ollama --> Kokoro TTS --> Speaker
         |                                                                       |
         +------- adaptive echo gate (prevents self-hearing loop) <--------------+

  The whole pipeline targets sub-100ms first-syllable latency on
  Apple Silicon and NVIDIA GPU hardware.


========================================================================
  WHAT CAN IT DO?
========================================================================

  * Listen to you via microphone with real-time voice activity detection
  * Transcribe your speech locally using faster-whisper (base.en model)
  * Think and respond using Ollama with Llama 3.2 (runs locally)
  * Speak responses back using Kokoro TTS with hardware acceleration
  * Show a floating animated desktop orb (Siri-like, drag anywhere)
  * Interrupt it mid-sentence (barge-in) without breaking the pipeline
  * Suppress echo loops so it doesn't transcribe its own voice

  When it needs live data, it can also:

    - Pull real-time stock prices .... Yahoo Finance (TSLA, AAPL, etc.)
    - Search the web ................ DuckDuckGo
    - Get breaking news ............. Google News RSS
    - Look up facts ................. Wikipedia
    - Check the weather ............. OpenWeather API
    - Control smart lights .......... Smart Home REST API
    - Tell you the time ............. System clock


========================================================================
  GETTING STARTED
========================================================================

  Prerequisites:

    - Python 3.11 or newer
    - Ollama (https://ollama.com) installed and running
    - PortAudio and espeak-ng system libraries

  Step 1: Install system dependencies

    macOS:
      $ brew install portaudio espeak-ng

    Linux (Debian/Ubuntu):
      $ sudo apt-get update
      $ sudo apt-get install -y portaudio19-dev alsa-utils \
          libasound2-dev espeak-ng

  Step 2: Install Python packages

      $ pip install -r requirements.txt

  Step 3: Pull the LLM model

      $ ollama pull llama3.2

  Step 4: Run it

      $ python main.py

  That's it. Start talking.


========================================================================
  FILES
========================================================================

  jarvis_ai/
  |
  |-- main.py              Main entry point. Starts the async pipeline,
  |                        handles signals (SIGINT/SIGTERM), runs UI.
  |
  |-- audio_engine.py      Microphone capture via PyAudio. Runs Silero
  |                        VAD for speech detection. Manages echo gate.
  |
  |-- stt_engine.py        Speech-to-text via faster-whisper. Consumes
  |                        audio buffers from VAD queue.
  |
  |-- llm_engine.py        Chat engine via Ollama API. Manages memory,
  |                        prompt engineering, sentence chunking, and
  |                        deterministic tool/function calling.
  |
  |-- tts_engine.py        Text-to-speech via Kokoro. Hardware accel
  |                        on MPS (Apple) and CUDA (NVIDIA). Streams
  |                        audio segments with amplitude tracking.
  |
  |-- ui_engine.py         Floating desktop orb widget in Tkinter.
  |                        Animates: breathing (listen), swaying
  |                        (think), scaling (speak). Drag to move.
  |
  |-- test_jarvis.py       Unit tests for tool routing, memory
  |                        pruning, and parameter extraction.
  |
  |-- requirements.txt     Python dependencies.
  |-- Dockerfile           Docker config for Linux audio passthrough.
  |-- .gitignore           Ignores bytecode, venvs, OS junk.


========================================================================
  COMMAND LINE OPTIONS
========================================================================

  Basic usage:

      $ python main.py

  Barge-in modes:

      $ python main.py --barge-in smart       # default, volume-gated
      $ python main.py --barge-in headphones   # full duplex, open mic
      $ python main.py --barge-in disabled     # half duplex, mic lock

  Change the Whisper model (tiny.en / base.en / small.en / medium.en):

      $ python main.py --stt-model small.en

  Test the desktop orb widget by itself:

      $ python ui_engine.py

  Run unit tests:

      $ python -m unittest test_jarvis.py

  Docker (Linux only, needs host audio access):

      $ docker build -t local-voice-ai .
      $ docker run -it --device /dev/snd --network host local-voice-ai


========================================================================
  HOW IT STAYS FAST
========================================================================

  - Kokoro TTS runs in a background thread; audio chunks dispatch
    via loop.call_soon_threadsafe. Startup delay: ~50ms.

  - Whisper's internal VAD filter is OFF (vad_filter=False). We
    already did VAD with Silero, so the second pass is redundant.
    Saves 100-300ms per transcription.

  - Silence endpoint is set to 0.35 seconds (down from 1.2s).
    Transcription starts the instant you stop talking.

  - LLM runs greedy (temperature=0.0, num_ctx=1024, num_predict=50).
    Fast, deterministic, no sampling overhead.

  - macOS transparency hack: Tkinter canvas alpha compositing is
    broken on Cocoa. Fixed with a dynamic white background oval
    that tracks the avatar's exact scale.

  - PhotoImage GC fix: Python's garbage collector drops Tkinter
    image refs. Solved by pinning them to the canvas widget.


========================================================================
  HARDWARE
========================================================================

  Minimum:
    - 8 GB RAM
    - 5 GB disk space
    - Any microphone
    - macOS 12+ or Linux

  Recommended:
    - 16 GB+ RAM with Apple Silicon or NVIDIA GPU
    - 10 GB disk (room for multiple Whisper/Ollama models)
    - Dedicated USB microphone or headset
    - macOS 14+ on M-series chip


========================================================================
  CHANGELOG
========================================================================

  2026-08-04  Upgraded default Whisper model to base.en. Added
              --stt-model CLI flag for model selection.

  2026-08-04  Implemented deterministic get_relevant_tools routing
              in llm_engine.py. No more hallucinated tool calls.

  2026-08-04  Added real-time web search (DuckDuckGo), stock quotes
              (Yahoo Finance), and breaking news (Google News RSS).

  2026-08-04  Auto-route political/leader queries to web search.

  2026-08-04  Desktop orb: drag-to-reposition, macOS transparency
              fix, MPS/CUDA auto-acceleration, memory pruning.


========================================================================
  LICENSE
========================================================================

  MIT License. See LICENSE file for details.


========================================================================

  "It's not about the algorithm. It's about the latency."

========================================================================
