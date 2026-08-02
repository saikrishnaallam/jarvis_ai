# tts_engine.py: Kokoro TTS & sounddevice playback
import asyncio
import numpy as np
import sounddevice as sd
from kokoro import KPipeline
import torch

class TTSEngine:
    def __init__(self, sample_rate=24000):
        # Kokoro v1.0 generates 24kHz audio
        self.sample_rate = sample_rate
        
        print("🔊 Loading Kokoro TTS pipeline...")
        # Auto-detect hardware accelerator (MPS/Apple Silicon, CUDA, or CPU)
        device = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
        print(f"🔊 Running Kokoro TTS on device: {device}")
        self.pipeline = KPipeline(lang_code='a', device=device) 
        self.voice = 'af_heart' # Default high-quality female voice
        
        # Internal async queue to buffer synthesized audio chunks
        self.audio_playback_queue = asyncio.Queue()
        self.is_playing = False
        self.current_amplitude = 0.0

    def _synthesize_sync(self, text: str) -> np.ndarray:
        """
        Runs Kokoro inference synchronously. 
        Returns a float32 NumPy array of the audio.
        """
        # Kokoro yields a generator. Since we chunked by sentence in the LLM, 
        # we usually just get one segment here.
        generator = self.pipeline(text, voice=self.voice, speed=1.1, split_pattern=None)
        
        audio_chunks = []
        for _, _, audio in generator:
            # audio is a PyTorch tensor, convert to numpy
            audio_chunks.append(audio.numpy())
            
        if not audio_chunks:
            return np.array([], dtype=np.float32)
            
        return np.concatenate(audio_chunks)

    async def synthesis_worker(self, tts_text_queue: asyncio.Queue, barge_in_event: asyncio.Event):
        """Consumes text from LLM, synthesizes audio, pushes to playback queue."""
        print("🔊 TTS Synthesizer ready.")
        
        while True:
            text = await tts_text_queue.get()
            
            # 1. Handle Barge-in & End of Turn
            if barge_in_event.is_set():
                continue # Skip synthesis if user is currently interrupting
                
            if text == "<END_OF_TURN>":
                # Signal the playback worker that this response is finished
                await self.audio_playback_queue.put(None) 
                continue

            # 2. Synthesize audio in a background thread to prevent blocking event loop
            try:
                print(f"🔊 [TTS] Synthesizing: \"{text}\"")
                audio_array = await asyncio.to_thread(self._synthesize_sync, text)
                
                # If barge-in happened *during* synthesis, throw the audio away
                if barge_in_event.is_set():
                    continue
                    
                # Push the finished audio chunk to the speaker
                await self.audio_playback_queue.put(audio_array)
                
            except Exception as e:
                print(f"[TTS Error] {e}")

    async def playback_worker(self, barge_in_event: asyncio.Event, ui_engine=None):
        """Consumes audio arrays and plays them via sounddevice OutputStream."""
        print("🔊 Audio Playback worker ready.")
        
        current_chunk = None
        current_index = 0
        
        def _callback(outdata, frames, time, status):
            """This callback runs in a separate C-thread managed by PortAudio."""
            nonlocal current_chunk, current_index
            if status:
                print(status)
                
            # If barge-in is triggered, fill buffer with zeros (silence) and abort
            if barge_in_event.is_set():
                outdata.fill(0)
                current_chunk = None
                current_index = 0
                self.is_playing = False
                self.current_amplitude = 0.0
                return

            outdata.fill(0)
            
            # Keep filling the output buffer until we satisfy the requested 'frames'
            filled = 0
            has_voice = False
            while filled < frames:
                if current_chunk is None:
                    try:
                        current_chunk = self.audio_playback_queue.get_nowait()
                        current_index = 0
                        if current_chunk is None:
                            # End of turn signal - play silence
                            break
                    except asyncio.QueueEmpty:
                        break
                
                if current_chunk is not None:
                    has_voice = True
                    chunk_len = len(current_chunk)
                    remaining = chunk_len - current_index
                    needed = frames - filled
                    to_copy = min(remaining, needed)
                    
                    chunk_slice = current_chunk[current_index : current_index+to_copy]
                    outdata[filled:filled+to_copy, 0] = chunk_slice
                    
                    # Compute amplitude of current playing segment
                    amp = np.max(np.abs(chunk_slice)) if len(chunk_slice) > 0 else 0.0
                    self.current_amplitude = float(amp)
                    
                    current_index += to_copy
                    filled += to_copy
                    
                    if current_index >= chunk_len:
                        current_chunk = None
                        current_index = 0
            
            if not has_voice:
                self.current_amplitude = 0.0
            self.is_playing = has_voice

        # Open a persistent output stream
        with sd.OutputStream(samplerate=self.sample_rate,
                             channels=1,
                             dtype='float32',
                             blocksize=4096, # Adjust based on latency/stability needs
                             callback=_callback):
            
            while True:
                # 1. Check for barge-in
                if barge_in_event.is_set():
                    self.is_playing = False
                    self.current_amplitude = 0.0
                    current_chunk = None
                    current_index = 0
                    if ui_engine:
                        ui_engine.set_state("IDLE")
                        ui_engine.set_amplitude(0.0)
                    # Empty the playback queue instantly
                    while not self.audio_playback_queue.empty():
                        try:
                            self.audio_playback_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                
                # 2. Update UI engine state if active
                if self.is_playing:
                    if ui_engine:
                        ui_engine.set_state("SPEAKING")
                        ui_engine.set_amplitude(self.current_amplitude)
                else:
                    if ui_engine and ui_engine.state == "SPEAKING":
                        ui_engine.set_state("IDLE")
                        ui_engine.set_amplitude(0.0)
                        
                # 3. Keep the stream alive
                await asyncio.sleep(0.05)

# --- Integration Example ---
async def main():
    tts_text_queue = asyncio.Queue()
    barge_in_event = asyncio.Event()
    
    tts = TTSEngine()
    
    # Start both workers
    asyncio.create_task(tts.synthesis_worker(tts_text_queue, barge_in_event))
    asyncio.create_task(tts.playback_worker(barge_in_event))
    
    # Mock LLM sending sentences
    await tts_text_queue.put("Hello! I am your local voice assistant.")
    await tts_text_queue.put("I am running entirely on your machine.")
    await tts_text_queue.put("<END_OF_TURN>")
    
    # Keep loop alive
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())