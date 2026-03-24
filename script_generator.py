"""
script_generator.py
Generates retention-optimised 60-90 second YouTube scripts.

Supports three backends — set LLM_PROVIDER in config.py:
  "groq"   — Groq cloud API (free, ultra-fast, recommended)
  "gemini" — Google Gemini API (free tier, excellent quality)
  "ollama" — Local Ollama model (no internet needed, slower on CPU)
"""

import json
import re
import requests
import config


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert YouTube scriptwriter specialising in faceless educational short videos.
You understand viewer psychology, retention tactics, and what makes people stop scrolling.
Your scripts are punchy, specific, and immediately valuable — never vague or filler-heavy.
You always respond with valid JSON only. No markdown fences, no explanation, no extra text before or after the JSON."""

USER_TEMPLATE = """Write a YouTube Shorts script (under 50 seconds when spoken) about: "{topic}"

This is a VERTICAL SHORT VIDEO. Every word counts. Be punchy, fast, and specific.

STRICT WORD BUDGET — spoken at 130 words/minute, target 85-105 total words:
- intro:          12-15 words  (3-4 seconds — instant hook, no warmup)
- point 1 body:   18-22 words  (8-10 seconds)
- point 2 body:   18-22 words  (8-10 seconds)
- point 3 body:   18-22 words  (8-10 seconds)
- outro:          10-12 words  (4-5 seconds — short, punchy CTA)
- TOTAL:          76-93 words  = 35-43 seconds spoken. DO NOT exceed 93 words total.

Shorts retention rules:
- Intro: One sentence. Shocking fact, bold claim, or direct challenge. No warmup. No "today" or
  "in this video". Viewer must be hooked in 2 seconds or they scroll. Make it feel urgent.
- Each point: One sharp, specific insight. Named psychological concepts, real numbers, or
  counter-intuitive facts only. No generic advice. Make the viewer feel they learned something
  they can use or tell someone else immediately.
- Outro: Maximum 12 words. Direct CTA — follow for more, like if this surprised you. That's it.

Return ONLY a valid JSON object — nothing before or after:
{{
  "title": "Shorts-optimised title, max 60 chars, uses curiosity gap or strong number",
  "description": "2-3 sentences with searchable keywords for this topic",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],
  "intro": "12-15 WORDS EXACTLY. One shocking hook sentence.",
  "outro": "10-12 WORDS EXACTLY. Short punchy call to action.",
  "points": [
    {{
      "heading": "2-4 word heading, punchy",
      "body": "18-22 WORDS EXACTLY. One specific insight, spoken naturally, no lists or colons.",
      "footage_query": "3-5 word concrete visual scene for vertical stock footage"
    }}
  ]
}}

Here is a CORRECT example output for topic "sleep habits" — match this length exactly:
{{
  "title": "3 Sleep Facts That Will Shock You",
  "description": "Three surprising psychology facts about sleep. Neuroscience and dark psychology explained simply.",
  "tags": ["sleep", "psychology", "facts", "neuroscience", "shorts"],
  "intro": "You have been sleeping wrong your entire life and your brain is suffering because of it.",
  "outro": "Follow for more facts that change how you see yourself.",
  "points": [
    {{
      "heading": "Dreams erase memories",
      "body": "During REM sleep your brain actively deletes information it deems useless, which is why you forget ninety percent of your dreams within ten minutes of waking.",
      "footage_query": "person sleeping restlessly at night"
    }},
    {{
      "heading": "Sleep debt is real",
      "body": "Missing just one hour of sleep reduces your cognitive performance by thirty percent, and you cannot recover that deficit by sleeping in on weekends.",
      "footage_query": "tired person at office desk"
    }},
    {{
      "heading": "Brain stays half awake",
      "body": "In a new place your brain keeps one hemisphere alert all night as a survival mechanism, which is why your first night somewhere unfamiliar always feels terrible.",
      "footage_query": "person lying awake in dark room"
    }}
  ]
}}

Now write the same quality and length for topic: "{topic}"
Same structure. Same word density per section. JSON only."""


# ── Backend: Groq ─────────────────────────────────────────────────────────────

def _call_groq(prompt: str) -> str:
    """
    Groq free tier — extremely fast inference on Llama 3.3 70B.
    Get free key: https://console.groq.com
    Quota: 14,400 requests/day, 6,000 tokens/minute — more than enough.
    """
    api_key = config.GROQ_API_KEY
    if not api_key:
        raise ValueError(
            "\n[!] GROQ_API_KEY not set.\n"
            "    1. Go to https://console.groq.com and sign up free\n"
            "    2. Create an API key\n"
            "    3. Add to your .env file: GROQ_API_KEY=your_key_here\n"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.75,
        "max_tokens": 1000,
        "top_p": 0.9,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("\n[!] Cannot reach Groq API. Check your internet connection.\n")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("\n[!] Groq API key is invalid. Check GROQ_API_KEY in your .env file.\n")
        if response.status_code == 429:
            raise RuntimeError("\n[!] Groq rate limit hit. Wait a minute and try again.\n")
        raise RuntimeError(f"\n[!] Groq API error {response.status_code}: {e}\n")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ── Backend: Gemini ───────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    """
    Google Gemini free tier via AI Studio.
    Get free key: https://aistudio.google.com/apikey
    Quota: 1,500 requests/day on Flash models — plenty for daily use.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError(
            "\n[!] GEMINI_API_KEY not set.\n"
            "    1. Go to https://aistudio.google.com/apikey\n"
            "    2. Create a free API key\n"
            "    3. Add to your .env file: GEMINI_API_KEY=your_key_here\n"
        )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={api_key}"
    )

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 1000,
            "topP": 0.9,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("\n[!] Cannot reach Gemini API. Check your internet connection.\n")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            raise ValueError("\n[!] Gemini API key invalid or model not available. Check GEMINI_API_KEY.\n")
        raise RuntimeError(f"\n[!] Gemini API error {response.status_code}: {e}\n")

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"\n[!] Unexpected Gemini response format:\n{json.dumps(data, indent=2)[:400]}\n")


# ── Backend: Ollama (local) ───────────────────────────────────────────────────

def _call_ollama(prompt: str) -> str:
    """Local Ollama — no internet needed but slower on CPU-only machines."""
    url = f"{config.OLLAMA_HOST}/api/generate"

    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.75,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_predict": 800,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"\n[!] Cannot connect to Ollama at {config.OLLAMA_HOST}\n"
            f"    Run in a terminal: ollama serve\n"
            f"    Then pull the model: ollama pull {config.OLLAMA_MODEL}\n"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            "\n[!] Ollama timed out (600s). Your CPU may need more time.\n"
            "    Consider switching to Groq (free, instant) — set LLM_PROVIDER='groq' in config.py\n"
        )

    return response.json().get("response", "").strip()


# ── JSON parsing ──────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"\n[!] Could not parse JSON from model response.\n"
        f"    Try running again — LLMs occasionally produce malformed output.\n"
        f"    Raw output preview:\n{raw[:600]}\n"
    )


# ── Word count enforcement ────────────────────────────────────────────────────

def _enforce_limits(script: dict) -> dict:
    """Trim overlong fields and warn on underlong ones."""
    warnings = []

    # Intro: 12-15 words
    intro_words = script["intro"].split()
    if len(intro_words) < 12:
        warnings.append(f"Intro too short ({len(intro_words)} words, min 12).")
    if len(intro_words) > 15:
        script["intro"] = " ".join(intro_words[:15])

    # Outro: 10-12 words
    outro_words = script["outro"].split()
    if len(outro_words) < 10:
        warnings.append(f"Outro too short ({len(outro_words)} words, min 10).")
    if len(outro_words) > 12:
        script["outro"] = " ".join(outro_words[:12])

    # Each point body: 18-22 words
    for i, point in enumerate(script["points"]):
        body_words = point["body"].split()
        if len(body_words) < 18:
            warnings.append(f"Point {i+1} too short ({len(body_words)} words, min 18).")
        if len(body_words) > 22:
            point["body"] = " ".join(body_words[:22])

    if warnings:
        print("      [Warnings — model returned short content, running anyway]")
        for w in warnings:
            print(f"        - {w}")

    return script


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(script: dict) -> dict:
    required = ["title", "description", "tags", "intro", "outro", "points"]
    for key in required:
        if key not in script:
            raise ValueError(f"\n[!] Script missing field: '{key}'. Run again.\n")

    if not isinstance(script["points"], list) or len(script["points"]) != 3:
        raise ValueError(
            f"\n[!] Expected 3 points, got {len(script.get('points', []))}. Run again.\n"
        )

    for i, point in enumerate(script["points"]):
        point.setdefault("heading", f"Point {i + 1}")
        point.setdefault("body", point["heading"])
        point.setdefault("footage_query", point["heading"])

    return script


# ── Duration estimate ─────────────────────────────────────────────────────────

def _estimate_duration(script: dict) -> str:
    total = (
        len(script["intro"].split())
        + sum(len(p["body"].split()) for p in script["points"])
        + len(script["outro"].split())
    )
    seconds = int((total / 130) * 60)
    return f"~{seconds}s ({total} words @ 130wpm)"


# ── Public entry point ────────────────────────────────────────────────────────

def generate_script(topic: str) -> dict:
    provider = config.LLM_PROVIDER.lower()
    prompt   = USER_TEMPLATE.format(topic=topic)

    print(f"      Provider : {provider.upper()}")

    if provider == "groq":
        print(f"      Model    : {config.GROQ_MODEL}")
        raw = _call_groq(prompt)
    elif provider == "gemini":
        print(f"      Model    : {config.GEMINI_MODEL}")
        raw = _call_gemini(prompt)
    elif provider == "ollama":
        print(f"      Model    : {config.OLLAMA_MODEL} @ {config.OLLAMA_HOST}")
        print(f"      Note     : Generating locally — may take 2-5 min on CPU...")
        raw = _call_ollama(prompt)
    else:
        raise ValueError(
            f"\n[!] Unknown LLM_PROVIDER: '{provider}'\n"
            f"    Set LLM_PROVIDER to 'groq', 'gemini', or 'ollama' in config.py\n"
        )

    script = _parse_json(raw)
    script = _validate(script)
    script = _enforce_limits(script)

    print(f"      Duration : {_estimate_duration(script)}")
    return script