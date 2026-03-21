"""
script_generator.py
Generates structured video scripts using a local Ollama LLM.
No API key needed — runs entirely on your machine.
"""

import json
import re
import requests
import config


SYSTEM_PROMPT = """You are a YouTube scriptwriter for a faceless educational channel.
Write clear, engaging scripts optimised for text-on-screen delivery with voiceover.
Respond with valid JSON only. No markdown, no explanation, no extra text."""

USER_TEMPLATE = """Write a short educational YouTube script about: "{topic}"

Return ONLY a JSON object with this exact structure:
{{
  "title": "Compelling YouTube title (max 60 chars)",
  "description": "YouTube description 2-3 sentences with keywords",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "intro": "One engaging opening sentence (15-25 words)",
  "outro": "One closing sentence with call to action to like and subscribe (15-20 words)",
  "points": [
    {{
      "heading": "Short heading (3-6 words)",
      "body": "Explanation spoken aloud (25-40 words, conversational, factual)",
      "footage_query": "2-4 word search query to find relevant stock video for this point"
    }}
  ]
}}

Rules:
- Exactly 5 points
- Each point is self-contained and factual
- footage_query must be visual and concrete (e.g. "person sleeping peacefully", "healthy breakfast food")
- Tone: friendly, informative, confident
- JSON only, nothing else"""


def _call_ollama(prompt: str) -> str:
    """Send a prompt to the local Ollama server and return the response text."""
    url = f"{config.OLLAMA_HOST}/api/generate"

    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"\n[!] Cannot connect to Ollama at {config.OLLAMA_HOST}\n"
            f"    Make sure Ollama is running: open a terminal and run `ollama serve`\n"
            f"    Then ensure you have the model pulled: `ollama pull {config.OLLAMA_MODEL}`"
        )

    data = response.json()
    return data.get("response", "").strip()


def _parse_json(raw: str) -> dict:
    """Extract and parse JSON from LLM output, handling common formatting issues."""
    # Strip markdown code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting the first {...} block
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse JSON from LLM response.\n"
        f"Model returned:\n{raw[:500]}\n\n"
        f"Try a different model in config.py (OLLAMA_MODEL) or run again."
    )


def _validate(script: dict) -> dict:
    required = ["title", "description", "tags", "intro", "outro", "points"]
    for key in required:
        if key not in script:
            raise ValueError(f"Script missing required field: '{key}'")

    if not isinstance(script["points"], list) or len(script["points"]) != 5:
        raise ValueError(
            f"Expected exactly 5 points, got {len(script.get('points', []))}. "
            f"Try running again."
        )

    for i, point in enumerate(script["points"]):
        for field in ["heading", "body", "footage_query"]:
            if field not in point:
                point[field] = point.get("heading", f"point {i+1}") if field == "footage_query" else ""

    return script


def generate_script(topic: str) -> dict:
    prompt = USER_TEMPLATE.format(topic=topic)
    print(f"      Using model: {config.OLLAMA_MODEL} @ {config.OLLAMA_HOST}")

    raw = _call_ollama(prompt)
    script = _parse_json(raw)
    script = _validate(script)
    return script
