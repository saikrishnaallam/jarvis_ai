# main.py: The orchestrator (start here)
import asyncio
import signal
import sys
import threading

# Import our custom modules
from audio_engine import AudioPipeline
from stt_engine import STTEngine
from llm_engine import LLMEngine
from tts_engine import TTSEngine
from ui_engine import UIEngine

# Global references for signal handling
global_loop = None
global_ui_engine = None

def handle_sigint(signum, frame):
    """Triggered by Ctrl+C or kill signals on the main thread."""
    global global_loop, global_ui_engine
    print("\nReceived exit signal. Shutting down Voice AI Engine...")
    
    # 1. Close Tkinter UI on main thread
    if global_ui_engine:
        try:
            global_ui_engine.close()
        except Exception:
            pass
            
    # 2. Cancel asyncio tasks thread-safely
    if global_loop and global_loop.is_running():
        global_loop.call_soon_threadsafe(cancel_all_tasks, global_loop)

def cancel_all_tasks(loop):
    """Cancels all currently scheduled tasks in the loop."""
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    print(f"Cancelling {len(tasks)} outstanding background tasks...")
    for task in tasks:
        task.cancel()

async def main(ui_engine, barge_in_mode="smart"):
    print("🚀 Initializing Local Voice Assistant...")

    # 1. Global State & Queues
    barge_in_event = asyncio.Event()
    
    # 2. Instantiate all modules
    audio_engine = AudioPipeline(barge_in_mode=barge_in_mode)          # Connects Mic -> VAD (creates its own speech queue)
    stt_engine = STTEngine()                # Transcribes endpointed speech
    llm_engine = LLMEngine()                # Ollama chat orchestrator with custom tools
    tts_engine = TTSEngine()                # Kokoro TTS + Speaker playback
    
    # Wait a moment for models to load into memory
    await asyncio.sleep(1)
    
    # Start background daemon thread to listen for console Enter press interrupts (manual barge-in)
    def read_console_keys():
        loop = asyncio.get_running_loop()
        import sys
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                # Safely trigger event in event loop from the thread
                loop.call_soon_threadsafe(barge_in_event.set)
                print("\n⌨️ [Console] Interruption triggered by user!")
            except Exception:
                break
                
    threading.Thread(target=read_console_keys, daemon=True).start()
    
    print("\n🟢 All systems online. Say something!")
    
    try:
        # 3. Launch all worker loops concurrently
        await asyncio.gather(
            # Input pipeline
            audio_engine.vad_processing_loop(tts_engine, ui_engine),
            stt_engine.process_speech_queue(audio_engine.speech_buffer_queue),
            
            # Orchestration
            llm_engine.process_text_queue(stt_engine.text_queue, barge_in_event),
            
            # Output pipeline
            tts_engine.synthesis_worker(llm_engine.tts_queue, barge_in_event),
            tts_engine.playback_worker(barge_in_event, ui_engine),
        )
    except asyncio.CancelledError:
        pass # Expected on shutdown

def run_asyncio_thread(loop, ui_engine, barge_in_mode="smart"):
    """Runs the asyncio event loop inside a daemon thread."""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(ui_engine, barge_in_mode))
    except Exception as e:
        print(f"[Async Thread Error] {e}")
    finally:
        loop.close()
        print("Asynchronous background thread stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis Voice AI Assistant")
    parser.add_argument("--barge-in", choices=["smart", "headphones", "disabled"], default="smart",
                        help="Barge-in mode: 'smart' (volume-gated), 'headphones' (fully duplex, no echo lock), or 'disabled' (half-duplex lock)")
    args = parser.parse_args()
    
    # 1. Instantiate the UI on the main thread (Cocoa requirement on macOS)
    ui_engine = UIEngine()
    global_ui_engine = ui_engine
    
    # 2. Create the background asyncio event loop
    loop = asyncio.new_event_loop()
    global_loop = loop
    
    # 3. Setup signal handlers on the main thread
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    
    # 4. Start the background thread for the voice pipeline
    async_thread = threading.Thread(
        target=lambda: run_asyncio_thread(loop, ui_engine, args.barge_in),
        daemon=True
    )
    async_thread.start()
    
    # 5. Start the Tkinter main loop on the main thread (blocking)
    try:
        ui_engine.start()
    except KeyboardInterrupt:
        handle_sigint(None, None)
    finally:
        print("Successfully gracefully shutdown.")