# ============================================================
#  config.py  —  Central configuration for YouTube Automation
#  Sensitive keys are loaded from .env — never hardcoded here.
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── LLM Provider ─────────────────────────────────────────────
# Options: "groq" | "gemini" | "ollama"
# Recommendation: "groq" — free, instant, best quality for your hardware
LLM_PROVIDER  = "groq"

# Groq settings (free — https://console.groq.com)
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.3-70b-versatile"   # Best free model on Groq

# Gemini settings (free — https://aistudio.google.com/apikey)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash"

# Ollama settings (local fallback)
OLLAMA_MODEL  = "gemma3:4b"
OLLAMA_HOST   = "http://localhost:11434"

# ── TTS Engine ──────────────────────────────────────────────
TTS_ENGINE    = "kokoro"
KOKORO_VOICE  = "af_heart"
KOKORO_SPEED  = 0.9

COQUI_MODEL   = "tts_models/en/ljspeech/tacotron2-DDC"
PIPER_MODEL   = "en_US-lessac-medium.onnx"
PIPER_EXE     = r"C:\piper\piper.exe"

# ── Stock Footage ────────────────────────────────────────────
PEXELS_API_KEY   = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY  = os.getenv("PIXABAY_API_KEY", "")

FOOTAGE_PREFER       = "pexels"
FOOTAGE_FALLBACK     = "pixabay"
FOOTAGE_PER_POINT    = 1
FOOTAGE_ORIENTATION  = "portrait"    # vertical for Shorts
FOOTAGE_MIN_DURATION = 5

# ── Video Output — Vertical for YouTube Shorts (9:16) ────────
OUTPUT_WIDTH  = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FPS    = 30

# ── Visual Overlay Style ─────────────────────────────────────
OVERLAY_BG_OPACITY = 0.55
HEADING_COLOR      = (255, 255, 255)
BODY_COLOR         = (210, 210, 220)
ACCENT_COLOR       = (99, 102, 241)
FONT_HEADING_SIZE  = 82
FONT_BODY_SIZE     = 46

# ── Background Music ─────────────────────────────────────────
BG_MUSIC_ENABLED = True
BG_MUSIC_PATH    = "music/bg.mp3"
BG_MUSIC_VOLUME  = 0.10

# ── YouTube Upload ───────────────────────────────────────────
YOUTUBE_PRIVACY     = "private"
YOUTUBE_CATEGORY_ID = "27"
YOUTUBE_CREDS_FILE  = "client_secrets.json"
YOUTUBE_TOKEN_FILE  = "youtube_token.pkl"

# ── FFmpeg ───────────────────────────────────────────────────
FFMPEG_BIN   = "ffmpeg"
FFPROBE_BIN  = "ffprobe"

# ── Workspace ────────────────────────────────────────────────
WORKSPACE_DIR      = "workspace"
CLEANUP_ON_SUCCESS = False