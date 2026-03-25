# YouTube Shorts Automation

A fully local, zero-cost pipeline that turns a single topic into a published YouTube Short — automatically. You type a topic, the system writes the script, generates a voiceover, downloads stock footage, assembles the video, and uploads it to YouTube. No manual editing. No expensive subscriptions.

---

## How it works

```
You type a topic
      ↓
Groq AI writes the script (free, cloud, instant)
      ↓
Kokoro TTS reads it aloud (free, runs on your machine)
      ↓
Pexels API downloads matching stock footage (free)
      ↓
Pillow + FFmpeg build the vertical video (free, open source)
      ↓
YouTube Data API uploads the Short (free)
```

Everything runs on your Windows machine. The only internet calls are to Groq (script), Pexels (footage), and YouTube (upload) — all free.

---

## Cost breakdown

| Component | Tool | Cost |
|---|---|---|
| Script writing | Groq API (Llama 3.3 70B) | Free — 14,400 req/day |
| Voiceover | Kokoro TTS (local) | Free — runs on your CPU |
| Stock footage | Pexels API | Free — generous quota |
| Video assembly | FFmpeg + Pillow | Free — open source |
| Upload | YouTube Data API | Free — OAuth |
| **Total** | | **$0** |

---

## Requirements

Before starting, make sure you have:

- Windows 10 or 11
- Python 3.10 or higher → [python.org/downloads](https://www.python.org/downloads/)
- A stable internet connection
- A YouTube channel (any channel works)

---

## Step 1 — Download the project

Download or clone this repository into a folder on your machine. For example:

```
D:\AUTOMATION\yt-automation\
```

Your folder should contain these files:

```
yt-automation/
├── main.py
├── config.py
├── script_generator.py
├── voice_generator.py
├── footage_fetcher.py
├── visual_builder.py
├── video_assembler.py
├── uploader.py
├── requirements.txt
└── README.md
```

---

## Step 2 — Install FFmpeg

FFmpeg is the tool that assembles your final video. It is free and open source.

1. Go to [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Download **ffmpeg-release-essentials.zip**
3. Extract it — you will get a folder like `ffmpeg-7.x-essentials_build`
4. Rename that folder to `ffmpeg` and move it to `C:\ffmpeg`
5. Add FFmpeg to your Windows PATH so you can run it from anywhere:
   - Press `Windows + S` and search for **"Edit the system environment variables"**
   - Click **Environment Variables**
   - Under **System variables**, find **Path** and click **Edit**
   - Click **New** and add: `C:\ffmpeg\bin`
   - Click OK on all windows
6. Open a new Command Prompt and test it:
   ```
   ffmpeg -version
   ```
   You should see version information. If you get "not recognized", restart your computer and try again.

---

## Step 3 — Create a Python virtual environment

A virtual environment keeps this project's packages separate from the rest of your system.

Open Command Prompt, navigate to your project folder, and run:

```
cd D:\AUTOMATION\yt-automation
python -m venv venv
venv\Scripts\activate
```

Your terminal prompt will now show `(venv)` at the start. Always activate this before running the project.

---

## Step 4 — Install Python packages

With your virtual environment active, run:

```
pip install -r requirements.txt
pip install python-dotenv
```

This installs everything the project needs including Kokoro TTS, Pillow, the Google API client, and the Groq client.

---

## Step 5 — Download Kokoro TTS model files

Kokoro is the voice engine. It needs two model files that are too large to include in the project. Download them directly into your project folder.

Run these commands from inside `D:\AUTOMATION\yt-automation`:

```
curl -L -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

- `kokoro-v1.0.onnx` — about 310 MB
- `voices-v1.0.bin` — about 80 MB

Wait for both to finish completely before moving on.

---

## Step 6 — Get your free API keys

You need three free API keys. None require a credit card.

### Groq (script writing)

Groq runs a powerful 70B AI model for free. This is what writes your video scripts.

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Go to **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — it starts with `gsk_`

### Pexels (stock footage)

Pexels provides free stock video clips for your videos.

1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Click **Get Started** and create a free account
3. Fill in the application form — just say it's for personal automation
4. Your API key will be shown on the dashboard
5. Copy it

### YouTube Data API

This lets the system upload directly to your YouTube channel.

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Click **Select a project** at the top → **New Project**
3. Name it anything (e.g. `yt-automation`) and click **Create**
4. In the search bar at the top, search for **YouTube Data API v3**
5. Click it and then click **Enable**
6. In the left sidebar, go to **Credentials**
7. Click **Create Credentials** → **OAuth 2.0 Client ID**
8. If prompted to configure the consent screen:
   - Click **Configure Consent Screen**
   - Choose **External** → **Create**
   - Fill in App name (anything), User support email, Developer email
   - Click **Save and Continue** through all steps
   - Go back to Credentials
9. Click **Create Credentials** → **OAuth 2.0 Client ID** again
10. Application type: **Desktop app**
11. Name it anything and click **Create**
12. Click **Download JSON** on the popup
13. Rename the downloaded file to `client_secrets.json`
14. Move it into your project folder `D:\AUTOMATION\yt-automation\`

---

## Step 7 — Create your .env file

In your project folder, create a new file called `.env` (exactly that name, with the dot).

Open it with Notepad and paste this, filling in your actual keys:

```
GROQ_API_KEY=your_groq_key_here
PEXELS_API_KEY=your_pexels_key_here
```

Save the file. It should sit alongside `main.py` in your project folder.

> **Important:** Never share this file or commit it to GitHub. It is already listed in `.gitignore` to protect you.

---

## Step 8 — Run it for the first time

Make sure your virtual environment is active (`(venv)` shows in your terminal). Then run:

```
python main.py
```

Type a topic when prompted, for example:
```
Enter your video topic: dark psychology facts
```

### First run — YouTube authentication

The very first time you run the script, a browser window will open asking you to sign into your Google account. This is normal. It is requesting permission to upload videos to your YouTube channel on your behalf.

1. Sign in with the Google account that owns your YouTube channel
2. Click **Allow**
3. The browser will show a success message and you can close it

The script continues automatically. A file called `youtube_token.pkl` is saved in your project folder — this stores your login so you never need to authenticate again.

---

## Step 9 — Watch it run

The terminal will show exactly what is happening at each stage:

```
[1/6] Generating script...       ← Groq writes your script in ~3 seconds
[2/6] Generating voiceover...    ← Kokoro reads it aloud on your CPU
[3/6] Fetching stock footage...  ← Pexels downloads matching video clips
[4/6] Building visuals...        ← Pillow + FFmpeg compose the video frames
[5/6] Assembling final video...  ← FFmpeg stitches everything together
[6/6] Uploading to YouTube...    ← Sends the finished Short to your channel
```

At the end you will see:

```
✓  Published: https://www.youtube.com/watch?v=xxxxxxxxxx
```

Your Short is live.

---

## Project structure explained

```
yt-automation/
│
├── main.py                 ← Entry point. Run this to start the pipeline.
│
├── config.py               ← All settings in one place. Change model, voice,
│                             resolution, upload privacy, etc. here.
│
├── script_generator.py     ← Calls Groq API to write the video script.
│                             Supports Groq, Gemini, and local Ollama.
│
├── voice_generator.py      ← Runs Kokoro TTS locally to generate voiceover.
│                             Supports Kokoro, Coqui, and Piper.
│
├── footage_fetcher.py      ← Downloads stock video clips from Pexels.
│                             Falls back to Pixabay if Pexels has no results.
│
├── visual_builder.py       ← Builds each video frame using Pillow overlays.
│                             Uses FFmpeg to composite text onto footage.
│
├── video_assembler.py      ← Combines all segments into the final MP4.
│                             Optionally mixes in background music.
│
├── uploader.py             ← Uploads the finished video to YouTube via
│                             the YouTube Data API with OAuth.
│
├── requirements.txt        ← Python package list for pip install.
├── .env                    ← Your secret API keys. Never commit this.
├── .env.example            ← Template showing which keys are needed.
├── .gitignore              ← Protects secrets from being pushed to GitHub.
├── client_secrets.json     ← YouTube OAuth credentials. Never commit this.
├── youtube_token.pkl       ← Auto-created after first YouTube login.
│
├── kokoro-v1.0.onnx        ← Kokoro TTS model (you download this).
├── voices-v1.0.bin         ← Kokoro voice data (you download this).
│
├── music/
│   └── bg.mp3              ← Optional background music. Drop any MP3 here.
│
└── workspace/              ← Auto-created. Each job gets its own subfolder
                              with script, audio, footage, and video files.
```

---

## Configuration

Open `config.py` to customise the system. Every setting is documented inline. Key ones:

### Switch AI model provider
```python
LLM_PROVIDER = "groq"       # groq | gemini | ollama
```

### Change the Groq model
```python
GROQ_MODEL = "llama-3.3-70b-versatile"   # Best free option
```

### Change the voice
```python
KOKORO_VOICE = "af_heart"   # af_heart, af_bella, am_adam, bf_emma, bm_george
KOKORO_SPEED = 0.9           # 0.8 = slower, 1.0 = normal, 1.2 = faster
```

### Change upload privacy
```python
YOUTUBE_PRIVACY = "private"   # private | unlisted | public
```
Start with `"private"` so you can review videos before they go public. Change to `"public"` when you are happy with the output quality.

### Add background music
Drop any royalty-free MP3 file into the `music/` folder and name it `bg.mp3`. The system will automatically mix it in at low volume. Get free music from [YouTube Audio Library](https://studio.youtube.com/channel/music).

### Auto-cleanup workspace
```python
CLEANUP_ON_SUCCESS = True   # Deletes job files after upload
```

---

## Switching AI providers

The system supports three providers. Change `LLM_PROVIDER` in `config.py` and add the matching key to `.env`.

### Groq (recommended)
Fast, free, runs Llama 3.3 70B. Best quality for zero cost.
```
# .env
GROQ_API_KEY=gsk_your_key_here
```
```python
# config.py
LLM_PROVIDER = "groq"
GROQ_MODEL   = "llama-3.3-70b-versatile"
```

### Google Gemini
Also free. Get key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
```
# .env
GEMINI_API_KEY=your_key_here
```
```python
# config.py
LLM_PROVIDER  = "gemini"
GEMINI_MODEL  = "gemini-2.0-flash"
```

### Ollama (fully local, no internet)
Requires [Ollama](https://ollama.com) installed and running.
```
ollama pull llama3.2
```
```python
# config.py
LLM_PROVIDER = "ollama"
OLLAMA_MODEL = "llama3.2"
```

---

## Troubleshooting

### `ffmpeg` is not recognized
FFmpeg is not on your PATH. Re-do Step 2 and restart your computer after adding it.

### `FileNotFoundError: voices-v1.0.bin`
The Kokoro model files are not in your project folder. Re-run the curl commands in Step 5 from inside your project folder.

### `Cannot connect to Ollama`
Only relevant if using `LLM_PROVIDER = "ollama"`. Open a terminal and run `ollama serve`, then try again.

### `client_secrets.json not found`
You have not completed the YouTube API setup in Step 6, or the file is in the wrong location. It must be in the same folder as `main.py`.

### `getaddrinfo failed` during upload
Your internet connection dropped during the upload. Run the script again — it will rebuild and re-upload. If you want to skip rebuilding, the finished video is saved in `workspace/` and can be uploaded manually to YouTube Studio.

### Script is too short (under 30 seconds)
The AI model occasionally returns minimal content. Just run again — the output is non-deterministic and the next run will usually be correct length.

### Footage overlay falling back to static slides
Make sure you are using the latest `visual_builder.py`. The current version uses Pillow image compositing instead of FFmpeg drawtext, which is more reliable on Windows.

### YouTube upload says `insufficientPermissions`
Delete `youtube_token.pkl` from your project folder and run again. A fresh browser login will fix the permissions.

---

## Running automatically on a schedule

To publish a video every day without touching anything, use Windows Task Scheduler.

1. Press `Windows + S` → search **Task Scheduler** → Open it
2. Click **Create Basic Task** in the right panel
3. Name it `YouTube Auto` and click Next
4. Trigger: **Daily** → set your preferred time → Next
5. Action: **Start a program** → Next
6. Program: `D:\AUTOMATION\yt-automation\venv\Scripts\python.exe`
7. Arguments: `main.py "your default topic"`
8. Start in: `D:\AUTOMATION\yt-automation`
9. Finish

The script will run silently at your chosen time every day.

> For fully hands-off scheduling, create a text file called `topics.txt` with one topic per line and modify `main.py` to read a random line from it each run. This gives you weeks of unique content without any manual input.

---

## Roadmap

This project is the foundation for a larger system. Planned next steps:

- **Django web UI** — browser-based interface to trigger runs, preview scripts, and manage uploads without touching the terminal
- **Topic queue** — schedule multiple videos in advance from a list
- **Thumbnail generator** — auto-generate custom thumbnails with Pillow
- **Analytics dashboard** — track views and engagement per video
- **SaaS conversion** — multi-user platform with subscription billing

---

## Security notes

These files contain sensitive credentials and must never be committed to GitHub or shared:

- `.env` — your API keys
- `client_secrets.json` — your YouTube OAuth credentials
- `youtube_token.pkl` — your YouTube login token

All three are already listed in `.gitignore`. Double-check before pushing to any public repository.

---

## License

This project is for personal use. Stock footage is sourced from Pexels under their free license. All AI-generated scripts are original content. Background music, if used, must be royalty-free.