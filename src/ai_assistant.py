"""Gemini-powered intent parsing and recommendation explanation."""

import json
import logging
from typing import Dict, List, Optional, Tuple

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_KNOWN_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "reggaeton", "electronic", "folk", "dream pop", "hip hop",
}
_KNOWN_MOODS = {
    "happy", "chill", "intense", "relaxed", "focused",
    "moody", "playful", "warm", "dreamy", "confident", "tense",
}

_SYSTEM_PROMPT = """You are a music preference assistant. You help users find music by:
1. Parsing their natural language descriptions into structured preferences
2. Explaining why recommended songs match their request

Available music attributes:
- Genres: pop, lofi, rock, ambient, jazz, synthwave, indie pop, reggaeton, electronic, folk, dream pop, hip hop
- Moods: happy, chill, intense, relaxed, focused, moody, playful, warm, dreamy, confident, tense
- Energy: float 0.0 (very calm) to 1.0 (very energetic)
- likes_acoustic: boolean, whether the user prefers acoustic-sounding tracks
- confidence: float 0.0–1.0, how clearly the request maps to the available options"""

_MODEL = "gemini-2.0-flash"

# ── Few-shot examples for specialization ──────────────────────────────────────
# These guide Gemini on tricky or ambiguous requests that zero-shot prompting
# tends to map inconsistently. Measurable effect: higher confidence scores and
# more accurate genre/mood mapping on edge-case inputs.
_FEW_SHOT_EXAMPLES = [
    (
        "songs to cry to alone at night",
        '{"genre": "folk", "mood": "warm", "energy": 0.25, "likes_acoustic": true, "confidence": 0.82}',
    ),
    (
        "background music for deep work and coding",
        '{"genre": "lofi", "mood": "focused", "energy": 0.40, "likes_acoustic": false, "confidence": 0.91}',
    ),
    (
        "late night city drive with neon lights",
        '{"genre": "synthwave", "mood": "moody", "energy": 0.72, "likes_acoustic": false, "confidence": 0.88}',
    ),
    (
        "hype music to get pumped before a big game",
        '{"genre": "hip hop", "mood": "confident", "energy": 0.87, "likes_acoustic": false, "confidence": 0.90}',
    ),
    (
        "something for a lazy quiet sunday morning",
        '{"genre": "jazz", "mood": "relaxed", "energy": 0.33, "likes_acoustic": true, "confidence": 0.86}',
    ),
]


def _build_few_shot_block() -> str:
    lines = ["Here are examples of how to convert descriptions:\n"]
    for user_input, json_output in _FEW_SHOT_EXAMPLES:
        lines.append(f'User: "{user_input}"')
        lines.append(f"JSON: {json_output}\n")
    return "\n".join(lines)


def _get_client() -> genai.Client:
    import os
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _parse_prefs_json(raw: str) -> Dict:
    """Strips code fences, parses JSON, validates required keys, coerces types."""
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
    prefs = json.loads(raw.strip())
    for key in ("genre", "mood", "energy", "likes_acoustic"):
        if key not in prefs:
            raise ValueError(f"Missing required key: {key}")
    prefs["energy"] = float(prefs["energy"])
    prefs["likes_acoustic"] = bool(prefs["likes_acoustic"])
    prefs["confidence"] = float(prefs.get("confidence", 0.5))
    return prefs


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_user_intent(description: str, few_shot: bool = True) -> Dict:
    """
    Converts a natural language music description into structured preferences.

    Args:
        description : what the user typed
        few_shot    : if True (default), includes curated examples in the prompt
                      for better accuracy on ambiguous requests

    Returns a dict: genre, mood, energy, likes_acoustic, confidence.
    """
    logger.info("Parsing user intent (few_shot=%s): %.100s", few_shot, description)

    few_shot_block = _build_few_shot_block() + "\nNow convert the following:\n" if few_shot else ""

    prompt = (
        f"{few_shot_block}"
        f'User: "{description}"\n\n'
        "Reply with ONLY valid JSON using exactly these keys:\n"
        "genre, mood, energy (0.0–1.0), likes_acoustic (true/false), confidence (0.0–1.0)\n\n"
        'Example: {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": false, "confidence": 0.9}'
    )

    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
    )
    raw = response.text.strip()
    logger.debug("Gemini raw response: %s", raw)

    try:
        prefs = _parse_prefs_json(raw)
        if prefs["genre"] not in _KNOWN_GENRES:
            logger.warning("Unrecognised genre '%s'", prefs["genre"])
        if prefs["mood"] not in _KNOWN_MOODS:
            logger.warning("Unrecognised mood '%s'", prefs["mood"])
        logger.info(
            "Parsed: genre=%s mood=%s energy=%.2f confidence=%.2f",
            prefs["genre"], prefs["mood"], prefs["energy"], prefs["confidence"],
        )
        return prefs
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.error("Failed to parse Gemini response '%s': %s", raw, exc)
        raise ValueError(f"Could not parse music preferences: {exc}") from exc


def explain_recommendations(
    user_description: str,
    preferences: Dict,
    recommendations: List[Tuple],
    context: Optional[Dict] = None,
) -> str:
    """
    Generates a natural language explanation for the recommended songs.

    If `context` is provided (from the enhanced RAG retriever), Gemini uses
    genre and mood descriptions from the knowledge base to write richer,
    more specific explanations than it could from song metadata alone.
    """
    logger.info("Generating explanation (with_context=%s)", context is not None)

    song_list = "\n".join(
        f"- {s['title']} by {s['artist']} "
        f"(genre={s['genre']}, mood={s['mood']}, energy={s['energy']:.2f})"
        for s, _, _ in recommendations
    )

    context_block = ""
    if context:
        genre_ctx = context.get("genre", {})
        mood_ctx  = context.get("mood", {})
        if genre_ctx or mood_ctx:
            context_block = "\nKnowledge base context:\n"
        if genre_ctx:
            context_block += (
                f"- {preferences['genre'].title()}: {genre_ctx.get('description', '')}\n"
                f"  Typical use cases: {', '.join(genre_ctx.get('use_cases', []))}\n"
            )
        if mood_ctx:
            context_block += (
                f"- {preferences['mood'].title()} mood: {mood_ctx.get('description', '')}\n"
                f"  Energy hint: {mood_ctx.get('energy_hint', '')}\n"
            )

    prompt = (
        f'User asked for: "{user_description}"\n'
        f"Interpreted as: genre={preferences['genre']}, mood={preferences['mood']}, "
        f"energy={preferences['energy']:.2f}, likes_acoustic={preferences['likes_acoustic']}"
        f"{context_block}\n\n"
        f"Recommended songs:\n{song_list}\n\n"
        "Write 2–3 sentences explaining why these songs fit the request. "
        "Reference specific musical qualities from the knowledge base context if available. "
        "Keep it friendly and concise."
    )

    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
    )
    explanation = response.text.strip()
    logger.info("Explanation generated (%d chars, context=%s)", len(explanation), context is not None)
    return explanation
