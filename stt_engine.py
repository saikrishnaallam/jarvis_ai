# stt_engine.py: faster-whisper transcription
import asyncio
import numpy as np
from faster_whisper import WhisperModel

class STTEngine:
    def __init__(self, model_size="tiny.en", device="cpu"):
        """
        Initializes the STT Engine. 
        For CPU, use 'int8' compute type for speed. 
        For GPU, use 'cuda' and 'float16' compute type.
        """
        print(f"Loading faster-whisper ({model_size}) on {device}...")
        
        # Determine optimal quantization based on hardware
        compute_type = "int8" if device == "cpu" else "float16"
        
        self.model = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type=compute_type
        )
        
        # Async Queue to push transcribed text to the LLM
        self.text_queue = asyncio.Queue()
        
    def _transcribe_sync(self, audio_array: np.ndarray) -> str:
        """
        Synchronous transcription method executed inside a worker thread.
        Expects a 16kHz float32 NumPy array.
        """
        # faster-whisper accepts NumPy arrays directly.
        segments, info = self.model.transcribe(
            audio=audio_array,
            beam_size=1,            # Beam size 1 is faster for real-time (greedy decoding)
            vad_filter=False,       # Disabled redundant VAD filter to save 100-300ms (we already endpoint in AudioPipeline)
            language="en",          # Hardcode language to save detection time (optional)
            condition_on_previous_text=False # Prevent hallucinations on short clips
        )
        
        # The transcription is a generator, iterate to extract text
        full_text = "".join(segment.text for segment in segments).strip()
        return full_text

    async def process_speech_queue(self, speech_buffer_queue: asyncio.Queue):
        """
        Continuously consumes audio buffers from the VAD pipeline,
        transcribes them without blocking the event loop, and pushes text to the LLM.
        """
        print("👂 STT Engine ready. Waiting for speech buffers...")
        
        while True:
            # 1. Wait for endpointed audio array from the VAD pipeline
            audio_array = await speech_buffer_queue.get()
            
            # Skip noise/mic clicks (e.g., less than 0.5 seconds of audio)
            if len(audio_array) < 16000 * 0.5:
                continue 

            print("\n[STT] Transcribing...")
            
            # 2. Offload the heavy blocking inference to a background thread
            # This prevents the audio input stream from dropping frames!
            transcription = await asyncio.to_thread(self._transcribe_sync, audio_array)
            
            if transcription:
                print(f"[STT] User said: \"{transcription}\"")
                # 3. Push to the LLM orchestration queue
                await self.text_queue.put(transcription)

# --- Integration Example ---
async def main():
    # In a real app, this queue comes from `AudioPipeline` (Phase 1)
    speech_queue = asyncio.Queue()
    stt = STTEngine(model_size="base", device="cpu")
    
    # Start STT background task
    asyncio.create_task(stt.process_speech_queue(speech_queue))
    
    # Mocking Phase 1: Sending a fake 2-second audio buffer
    dummy_audio = np.zeros(16000 * 2, dtype=np.float32)
    await speech_queue.put(dummy_audio)
    
    # Keep event loop running
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())