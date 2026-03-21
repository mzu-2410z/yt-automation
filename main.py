"""
main.py — YouTube Automation Pipeline
Run: python main.py
 or: python main.py "5 habits of highly productive people"
"""

import sys
import re
import time
import json
import shutil
from pathlib import Path

import config
from script_generator import generate_script
from voice_generator   import generate_voiceover
from footage_fetcher   import fetch_all_clips
from visual_builder    import build_visuals
from video_assembler   import assemble_video, get_all_durations
from uploader          import upload_to_youtube

WORKSPACE = Path(config.WORKSPACE_DIR)
WORKSPACE.mkdir(exist_ok=True)


def banner():
    print()
    print("=" * 54)
    print("  YouTube Automation  —  Local AI  •  No API Limits")
    print("=" * 54)
    print(f"  LLM   : Ollama / {config.OLLAMA_MODEL}")
    print(f"  TTS   : {config.TTS_ENGINE}")
    print(f"  Video : Pexels + Pixabay stock footage")
    print("=" * 54)
    print()


def make_job_dir(topic: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower())[:40]
    job_dir = WORKSPACE / f"{slug}_{int(time.time())}"
    job_dir.mkdir(parents=True)
    return job_dir


def run(topic: str):
    job_dir = make_job_dir(topic)

    # ── 1. Script ──────────────────────────────────────────────────────────
    print("[1/6] Generating script...")
    script = generate_script(topic)
    with open(job_dir / "script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    print(f"      Title: {script['title']}\n")

    # ── 2. Voiceover ───────────────────────────────────────────────────────
    print("[2/6] Generating voiceover (local TTS)...")
    audio_files = generate_voiceover(script, job_dir)
    print(f"      {len(audio_files)} audio clips ready.\n")

    # ── 3. Stock footage ───────────────────────────────────────────────────
    print("[3/6] Fetching stock footage...")
    footage_clips = fetch_all_clips(script, job_dir)
    found = sum(1 for c in footage_clips if c and c.exists())
    print(f"      {found}/{len(footage_clips)} clips downloaded.\n")

    # ── 4. Visuals ─────────────────────────────────────────────────────────
    print("[4/6] Building visuals (footage overlay + slide fallbacks)...")
    durations = get_all_durations(audio_files)
    visuals   = build_visuals(script, job_dir, footage_clips, durations)
    footage_count = sum(1 for v in visuals if v["type"] == "video")
    slide_count   = sum(1 for v in visuals if v["type"] == "image")
    print(f"      {footage_count} footage segments, {slide_count} static slides.\n")

    # ── 5. Assemble video ──────────────────────────────────────────────────
    print("[5/6] Assembling final video...")
    output_video = assemble_video(script, audio_files, visuals, durations, job_dir)
    size_mb = output_video.stat().st_size / 1024 / 1024
    print(f"      Done: {output_video} ({size_mb:.1f} MB)\n")

    # ── 6. Upload ──────────────────────────────────────────────────────────
    print("[6/6] Uploading to YouTube...")
    url = upload_to_youtube(
        video_path=output_video,
        title=script["title"],
        description=script["description"],
        tags=script["tags"],
    )
    print(f"\n{'='*54}")
    print(f"  ✓  Published: {url}")
    print(f"{'='*54}\n")

    # ── Cleanup ────────────────────────────────────────────────────────────
    if config.CLEANUP_ON_SUCCESS:
        shutil.rmtree(job_dir)
        print("  Workspace cleaned.\n")
    else:
        print(f"  Job files saved at: {job_dir}\n")


if __name__ == "__main__":
    banner()
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter your video topic: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        sys.exit(1)

    run(topic)
