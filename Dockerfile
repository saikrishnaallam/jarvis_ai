# Dockerfile: For containerized deployment
FROM python:3.11-slim

# Install system dependencies (ALSA, PortAudio for mic/speakers, espeak for Kokoro)
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    gcc \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models (Optional, but recommended for Docker)
# RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
# RUN python -c "from kokoro import KPipeline; KPipeline(lang_code='a')"

COPY . .

CMD ["python", "main.py"]