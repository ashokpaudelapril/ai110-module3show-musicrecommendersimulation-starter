"""Streamlit UI for the AI-powered Music Recommender."""

import logging
import os
from pathlib import Path

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

from src.ai_assistant import explain_recommendations, parse_user_intent
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

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Music Recommender", page_icon="🎵", layout="centered")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Get your key at aistudio.google.com",
    )
    num_recs = st.slider("Number of recommendations", 1, 10, 5)
    scoring_mode = st.selectbox(
        "Scoring mode",
        ["balanced", "genre_first", "mood_first", "energy_focused"],
        help="How to weight genre, mood, and energy when scoring songs",
    )
    st.divider()
    st.caption("Logs are written to `recommender.log` in the project root.")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("🎵 AI Music Recommender")
st.caption("Describe what you're in the mood for — Gemini will find the perfect tracks.")

user_description = st.text_area(
    "What kind of music are you looking for?",
    placeholder="e.g. 'Upbeat danceable songs for the gym' or 'Chill lo-fi beats to study to'",
    height=100,
)

get_recs = st.button(
    "Get Recommendations",
    type="primary",
    disabled=not user_description.strip(),
)

if get_recs:
    api_key = api_key_input.strip() or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar (or set GEMINI_API_KEY in .env).")
        st.stop()

    genai.configure(api_key=api_key)
    logger.info("New request — user description: '%.120s'", user_description)

    try:
        songs = load_songs(str(_DATA_PATH))
        logger.info("Loaded %d songs from catalog", len(songs))

        # Step 1: Gemini parses natural language into structured preferences (RAG query phase)
        with st.spinner("Understanding your music taste..."):
            prefs = parse_user_intent(user_description)

        st.subheader("Interpreted Preferences")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Genre", prefs["genre"].title())
        c2.metric("Mood", prefs["mood"].title())
        c3.metric("Energy", f"{prefs['energy']:.0%}")
        c4.metric("Acoustic", "Yes" if prefs["likes_acoustic"] else "No")

        # Step 2: Retrieve matching songs from the catalog
        recommendations = recommend_songs(prefs, songs, k=num_recs, scoring_mode=scoring_mode)
        logger.info("Produced %d recommendations (mode=%s)", len(recommendations), scoring_mode)

        # Step 3: Gemini explains why the retrieved songs fit the request (RAG generation phase)
        with st.spinner("Writing your personalized explanation..."):
            explanation = explain_recommendations(user_description, prefs, recommendations)

        st.info(f"**Why these songs?** {explanation}")

        st.subheader(f"Top {len(recommendations)} Songs")
        for rank, (song, score, reasons) in enumerate(recommendations, 1):
            with st.expander(
                f"{rank}. **{song['title']}** — {song['artist']}  ·  score: {score:.2f}"
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Genre:** {song['genre']}")
                    st.write(f"**Mood:** {song['mood']}")
                    st.write(f"**Energy:** {song['energy']:.0%}")
                with col_b:
                    st.write(f"**Tempo:** {song['tempo_bpm']} BPM")
                    st.write(f"**Danceability:** {song['danceability']:.0%}")
                    st.write(f"**Acousticness:** {song['acousticness']:.0%}")
                st.caption(f"Scoring: {reasons}")

    except ValueError as exc:
        logger.warning("Preference parsing failed: %s", exc)
        st.warning(f"Could not understand your request: {exc}. Try rephrasing.")
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        st.error(f"An unexpected error occurred: {exc}")
