"""Gemini-powered intent parsing and recommendation explanation."""

import json
import logging
from typing import Dict, List, Tuple

import google.generativeai as genai

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a music preference assistant. You help users find music by:
1. Parsing their natural language descriptions into structured preferences
2. Explaining why recommended songs match their request

Available music attributes:
- Genres: pop, lofi, rock, ambient, jazz, synthwave, indie pop, reggaeton, electronic, folk, dream pop, hip hop
- Moods: happy, chill, intense, relaxed, focused, moody, playful, warm, dreamy, confident, tense
- Energy: float 0.0 (very calm) to 1.0 (very energetic)
- likes_acoustic: boolean, whether the user prefers acoustic-sounding tracks"""


def parse_user_intent(description: str) -> Dict:
    """Converts a natural language music description into structured preferences using Gemini."""
    logger.info("Parsing user intent: %.100s", description)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_SYSTEM_PROMPT,
    )

    prompt = (
        f'Convert this music request into JSON preferences: "{description}"\n\n'
        "Reply with ONLY valid JSON using exactly these keys: "
        "genre, mood, energy (0.0–1.0), likes_acoustic (true/false).\n"
        'Example: {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": false}'
    )

    response = model.generate_content(prompt)
    raw = response.text.strip()
    logger.debug("Gemini raw response: %s", raw)

    # Strip markdown code fences if Gemini wrapped the JSON
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    try:
        prefs = json.loads(raw)
        for key in ("genre", "mood", "energy", "likes_acoustic"):
            if key not in prefs:
                raise ValueError(f"Missing required key: {key}")
        prefs["energy"] = float(prefs["energy"])
        prefs["likes_acoustic"] = bool(prefs["likes_acoustic"])
        logger.info("Parsed preferences: %s", prefs)
        return prefs
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.error("Failed to parse Gemini response '%s': %s", raw, exc)
        raise ValueError(f"Could not parse music preferences from your description: {exc}") from exc


def explain_recommendations(
    user_description: str,
    preferences: Dict,
    recommendations: List[Tuple],
) -> str:
    """Generates a natural language explanation for why the recommended songs fit the request."""
    logger.info("Generating explanation for %d recommendations", len(recommendations))

    song_list = "\n".join(
        f"- {s['title']} by {s['artist']} "
        f"(genre={s['genre']}, mood={s['mood']}, energy={s['energy']:.2f})"
        for s, _, _ in recommendations
    )

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_SYSTEM_PROMPT,
    )

    prompt = (
        f'User asked for: "{user_description}"\n'
        f"Interpreted as: genre={preferences['genre']}, mood={preferences['mood']}, "
        f"energy={preferences['energy']:.2f}, likes_acoustic={preferences['likes_acoustic']}\n\n"
        f"Recommended songs:\n{song_list}\n\n"
        "Write 2–3 sentences explaining why these songs fit the request. "
        "Mention specific musical qualities. Keep it friendly and concise."
    )

    response = model.generate_content(prompt)
    explanation = response.text.strip()
    logger.info("Explanation generated (%d chars)", len(explanation))
    return explanation
