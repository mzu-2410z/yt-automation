"""
visual_builder.py
Two modes:
  1. Footage mode  — burns text overlay onto a video clip (used when footage was found)
  2. Slide mode    — generates a static PNG (fallback when no footage available)

Returns a list of "visual" dicts that video_assembler understands:
  {"type": "video", "path": Path, "has_audio": bool}
  {"type": "image", "path": Path}
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
import config


# ── Font loader ───────────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
            r"C:\Windows\Fonts\seguibl.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
        ]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Static slide generator ────────────────────────────────────────────────────

def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if draw.textbbox((0, 0), test, font=font)[2] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _make_static_slide(
    job_dir: Path,
    label: str,
    heading: str,
    body: str,
    point_number: int = None,
) -> Path:
    W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    img = Image.new("RGB", (W, H), (10, 10, 14))
    draw = ImageDraw.Draw(img)

    MX = 160
    # Accent bar
    draw.rectangle([MX, 320, MX + 80, 326], fill=config.ACCENT_COLOR)

    # Point counter
    if point_number is not None:
        num_font = _load_font(28)
        draw.text((MX, 272), f"{point_number} / 5", font=num_font, fill=config.ACCENT_COLOR)

    # Heading
    hfont = _load_font(config.FONT_HEADING_SIZE, bold=True)
    lines = _wrap_text(draw, heading.upper(), hfont, W - MX * 2)
    y = 360
    for line in lines:
        draw.text((MX, y), line, font=hfont, fill=config.HEADING_COLOR)
        y += int(config.FONT_HEADING_SIZE * 1.2)

    # Body
    bfont = _load_font(config.FONT_BODY_SIZE)
    lines = _wrap_text(draw, body, bfont, W - MX * 2)
    y = max(y + 20, 490)
    for line in lines:
        draw.text((MX, y), line, font=bfont, fill=config.BODY_COLOR)
        y += int(config.FONT_BODY_SIZE * 1.55)

    # Footer
    ffont = _load_font(26)
    draw.text((MX, H - 80), "Subscribe for more", font=ffont, fill=(80, 80, 95))

    out = job_dir / "slides" / f"{label}.png"
    out.parent.mkdir(exist_ok=True)
    img.save(str(out), "PNG")
    return out


def _make_title_slide(job_dir: Path, title: str) -> Path:
    W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    img = Image.new("RGB", (W, H), (10, 10, 14))
    draw = ImageDraw.Draw(img)

    tfont = _load_font(96, bold=True)
    lines = _wrap_text(draw, title, tfont, W - 320)
    lh = int(96 * 1.3)
    y = (H - lh * len(lines)) // 2 - 40

    for line in lines:
        bw = draw.textbbox((0, 0), line, font=tfont)[2]
        draw.text(((W - bw) // 2, y), line, font=tfont, fill=config.HEADING_COLOR)
        y += lh

    draw.rectangle([(W // 2 - 80), y + 20, (W // 2 + 80), y + 26], fill=config.ACCENT_COLOR)

    out = job_dir / "slides" / "title.png"
    out.parent.mkdir(exist_ok=True)
    img.save(str(out), "PNG")
    return out


# ── Footage overlay via FFmpeg ────────────────────────────────────────────────

def _escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'",  "\\'")
    text = text.replace(":",  "\\:")
    text = text.replace("[",  "\\[")
    text = text.replace("]",  "\\]")
    return text


def _find_font() -> str:
    """Return the path to a usable font for FFmpeg drawtext."""
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


def _overlay_text_on_footage(
    footage_path: Path,
    out_path: Path,
    heading: str,
    body: str,
    duration: float,
    point_number: int = None,
) -> Path:
    """
    Use FFmpeg to:
    1. Trim/loop footage to required duration
    2. Darken the footage with an overlay
    3. Burn heading + body text on top
    """
    font_path = _find_font()
    font_arg  = f":fontfile='{font_path}'" if font_path else ""

    W, H   = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    opacity = config.OVERLAY_BG_OPACITY
    MX      = 160
    accent  = "6366F1"  # Indigo hex for drawtext

    heading_esc = _escape_ffmpeg_text(heading.upper())
    body_esc    = _escape_ffmpeg_text(body)

    # Build point number text if needed
    num_filter = ""
    if point_number:
        num_filter = (
            f"drawtext=text='{point_number} / 5'"
            f"{font_arg}"
            f":fontsize=28:fontcolor=#{accent}@1.0"
            f":x={MX}:y=272,"
        )

    vf = (
        # Scale + pad to output resolution
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        # Dark overlay
        f"colorchannelmixer=aa={1 - opacity},"
        f"drawbox=x=0:y=0:w={W}:h={H}:color=black@{opacity}:t=fill,"
        # Accent bar
        f"drawbox=x={MX}:y=320:w=80:h=6:color=#6366F1@1.0:t=fill,"
        # Point number
        + num_filter +
        # Heading
        f"drawtext=text='{heading_esc}'"
        f"{font_arg}"
        f":fontsize={config.FONT_HEADING_SIZE}:fontcolor=white@1.0"
        f":x={MX}:y=360:line_spacing=8,"
        # Body
        f"drawtext=text='{body_esc}'"
        f"{font_arg}"
        f":fontsize={config.FONT_BODY_SIZE}:fontcolor=#C8C8DC@1.0"
        f":x={MX}:y=490:line_spacing=10"
    )

    cmd = [
        config.FFMPEG_BIN, "-y",
        "-stream_loop", "-1",
        "-i", str(footage_path),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",   # No audio from footage
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg footage overlay failed for '{out_path.name}':\n{result.stderr[-600:]}"
        )
    return out_path


# ── Public API ────────────────────────────────────────────────────────────────

def build_visuals(
    script: dict,
    job_dir: Path,
    footage_clips: list,           # list of Path | None, aligned with sections
    audio_durations: list[float],  # duration per section in seconds
) -> list[dict]:
    """
    Returns a list of visual dicts, one per section:
      {"type": "video", "path": Path}  — footage with text burned in
      {"type": "image", "path": Path}  — static PNG slide
    """
    visuals_dir = job_dir / "visuals"
    visuals_dir.mkdir(exist_ok=True)

    sections_meta = [
        {"label": "intro",    "heading": script["title"],         "body": script["intro"],  "num": None},
        *[
            {"label": f"point_{i+1}", "heading": p["heading"], "body": p["body"], "num": i+1}
            for i, p in enumerate(script["points"])
        ],
        {"label": "outro",    "heading": "Thanks for watching",    "body": script["outro"],  "num": None},
    ]

    visuals = []

    for i, meta in enumerate(sections_meta):
        label    = meta["label"]
        clip     = footage_clips[i] if footage_clips and i < len(footage_clips) else None
        duration = audio_durations[i] + 0.5  # add small buffer

        if clip and clip.exists() and clip.stat().st_size > 0:
            # Footage mode — burn text onto video
            out_path = visuals_dir / f"{label}.mp4"
            try:
                _overlay_text_on_footage(
                    footage_path=clip,
                    out_path=out_path,
                    heading=meta["heading"],
                    body=meta["body"],
                    duration=duration,
                    point_number=meta["num"],
                )
                visuals.append({"type": "video", "path": out_path})
                continue
            except Exception as e:
                print(f"        [Warning] Footage overlay failed for {label}: {e}")
                print(f"        Falling back to static slide.")

        # Static slide fallback
        if label == "intro":
            slide_path = _make_title_slide(job_dir, script["title"])
        else:
            slide_path = _make_static_slide(
                job_dir, label, meta["heading"], meta["body"], meta["num"]
            )
        visuals.append({"type": "image", "path": slide_path})

    return visuals
