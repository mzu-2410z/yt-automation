"""
video_assembler.py
Stitches visual segments (footage clips or static slides) + audio into final MP4.
Handles mixed input: some sections may be footage, others static images.
"""

import json
import subprocess
from pathlib import Path

import config


def get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            config.FFPROBE_BIN, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def get_all_durations(audio_files: list[Path]) -> list[float]:
    return [get_audio_duration(p) for p in audio_files]


def _make_segment(
    visual: dict,
    audio_path: Path,
    out_path: Path,
    duration: float,
    fade: float = 0.35,
) -> Path:
    """Combine one visual + one audio track into a single segment MP4."""
    W, H  = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    t_out = max(0.0, duration - fade - 0.05)

    scale_pad = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
    )
    fade_filter = (
        f",fade=t=in:st=0:d={fade}"
        f",fade=t=out:st={t_out:.2f}:d={fade}"
    )

    if visual["type"] == "image":
        video_filter = scale_pad + fade_filter
        cmd = [
            config.FFMPEG_BIN, "-y",
            "-loop", "1",
            "-i", str(visual["path"]),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-vf", video_filter,
            "-shortest",
            str(out_path),
        ]
    else:
        # Footage clip already has text burned in; just sync audio
        video_filter = scale_pad + fade_filter
        cmd = [
            config.FFMPEG_BIN, "-y",
            "-i", str(visual["path"]),   # video (no audio)
            "-i", str(audio_path),       # voiceover
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-vf", video_filter,
            "-shortest",
            str(out_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg segment failed for {out_path.name}:\n{result.stderr[-600:]}"
        )
    return out_path


def assemble_video(
    script: dict,
    audio_files: list[Path],
    visuals: list[dict],
    durations: list[float],
    job_dir: Path,
) -> Path:
    if len(audio_files) != len(visuals):
        raise ValueError(
            f"Mismatch: {len(audio_files)} audio files vs {len(visuals)} visuals."
        )

    segments_dir = job_dir / "segments"
    segments_dir.mkdir(exist_ok=True)

    segment_paths = []
    for i, (visual, audio, dur) in enumerate(zip(visuals, audio_files, durations)):
        seg_out = segments_dir / f"seg_{i:02d}.mp4"
        print(f"      Segment {i+1}/{len(visuals)}: {visual['type']} + audio")
        _make_segment(visual, audio, seg_out, dur + 0.3)
        segment_paths.append(seg_out)

    # Concat all segments
    concat_list = job_dir / "concat.txt"
    with open(concat_list, "w") as f:
        for seg in segment_paths:
            f.write(f"file '{seg.resolve()}'\n")

    merged_path = job_dir / "merged.mp4"
    merge_cmd = [
        config.FFMPEG_BIN, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(merged_path),
    ]
    result = subprocess.run(merge_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed:\n{result.stderr[-600:]}")

    # Mix background music if enabled and file exists
    output_path = job_dir / "final.mp4"
    music_path  = Path(config.BG_MUSIC_PATH)

    if config.BG_MUSIC_ENABLED and music_path.exists():
        vol = config.BG_MUSIC_VOLUME
        music_cmd = [
            config.FFMPEG_BIN, "-y",
            "-i", str(merged_path),
            "-stream_loop", "-1",
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={vol},apad[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[out]",
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(music_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [Warning] Background music mix failed. Using video without music.")
            output_path = merged_path
    else:
        output_path = merged_path
        if config.BG_MUSIC_ENABLED:
            print(f"  [Info] Background music enabled but {music_path} not found.")
            print(f"         Drop a royalty-free MP3 at '{config.BG_MUSIC_PATH}' to enable it.")

    return output_path
