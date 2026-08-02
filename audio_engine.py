# audio_engine.py: Voice Activity Detection (VAD) & microphone capture
import asyncio
import numpy as np
import sounddevice as sd
from silero_vad import load_silero_vad, get_speech_timestamps
import torch

class AudioPipeline:
    def __init__(self, sample_rate=16000, chunk_duration_ms=32):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * (chunk_duration_ms / 1000))
        
        # Load Silero VAD for sub-millisecond edge processing
        self.vad_model = load_silero_vad()
        
        # Async Queues and State
        self.raw_audio_queue = asyncio.Queue()
        self.speech_buffer_queue = asyncio.Queue()
        
        self.is_user_speaking = False
        self.barge_in_event = asyncio.Event()
        self.loop = asyncio.get_running_loop()

    def _audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for every new audio chunk from the mic."""
        if status:
            print(f"Audio Buffer Status: {status}")
        
        # Push raw audio to the async event loop thread safely
        audio_chunk = np.squeeze(indata.copy())
        self.loop.call_soon_threadsafe(self.raw_audio_queue.put_nowait, audio_chunk)

    async def vad_processing_loop(self, tts_engine=None, ui_engine=None):
        """Consumes raw audio, runs VAD, and endpoints speech."""
        current_speech_buffer = []
        silence_frames = 0
        max_silence_frames = int(0.8 / (self.chunk_size / self.sample_rate)) # 0.8s silence threshold
        
        print("🎙️ Listening...")
        
        last_playback_time = 0
        with sd.InputStream(samplerate=self.sample_rate, 
                            channels=1, 
                            dtype='float32', 
                            blocksize=self.chunk_size, 
                            callback=self._audio_callback):
            while True:
                chunk = await self.raw_audio_queue.get()
                
                current_time = self.loop.time()
                if tts_engine and tts_engine.is_playing:
                    last_playback_time = current_time
                
                # If assistant is speaking, or we are in the 1.0s echo cooldown period, discard incoming audio
                if tts_engine and (tts_engine.is_playing or (current_time - last_playback_time < 1.0)):
                    self.is_user_speaking = False
                    current_speech_buffer = []
                    silence_frames = 0
                    self.barge_in_event.clear()
                    continue
                
                # Convert NumPy array to Torch tensor for Silero
                tensor_chunk = torch.from_numpy(chunk)
                
                # Get speech probability for this chunk
                speech_prob = self.vad_model(tensor_chunk, self.sample_rate).item()
                
                if speech_prob > 0.5:
                    if not self.is_user_speaking:
                        # User just started speaking -> Trigger Barge-In
                        self.is_user_speaking = True
                        self.barge_in_event.set() 
                        print("\n[VAD] Speech onset detected. Triggering barge-in.")
                        if ui_engine:
                            ui_engine.set_state("LISTENING")
                    
                    current_speech_buffer.append(chunk)
                    silence_frames = 0
                else:
                    if self.is_user_speaking:
                        silence_frames += 1
                        current_speech_buffer.append(chunk)
                        
                        # Dynamic Endpointing: Has the user stopped speaking?
                        if silence_frames > max_silence_frames:
                            self.is_user_speaking = False
                            if ui_engine:
                                ui_engine.set_state("THINKING")
                            
                            # Concatenate buffer and push to STT queue
                            final_audio = np.concatenate(current_speech_buffer)
                            await self.speech_buffer_queue.put(final_audio)
                            
                            print(f"[VAD] Speech complete. Buffer size: {len(final_audio) / self.sample_rate:.2f}s")
                            
                            # Reset buffers
                            current_speech_buffer = []
                            silence_frames = 0
                            self.barge_in_event.clear()

# --- Example Usage ---
async def main():
    pipeline = AudioPipeline()
    
    # Run the VAD loop as a background task
    vad_task = asyncio.create_task(pipeline.vad_processing_loop())
    
    # Mock STT consumer
    while True:
        speech_array = await pipeline.speech_buffer_queue.get()
        print(f"➡️ Sent {len(speech_array)} samples to STT Engine...")

if __name__ == "__main__":
    asyncio.run(main())