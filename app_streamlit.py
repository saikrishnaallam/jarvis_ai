import streamlit as st
import io
import os
import json
import asyncio
import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline

# Import local engines
from llm_engine import LLMEngine
from stt_engine import STTEngine

# =========================================================
# Page Configurations & Design
# =========================================================
st.set_page_config(
    page_title="Jarvis Voice AI Dashboard",
    page_icon="🎙️",
    layout="centered"
)

# Custom premium styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .title-text {
        font-family: 'Outfit', sans-serif;
        text-align: center;
        background: linear-gradient(135deg, #00d4ff 0%, #a600ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .subtitle-text {
        text-align: center;
        color: #88888b;
        font-size: 1.1rem;
        margin-bottom: 40px;
    }
    
    .orb-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 40px 0;
    }
    
    .jarvis-orb {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        transition: all 0.5s ease;
    }
    
    /* State: IDLE/LISTENING - Breathing Blue */
    .orb-listening {
        background: radial-gradient(circle, rgba(0,212,255,1) 0%, rgba(9,9,121,1) 70%, rgba(2,0,36,1) 100%);
        box-shadow: 0 0 45px rgba(0, 212, 255, 0.8), inset 0 0 20px rgba(255, 255, 255, 0.4);
        animation: breath 3s infinite ease-in-out;
    }
    
    /* State: THINKING - Spinning colorful gradient */
    .orb-thinking {
        background: linear-gradient(270deg, #00d4ff, #a600ff, #ff007f);
        background-size: 600% 600%;
        box-shadow: 0 0 55px rgba(166, 0, 255, 0.9);
        animation: spin 1.5s linear infinite, glow-pulse 1.5s infinite alternate;
    }
    
    /* State: SPEAKING - Pulsing Green */
    .orb-speaking {
        background: radial-gradient(circle, rgba(57,255,20,1) 0%, rgba(0,100,0,1) 70%, rgba(2,0,36,1) 100%);
        box-shadow: 0 0 50px rgba(57, 255, 20, 0.9), inset 0 0 20px rgba(255, 255, 255, 0.5);
        animation: speak-pulse 0.4s infinite alternate ease-in-out;
    }
    
    @keyframes breath {
        0% { transform: scale(0.95); box-shadow: 0 0 30px rgba(0, 212, 255, 0.5); }
        50% { transform: scale(1.05); box-shadow: 0 0 60px rgba(0, 212, 255, 0.9); }
        100% { transform: scale(0.95); box-shadow: 0 0 30px rgba(0, 212, 255, 0.5); }
    }
    
    @keyframes spin {
        0%{background-position:0% 50%}
        50%{background-position:100% 50%}
        100%{background-position:0% 50%}
    }
    
    @keyframes glow-pulse {
        0% { transform: scale(0.98); }
        100% { transform: scale(1.04); }
    }
    
    @keyframes speak-pulse {
        0% { transform: scale(0.98); box-shadow: 0 0 30px rgba(57, 255, 20, 0.6); }
        100% { transform: scale(1.08); box-shadow: 0 0 65px rgba(57, 255, 20, 1.0); }
    }
    
    .chat-container {
        border-radius: 12px;
        background-color: #1a1a24;
        padding: 20px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-text">JARVIS VOICE AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Local Voice Intelligence Dashboard</div>', unsafe_allow_html=True)

# =========================================================
# Model / Cache Resource Initializations
# =========================================================
@st.cache_resource
def load_models():
    # Initialize engines
    stt = STTEngine()
    llm = LLMEngine()
    
    # Initialize Kokoro
    device = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
    tts_pipe = KPipeline(lang_code='a', device=device)
    
    return stt, llm, tts_pipe

with st.spinner("🧠 Booting local AI models (Whisper, Llama, Kokoro)..."):
    stt_engine, llm_engine, tts_pipeline = load_models()

# =========================================================
# Application State
# =========================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "orb_state" not in st.session_state:
    st.session_state.orb_state = "listening" # listening, thinking, speaking

# Sidebar configuration
st.sidebar.title("🛠️ Config Center")
voice = st.sidebar.selectbox("Kokoro TTS Voice", [
    "af_heart", "af_bella", "af_nicole", "af_sarah", 
    "am_adam", "am_michael", "bf_emma", "bf_isabella"
], index=0)
speed = st.sidebar.slider("Speech Speed Ratio", 0.8, 1.5, 1.1, 0.1)

if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    llm_engine.messages = [llm_engine.system_prompt]
    st.rerun()

# =========================================================
# Audio Helper Functions
# =========================================================
def resample_audio(audio_data, src_sr, target_sr=16000):
    """Linearly resamples numpy arrays to target sample rate without external dependencies."""
    if src_sr == target_sr:
        return audio_data
    duration = len(audio_data) / src_sr
    num_target_samples = int(duration * target_sr)
    indices = np.linspace(0, len(audio_data) - 1, num_target_samples)
    resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
    return resampled.astype(np.float32)

async def run_llm_inference(user_text):
    """Executes the tool-calling Ollama chat transaction asynchronously."""
    llm_engine._add_to_memory("user", user_text)
    
    # Query Llama 3.2
    response = await llm_engine.client.chat(
        model=llm_engine.model,
        messages=llm_engine.messages,
        tools=llm_engine.tools,
        options={
            "temperature": 0.0,
            "num_ctx": 1024,
            "num_predict": 55
        }
    )
    
    message = response.message
    tool_calls = message.tool_calls
    
    if tool_calls:
        # LLM wants to execute tool calls
        llm_engine._add_to_memory("assistant", tool_calls=tool_calls)
        for tool_call in tool_calls:
            result = await llm_engine._execute_tool(tool_call)
            # Push tool outputs to memory
            llm_engine.messages.append({
                "role": "tool",
                "content": result,
                "name": tool_call.function.name
            })
            
        # Follow up query with tool execution results
        follow_up = await llm_engine.client.chat(
            model=llm_engine.model,
            messages=llm_engine.messages,
            options={
                "temperature": 0.0,
                "num_ctx": 1024,
                "num_predict": 55
            }
        )
        assistant_text = follow_up.message.content
        llm_engine._add_to_memory("assistant", assistant_text)
        return assistant_text
    else:
        assistant_text = message.content
        llm_engine._add_to_memory("assistant", assistant_text)
        return assistant_text

# =========================================================
# Interface Layout & Execution
# =========================================================

# Render Orb based on current state
orb_class = "orb-listening"
if st.session_state.orb_state == "thinking":
    orb_class = "orb-thinking"
elif st.session_state.orb_state == "speaking":
    orb_class = "orb-speaking"

st.markdown(f"""
    <div class="orb-container">
        <div class="jarvis-orb {orb_class}"></div>
    </div>
""", unsafe_allow_html=True)

# Mic Recorder Widget
from streamlit_mic_recorder import mic_recorder

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_record = mic_recorder(
        start_prompt="🎙️ Talk to Jarvis",
        stop_prompt="🛑 Finish Speaking",
        just_once=True,
        use_container_width=True,
        key="recorder"
    )

if audio_record:
    # 1. Parse WAV bytes from web page microphone
    raw_audio_bytes = audio_record['bytes']
    
    # Read WAV data
    data, samplerate = sf.read(io.BytesIO(raw_audio_bytes))
    if len(data.shape) > 1:
        data = np.mean(data, axis=1) # Convert to mono
    
    # 2. Resample to 16kHz for Whisper
    audio_16k = resample_audio(data, samplerate, 16000)
    
    # Update UI to thinking
    st.session_state.orb_state = "thinking"
    
    # 3. Transcribe speech using Whisper
    with st.spinner("STT transcribing voice..."):
        segments, _ = stt_engine.model.transcribe(audio_16k, beam_size=1)
        transcription = "".join([segment.text for segment in segments]).strip()
        
    if transcription:
        st.session_state.chat_history.append({"role": "user", "content": transcription})
        
        # 4. Generate LLM text response
        with st.spinner("Jarvis is thinking..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(run_llm_inference(transcription))
            loop.close()
            
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        
        # 5. Synthesize TTS response
        st.session_state.orb_state = "speaking"
        with st.spinner("Synthesizing speech response..."):
            generator = tts_pipeline(response_text, voice=voice, speed=speed, split_pattern=None)
            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio.numpy())
            
            if audio_chunks:
                full_audio = np.concatenate(audio_chunks)
                # Output audio directly to the browser
                st.audio(full_audio, sample_rate=24000, autoplay=True)
                
        # Reset to listening
        st.session_state.orb_state = "listening"
        st.rerun()
    else:
        st.warning("No speech detected. Please try speaking again!")
        st.session_state.orb_state = "listening"
        st.rerun()

# Render Conversation Logs
if st.session_state.chat_history:
    st.markdown("### 💬 Transcript Log")
    for msg in st.session_state.chat_history[::-1]: # Show latest first
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
