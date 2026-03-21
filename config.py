# ============================================================
#  config.py  —  Central configuration for YouTube Automation
#  Edit this file to change models, voices, keys, styles.
# ============================================================

# ── LLM (Ollama) ────────────────────────────────────────────
OLLAMA_MODEL   = "llama3.2"          # Any model you have pulled via `ollama pull <name>`
OLLAMA_HOST    = "http://localhost:11434"  # Default Ollama server address

# ── TTS Engine ──────────────────────────────────────────────
# Options: "kokoro" | "coqui" | "piper"
TTS_ENGINE     = "kokoro"

# Kokoro settings
KOKORO_VOICE   = "af_heart"          # af_heart, af_bella, am_adam, bf_emma, bm_george ...
KOKORO_SPEED   = 1.0                 # 0.8 = slower, 1.2 = faster

# Coqui / XTTS settings (used if TTS_ENGINE = "coqui")
COQUI_MODEL    = "tts_models/en/ljspeech/tacotron2-DDC"

# Piper settings (used if TTS_ENGINE = "piper")
# Download voice models from: https://github.com/rhasspy/piper/releases
PIPER_MODEL    = "en_US-lessac-medium.onnx"
PIPER_EXE      = r"C:\piper\piper.exe"   # Path to piper.exe on Windows

# ── Stock Footage ────────────────────────────────────────────
# Get free Pexels key: https://www.pexels.com/api/
PEXELS_API_KEY    = ""

# Get free Pixabay key: https://pixabay.com/api/docs/
PIXABAY_API_KEY   = ""

# Footage fetch settings
FOOTAGE_PREFER    = "pexels"         # "pexels" | "pixabay"  — tried first
FOOTAGE_FALLBACK  = "pixabay"        # fallback if preferred fails
FOOTAGE_PER_POINT = 1                # clips to download per script point
FOOTAGE_ORIENTATION = "landscape"    # "landscape" | "portrait" | "square"
FOOTAGE_MIN_DURATION = 5             # minimum clip duration in seconds

# ── Video Output ─────────────────────────────────────────────
OUTPUT_WIDTH      = 1920
OUTPUT_HEIGHT     = 1080
OUTPUT_FPS        = 30

# ── Visual Overlay Style ─────────────────────────────────────
OVERLAY_BG_OPACITY   = 0.55          # Darken footage behind text (0=none, 1=black)
HEADING_COLOR        = (255, 255, 255)
BODY_COLOR           = (210, 210, 220)
ACCENT_COLOR         = (99, 102, 241)   # Indigo bar accent
FONT_HEADING_SIZE    = 82
FONT_BODY_SIZE       = 46

# ── Background Music ─────────────────────────────────────────
BG_MUSIC_ENABLED  = True
BG_MUSIC_PATH     = "music/bg.mp3"   # Drop any royalty-free MP3 here
BG_MUSIC_VOLUME   = 0.10

# ── YouTube Upload ───────────────────────────────────────────
YOUTUBE_PRIVACY      = "private"     # "private" | "unlisted" | "public"
YOUTUBE_CATEGORY_ID  = "27"          # 27 = Education
YOUTUBE_CREDS_FILE   = "client_secrets.json"
YOUTUBE_TOKEN_FILE   = "youtube_token.pkl"

# ── FFmpeg ───────────────────────────────────────────────────
FFMPEG_BIN        = "ffmpeg"         # or full path: r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE_BIN       = "ffprobe"

# ── Workspace ────────────────────────────────────────────────
WORKSPACE_DIR     = "workspace"
CLEANUP_ON_SUCCESS = False           # Set True to auto-delete job files after upload
