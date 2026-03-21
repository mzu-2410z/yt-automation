# YouTube Automation v2 — Local AI Edition
Zero cloud AI costs. Runs entirely on your Windows machine.

---

## What changed from v1
| Component     | v1 (old)             | v2 (new)                        |
|---------------|----------------------|---------------------------------|
| LLM           | Claude API           | **Ollama** (local, free)        |
| TTS           | Edge-TTS (Microsoft) | **Kokoro / Coqui / Piper** (local) |
| Visuals       | Static Pillow slides | **Stock footage + text overlay** |
| Config        | Hardcoded            | **Single config.py file**       |

---

## One-time setup

### 1. Install FFmpeg
- Download: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)
- Extract to `C:\ffmpeg`, add `C:\ffmpeg\bin` to Windows PATH
- Test: `ffmpeg -version` in Command Prompt

### 2. Install Ollama
- Download: https://ollama.com/download
- Install and run it (it runs as a background service)
- Pull your model:
  ```
  ollama pull llama3.2
  ```
- Test: `ollama run llama3.2 "say hello"`

### 3. Install Python packages
```
pip install -r requirements.txt
```

### 4. Set up Kokoro TTS (recommended)
```
pip install kokoro-onnx soundfile
```
On first run, Kokoro downloads its model files (~80MB) automatically.
No setup beyond the pip install.

### 5. Get free API keys for stock footage
**Pexels** (recommended):
- Go to https://www.pexels.com/api/
- Sign up free → copy your API key
- Paste it in `config.py` → `PEXELS_API_KEY`

**Pixabay** (optional fallback):
- Go to https://pixabay.com/api/docs/
- Sign up free → copy your key
- Paste in `config.py` → `PIXABAY_API_KEY`

### 6. Set up YouTube API (one time)
1. https://console.cloud.google.com/ → New project
2. Enable "YouTube Data API v3"
3. Credentials → OAuth 2.0 Client ID → Desktop app
4. Download JSON → rename to `client_secrets.json` → place in this folder
5. First run opens a browser login. After that it's fully automatic.

---

## Running

```bash
python main.py
```
Enter topic when prompted. Or pass it directly:
```bash
python main.py "10 foods that boost your memory"
```

---

## Configuring everything

Open `config.py` — every setting is documented inline:

```python
OLLAMA_MODEL     = "llama3.2"       # swap to mistral, deepseek-r1, etc.
TTS_ENGINE       = "kokoro"         # kokoro | coqui | piper
KOKORO_VOICE     = "af_heart"       # af_bella, am_adam, bf_emma, bm_george...
PEXELS_API_KEY   = "your_key"
PIXABAY_API_KEY  = "your_key"
YOUTUBE_PRIVACY  = "private"        # review before publishing
```

---

## Project structure
```
youtube_auto_v2/
├── main.py                  ← Run this
├── config.py                ← All settings here
├── script_generator.py      ← Ollama LLM writes the script
├── voice_generator.py       ← Local TTS (Kokoro/Coqui/Piper)
├── footage_fetcher.py       ← Downloads stock clips from Pexels/Pixabay
├── visual_builder.py        ← Overlays text on footage (or makes slides)
├── video_assembler.py       ← FFmpeg final assembly
├── uploader.py              ← YouTube Data API upload
├── requirements.txt
├── client_secrets.json      ← You download this (YouTube OAuth)
├── youtube_token.pkl        ← Auto-created after first login
├── music/
│   └── bg.mp3              ← Optional royalty-free background music
└── workspace/               ← Job files auto-created here
```

---

## Cost breakdown
| Component        | Cost  |
|------------------|-------|
| Ollama LLM       | Free  |
| Kokoro TTS       | Free  |
| Pexels API       | Free  |
| Pixabay API      | Free  |
| FFmpeg           | Free  |
| YouTube Data API | Free  |
| **Total**        | **$0** |

---

## Roadmap
Next step: wrap this in a Django UI for browser-based operation,
then eventually convert to a SaaS product.
