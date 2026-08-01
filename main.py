# main.py: The orchestrator (start here)
import asyncio
import signal
import sys

# Import our custom modules
from audio_engine import AudioPipeline
from stt_engine import STTEngine
from llm_engine import LLMEngine
from tts_engine import TTSEngine

async def shutdown(loop, signal=None):
    """Gracefully cleans up tasks on exit (Ctrl+C)."""
    if signal:
        print(f"\nReceived exit signal {signal.name}...")
    print("Shutting down Voice AI Engine...")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    print("🚀 Initializing Local Voice Assistant...")

    # 1. Global State & Queues
    barge_in_event = asyncio.Event()
    
    # 2. Instantiate all modules
    audio_engine = AudioPipeline()          # Connects Mic -> VAD (creates its own speech queue)
    stt_engine = STTEngine()                # Transcribes endpointed speech
    llm_engine = LLMEngine()                # Ollama Llama-3.1 + Tools (creates tts_text_queue)
    tts_engine = TTSEngine()                # Kokoro TTS + Speaker playback
    
    # Wait a moment for models to load into memory
    await asyncio.sleep(1)
    
    print("\n🟢 All systems online. Say something!")
    
    try:
        # 3. Launch all worker loops concurrently
        await asyncio.gather(
            # Input pipeline
            audio_engine.vad_processing_loop(tts_engine),
            stt_engine.process_speech_queue(audio_engine.speech_buffer_queue),
            
            # Orchestration
            llm_engine.process_text_queue(stt_engine.text_queue, barge_in_event),
            
            # Output pipeline
            tts_engine.synthesis_worker(llm_engine.tts_queue, barge_in_event),
            tts_engine.playback_worker(barge_in_event),
        )
    except asyncio.CancelledError:
        pass # Expected on shutdown

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup graceful shutdown handlers
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s))
        )
        
    try:
        loop.run_until_complete(main())
    finally:
        print("Successfully gracefully shutdown.")
        loop.close()