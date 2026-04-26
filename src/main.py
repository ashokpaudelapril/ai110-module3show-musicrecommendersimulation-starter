"""CLI runner for the Music Recommender.

Usage:
  python -m src.main                    # run preset experiments
  python -m src.main --ai "DESCRIPTION" # AI-powered natural language mode
"""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.recommender import load_songs, recommend_songs

load_dotenv()

_LOG_FILE = Path(__file__).parent.parent / "recommender.log"
_DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def print_recommendations(label: str, recommendations) -> None:
    title_width = max([len(song["title"]) for song, _, _ in recommendations] + [5])
    score_width = 7
    border = f"+{'-' * 4}+{'-' * (title_width + 2)}+{'-' * (score_width + 2)}+{'-' * 40}+"

    print(f"\n{label}")
    print(border)
    print(f"| {'Rank':<2} | {'Title':<{title_width}} | {'Score':<{score_width}} | Reasons")
    print(border)
    for index, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"| {index:<2} | {song['title']:<{title_width}} | {score:<{score_width}.2f} | {explanation}")
    print(border)


def run_ai_mode(description: str, k: int = 5) -> None:
    """Run recommendations using Gemini to parse a natural language description."""
    try:
        from src.ai_assistant import explain_recommendations, parse_user_intent
    except ImportError:
        logger.error("google-genai package not installed — run: pip install google-genai")
        print("Error: run `pip install google-genai` first.")
        return

    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY not set in environment or .env file")
        print("Error: set GEMINI_API_KEY in your .env file or environment.")
        return
    songs = load_songs(str(_DATA_PATH))
    logger.info("Loaded %d songs from catalog", len(songs))

    print(f"\nParsing: \"{description}\"")
    try:
        prefs = parse_user_intent(description)
    except ValueError as exc:
        logger.warning("Could not parse intent: %s", exc)
        print(f"Could not understand request: {exc}")
        return

    print(
        f"Preferences: genre={prefs['genre']}, mood={prefs['mood']}, "
        f"energy={prefs['energy']:.2f}, likes_acoustic={prefs['likes_acoustic']}"
    )

    recommendations = recommend_songs(prefs, songs, k=k)
    logger.info("Generated %d recommendations", len(recommendations))
    print_recommendations(f"AI Recommendations for: \"{description}\"", recommendations)

    explanation = explain_recommendations(description, prefs, recommendations)
    print(f"\nAI Explanation:\n{explanation}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender CLI")
    parser.add_argument(
        "--ai",
        metavar="DESCRIPTION",
        help="Describe what you want in natural language (uses Gemini)",
    )
    parser.add_argument("-k", type=int, default=5, help="Number of recommendations (default: 5)")
    args = parser.parse_args()

    if args.ai:
        run_ai_mode(args.ai, k=args.k)
        return

    songs = load_songs(str(_DATA_PATH))
    logger.info("Loaded %d songs from catalog", len(songs))
    print(f"Loaded songs: {len(songs)}")

    experiments = [
        ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.85}, "balanced"),
        ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.40}, "mood_first"),
        ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.92}, "genre_first"),
    ]

    for label, user_prefs, scoring_mode in experiments:
        recommendations = recommend_songs(user_prefs, songs, k=5, scoring_mode=scoring_mode)
        logger.info("Experiment '%s': %d recommendations", label, len(recommendations))
        print_recommendations(f"Top recommendations for {label} ({scoring_mode}):", recommendations)


if __name__ == "__main__":
    main()
