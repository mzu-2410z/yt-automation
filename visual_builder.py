"""
visual_builder.py
Builds visuals for YouTube Shorts — vertical 1080x1920 (9:16).

Strategy:
  1. Generate a transparent PNG overlay with Pillow (text, dots, bars)
  2. Use FFmpeg to composite that overlay onto the footage clip
  This completely avoids FFmpeg drawtext escaping issues on Windows.

Returns list of visual dicts for video_assembler:
  {"type": "video", "path": Path}
  {"type": "image", "path": Path}
"""

import os
import subprocess
import tempfile
from pathlib import Path

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


# ── Text wrapping ─────────────────────────────────────────────────────────────

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


# ── Core slide renderer (used for both static slides and overlay PNGs) ────────

def _render_slide_image(
    size: tuple,
    heading: str,
    body: str,
    bg_color: tuple = (10, 10, 14),
    bg_alpha: int = 255,
    point_number: int = None,
    total_points: int = 3,
    footer_text: str = "Follow for more",
) -> Image.Image:
    """
    Renders a complete slide as an RGBA image.
    bg_alpha=255 → opaque (static slide)
    bg_alpha=0   → transparent background (overlay on footage)
    """
    W, H = size
    img  = Image.new("RGBA", (W, H), (*bg_color, bg_alpha))
    draw = ImageDraw.Draw(img)

    MX = 80   # horizontal margin

    # ── Semi-transparent dark band behind text (only for overlay mode) ──
    if bg_alpha == 0:
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd   = ImageDraw.Draw(band)
        bd.rectangle([0, 600, W, 1400], fill=(0, 0, 0, 175))
        img = Image.alpha_composite(img, band)
        draw = ImageDraw.Draw(img)

    # ── Progress dots ────────────────────────────────────────────────────
    if point_number is not None:
        dot_r   = 10
        dot_gap = 32
        total_w = total_points * (dot_r * 2) + (total_points - 1) * dot_gap
        dot_x   = (W - total_w) // 2
        dot_y   = 660
        for d in range(total_points):
            color = (*config.ACCENT_COLOR, 255) if d < point_number else (60, 60, 75, 200)
            draw.ellipse([dot_x, dot_y, dot_x + dot_r * 2, dot_y + dot_r * 2], fill=color)
            dot_x += dot_r * 2 + dot_gap

    # ── Accent bar ───────────────────────────────────────────────────────
    bar_w = 80
    bar_x = (W - bar_w) // 2
    draw.rectangle(
        [bar_x, 700, bar_x + bar_w, 706],
        fill=(*config.ACCENT_COLOR, 255)
    )

    # ── Heading ──────────────────────────────────────────────────────────
    hfont  = _load_font(88, bold=True)
    hlines = _wrap_text(draw, heading.upper(), hfont, W - MX * 2)
    h_lh   = int(88 * 1.2)
    h_y    = 730

    for line in hlines:
        bbox = draw.textbbox((0, 0), line, font=hfont)
        x    = (W - bbox[2]) // 2
        draw.text((x, h_y), line, font=hfont, fill=(*config.HEADING_COLOR, 255))
        h_y += h_lh

    # ── Body text ─────────────────────────────────────────────────────────
    bfont  = _load_font(52, bold=False)
    blines = _wrap_text(draw, body, bfont, W - MX * 2)
    b_lh   = int(52 * 1.6)
    b_y    = h_y + 40

    for line in blines:
        bbox = draw.textbbox((0, 0), line, font=bfont)
        x    = (W - bbox[2]) // 2
        draw.text((x, b_y), line, font=bfont, fill=(*config.BODY_COLOR, 255))
        b_y += b_lh

    # ── Footer ────────────────────────────────────────────────────────────
    if footer_text:
        ffont = _load_font(30)
        fbbox = draw.textbbox((0, 0), footer_text, font=ffont)
        draw.text(
            ((W - fbbox[2]) // 2, H - 100),
            footer_text,
            font=ffont,
            fill=(80, 80, 95, 200)
        )

    return img


def _render_title_image(size: tuple, title: str, bg_alpha: int = 255) -> Image.Image:
    W, H  = size
    bg    = (10, 10, 14)
    img   = Image.new("RGBA", (W, H), (*bg, bg_alpha))
    draw  = ImageDraw.Draw(img)

    if bg_alpha == 0:
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd   = ImageDraw.Draw(band)
        bd.rectangle([0, 600, W, 1100], fill=(0, 0, 0, 175))
        img  = Image.alpha_composite(img, band)
        draw = ImageDraw.Draw(img)

    tfont  = _load_font(92, bold=True)
    lines  = _wrap_text(draw, title, tfont, W - 160)
    lh     = int(92 * 1.25)
    total  = lh * len(lines)
    y      = (H - total) // 2 - 60

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=tfont)
        draw.text(((W - bbox[2]) // 2, y), line, font=tfont, fill=(*config.HEADING_COLOR, 255))
        y += lh

    bar_w = 100
    draw.rectangle(
        [(W - bar_w) // 2, y + 30, (W + bar_w) // 2, y + 38],
        fill=(*config.ACCENT_COLOR, 255)
    )
    return img


# ── Static slide (PNG) ────────────────────────────────────────────────────────

def _make_static_slide(job_dir, label, heading, body, point_number=None, total_points=3):
    img = _render_slide_image(
        size=(config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT),
        heading=heading, body=body,
        bg_alpha=255,
        point_number=point_number, total_points=total_points,
    )
    out = job_dir / "slides" / f"{label}.png"
    out.parent.mkdir(exist_ok=True)
    img.convert("RGB").save(str(out), "PNG")
    return out


def _make_title_slide(job_dir, title):
    img = _render_title_image(
        size=(config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT),
        title=title, bg_alpha=255,
    )
    out = job_dir / "slides" / "title.png"
    out.parent.mkdir(exist_ok=True)
    img.convert("RGB").save(str(out), "PNG")
    return out


# ── Footage overlay (PNG composite via FFmpeg) ────────────────────────────────

def _overlay_on_footage(
    footage_path: Path,
    out_path: Path,
    overlay_img: Image.Image,
    duration: float,
) -> Path:
    """
    Saves overlay as a temp PNG then uses FFmpeg overlay filter to composite
    it on top of the footage. No drawtext — zero escaping issues.
    """
    W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT

    # Save overlay PNG to a temp file
    tmp_overlay = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_overlay.close()
    overlay_img.save(tmp_overlay.name, "PNG")

    # Convert all paths to forward slashes for FFmpeg on Windows
    footage_p = str(footage_path).replace("\\", "/")
    overlay_p = tmp_overlay.name.replace("\\", "/")
    out_p     = str(out_path).replace("\\", "/")

    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}"
        f"[base];"
        f"[base][1:v]overlay=0:0"
    )

    cmd = [
        config.FFMPEG_BIN, "-y",
        "-stream_loop", "-1",
        "-i", footage_p,
        "-i", overlay_p,
        "-filter_complex", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        out_p,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-600:])
        return out_path
    finally:
        Path(tmp_overlay.name).unlink(missing_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

def build_visuals(
    script: dict,
    job_dir: Path,
    footage_clips: list,
    audio_durations: list[float],
) -> list[dict]:

    visuals_dir  = job_dir / "visuals"
    visuals_dir.mkdir(exist_ok=True)

    W, H         = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    total_points = len(script["points"])

    sections_meta = [
        {"label": "intro",  "heading": script["title"], "body": script["intro"],  "num": None,  "is_title": True},
        *[
            {"label": f"point_{i+1}", "heading": p["heading"], "body": p["body"], "num": i+1, "is_title": False}
            for i, p in enumerate(script["points"])
        ],
        {"label": "outro",  "heading": "Follow for more", "body": script["outro"], "num": None, "is_title": False},
    ]

    visuals = []

    for i, meta in enumerate(sections_meta):
        label    = meta["label"]
        clip     = footage_clips[i] if footage_clips and i < len(footage_clips) else None
        duration = audio_durations[i] + 0.4

        if clip and clip.exists() and clip.stat().st_size > 0:
            out_path = visuals_dir / f"{label}.mp4"
            try:
                # Build transparent overlay image
                if meta["is_title"]:
                    overlay = _render_title_image((W, H), meta["heading"], bg_alpha=0)
                else:
                    overlay = _render_slide_image(
                        size=(W, H),
                        heading=meta["heading"],
                        body=meta["body"],
                        bg_alpha=0,
                        point_number=meta["num"],
                        total_points=total_points,
                        footer_text="Follow for more" if label == "outro" else "",
                    )

                _overlay_on_footage(clip, out_path, overlay, duration)
                visuals.append({"type": "video", "path": out_path})
                continue

            except Exception as e:
                print(f"        [Warning] Footage overlay failed for {label}: {e}")
                print(f"        Falling back to static slide.")

        # Static slide fallback
        if meta["is_title"]:
            slide_path = _make_title_slide(job_dir, meta["heading"])
        else:
            slide_path = _make_static_slide(
                job_dir, label, meta["heading"], meta["body"],
                meta["num"], total_points
            )
        visuals.append({"type": "image", "path": slide_path})

    return visuals