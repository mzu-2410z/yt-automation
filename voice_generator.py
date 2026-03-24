"""
voice_generator.py
Local TTS — supports Kokoro, Coqui XTTS, and Piper.
Zero cloud calls. No API keys. Runs entirely on your machine.
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path

import config


# ── Section builder ──────────────────────────────────────────────────────────

def build_sections(script: dict) -> list[dict]:
    """Return ordered list of {label, text} dicts matching the slide order."""
    sections = [{"label": "intro", "text": script["intro"]}]
    for i, point in enumerate(script["points"]):
        text = f"{point['heading']}. {point['body']}"
        sections.append({"label": f"point_{i+1}", "text": text})
    sections.append({"label": "outro", "text": script["outro"]})
    return sections


# ── Kokoro TTS ───────────────────────────────────────────────────────────────

def _generate_kokoro(sections: list[dict], audio_dir: Path) -> list[Path]:
    """
    Uses kokoro-onnx (CPU-compatible, no GPU needed).
    Install: pip install kokoro-onnx soundfile
    Model downloads automatically on first run (~80 MB).
    """
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
        import numpy as np
    except ImportError:
        raise ImportError(
            "\n[!] Kokoro not installed.\n"
            "    Run: pip install kokoro-onnx soundfile\n"
            "    First run will download the model (~80MB) automatically."
        )

    print(f"      Kokoro voice: {config.KOKORO_VOICE} | speed: {config.KOKORO_SPEED}")
    BASE_DIR = Path(__file__).parent
    kokoro = Kokoro(
        str(BASE_DIR / "kokoro-v1.0.onnx"),
        str(BASE_DIR / "voices-v1.0.bin")
    )

    paths = []
    for section in sections:
        out_path = audio_dir / f"{section['label']}.wav"
        samples, sample_rate = kokoro.create(
            section["text"],
            voice=config.KOKORO_VOICE,
            speed=config.KOKORO_SPEED,
            lang="en-us"
        )
        sf.write(str(out_path), samples, sample_rate)
        paths.append(out_path)

    return paths


# ── Coqui TTS ────────────────────────────────────────────────────────────────

def _generate_coqui(sections: list[dict], audio_dir: Path) -> list[Path]:
    """
    Uses Coqui TTS (TTS library).
    Install: pip install TTS
    First run downloads model automatically.
    """
    try:
        from TTS.api import TTS
    except ImportError:
        raise ImportError(
            "\n[!] Coqui TTS not installed.\n"
            "    Run: pip install TTS\n"
            "    Note: TTS installs torch — large download (~2GB). Be patient."
        )

    print(f"      Coqui model: {config.COQUI_MODEL}")
    tts = TTS(model_name=config.COQUI_MODEL, progress_bar=False)

    paths = []
    for section in sections:
        out_path = audio_dir / f"{section['label']}.wav"
        tts.tts_to_file(text=section["text"], file_path=str(out_path))
        paths.append(out_path)

    return paths


# ── Piper TTS ────────────────────────────────────────────────────────────────

def _generate_piper(sections: list[dict], audio_dir: Path) -> list[Path]:
    """
    Uses Piper TTS — fastest, most lightweight option.
    Download piper.exe + voice model from:
    https://github.com/rhasspy/piper/releases
    Set PIPER_EXE and PIPER_MODEL in config.py.
    """
    import shutil
    piper_exe = config.PIPER_EXE

    if not Path(piper_exe).exists() and not shutil.which("piper"):
        raise FileNotFoundError(
            f"\n[!] Piper executable not found at: {piper_exe}\n"
            f"    Download from: https://github.com/rhasspy/piper/releases\n"
            f"    Then set PIPER_EXE in config.py"
        )

    model_path = config.PIPER_MODEL
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"\n[!] Piper voice model not found: {model_path}\n"
            f"    Download .onnx model + .json config from:\n"
            f"    https://github.com/rhasspy/piper/blob/master/VOICES.md\n"
            f"    Then set PIPER_MODEL in config.py"
        )

    print(f"      Piper model: {model_path}")
    paths = []
    for section in sections:
        out_path = audio_dir / f"{section['label']}.wav"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write(section["text"])
            tmp_input = tf.name

        cmd = [piper_exe, "--model", model_path, "--output_file", str(out_path)]
        with open(tmp_input, "r", encoding="utf-8") as inp:
            result = subprocess.run(cmd, stdin=inp, capture_output=True, text=True)

        Path(tmp_input).unlink(missing_ok=True)

        if result.returncode != 0:
            raise RuntimeError(f"Piper failed on '{section['label']}':\n{result.stderr}")
        paths.append(out_path)

    return paths


# ── Dispatcher ───────────────────────────────────────────────────────────────

def generate_voiceover(script: dict, job_dir: Path) -> list[Path]:
    audio_dir = job_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    sections = build_sections(script)
    engine = config.TTS_ENGINE.lower()

    print(f"      TTS engine: {engine}")

    if engine == "kokoro":
        paths = _generate_kokoro(sections, audio_dir)
    elif engine == "coqui":
        paths = _generate_coqui(sections, audio_dir)
    elif engine == "piper":
        paths = _generate_piper(sections, audio_dir)
    else:
        raise ValueError(
            f"Unknown TTS engine: '{engine}'. "
            f"Set TTS_ENGINE to 'kokoro', 'coqui', or 'piper' in config.py"
        )

    # Verify all files exist and are non-empty
    for p in paths:
        if not p.exists() or p.stat().st_size == 0:
            raise RuntimeError(f"Audio file missing or empty after TTS: {p}")

    return paths
