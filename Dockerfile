FROM python:3.11-slim

# ffmpeg install karein (yt-dlp audio stream extraction ke liye zaroori hai)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-8000} main:app"]
