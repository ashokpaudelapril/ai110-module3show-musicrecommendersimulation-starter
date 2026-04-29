"""
Enhanced RAG retriever.

Combines two data sources:
  1. data/songs.csv          — the song catalog
  2. data/genre_knowledge.json + data/mood_knowledge.json — the knowledge base

The knowledge base gives Gemini richer context about what each genre and mood
actually sounds like, which produces more specific and accurate explanations
than using song metadata alone.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from recommender import recommend_songs

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> Dict:
    path = _DATA_DIR / filename
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Knowledge base file not found: %s", path)
        return {}


def retrieve(
    prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    scoring_mode: str = "balanced",
) -> Tuple[List[Tuple], Dict]:
    """
    Retrieves matching songs AND relevant knowledge base context.

    Returns:
        recommendations : list of (song, score, reasons) — from the song catalog
        context         : {"genre": {...}, "mood": {...}} — from the knowledge base
    """
    recommendations = recommend_songs(prefs, songs, k=k, scoring_mode=scoring_mode)

    genre_kb = _load_json("genre_knowledge.json")
    mood_kb  = _load_json("mood_knowledge.json")

    genre = prefs.get("genre", "")
    mood  = prefs.get("mood", "")

    context = {
        "genre": genre_kb.get(genre, {}),
        "mood":  mood_kb.get(mood, {}),
    }

    if context["genre"]:
        logger.info(
            "RAG: loaded genre context for '%s' — %s",
            genre, context["genre"].get("description", "")[:60],
        )
    if context["mood"]:
        logger.info(
            "RAG: loaded mood context for '%s' — %s",
            mood, context["mood"].get("description", "")[:60],
        )

    return recommendations, context
