"""Streamlit UI for the AI-powered Music Recommender."""

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ai_assistant import explain_recommendations, parse_user_intent
from agent import RecommendationAgent
from retriever import retrieve
from recommender import load_songs, recommend_songs

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
    num_recs = st.slider("Number of recommendations", 1, 10, 5)
    scoring_mode = st.selectbox(
        "Scoring mode",
        ["balanced", "genre_first", "mood_first", "energy_focused"],
        help="How to weight genre, mood, and energy when scoring songs",
    )
    st.divider()
    agent_mode = st.checkbox(
        "Agent Mode",
        help=(
            "Uses a multi-step pipeline: plan → parse → retrieve → evaluate → [refine] → explain. "
            "Shows each reasoning step. Uses 3–4 extra API calls."
        ),
    )
    st.divider()
    st.caption("Logs are written to `recommender.log` in the project root.")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("🎵 AI Music Recommender")
st.caption("Describe what you're in the mood for — Claude will find the perfect tracks.")

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
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not found. Add it to your .env file.")
        st.stop()
    logger.info("New request (agent=%s): '%.120s'", agent_mode, user_description)

    try:
        songs = load_songs(str(_DATA_PATH))

        # ── Agent Mode ─────────────────────────────────────────────────────────
        if agent_mode:
            with st.spinner("Running multi-step agent..."):
                agent = RecommendationAgent()
                recommendations, explanation, steps = agent.run(
                    user_description, songs, k=num_recs, scoring_mode=scoring_mode
                )

            st.subheader("Agent Reasoning Steps")
            step_icons = {
                "plan":     "🗺️ Plan",
                "parse":    "🔍 Parse",
                "retrieve": "📂 Retrieve",
                "evaluate": "✅ Evaluate",
                "refine":   "🔄 Refine",
                "explain":  "💬 Explain",
            }
            for step in steps:
                label = step_icons.get(step.name, step.name.title())
                with st.expander(label, expanded=(step.name in ("plan", "evaluate"))):
                    st.write(step.summary())

            # Pull prefs from the parse step for metrics display
            parse_step = next((s for s in steps if s.name == "parse"), None)
            prefs = parse_step.output if parse_step else {}

        # ── Standard Mode ──────────────────────────────────────────────────────
        else:
            with st.spinner("Understanding your music taste..."):
                prefs = parse_user_intent(user_description)

            with st.spinner("Finding and explaining songs..."):
                recommendations, context = retrieve(prefs, songs, k=num_recs, scoring_mode=scoring_mode)
                explanation = explain_recommendations(user_description, prefs, recommendations, context=context)

        logger.info("Produced %d recommendations (mode=%s)", len(recommendations), scoring_mode)

        # ── Shared display ─────────────────────────────────────────────────────
        if prefs:
            st.subheader("Interpreted Preferences")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Genre", prefs.get("genre", "—").title())
            c2.metric("Mood",  prefs.get("mood",  "—").title())
            c3.metric("Energy", f"{prefs.get('energy', 0):.0%}")
            c4.metric("Acoustic", "Yes" if prefs.get("likes_acoustic") else "No")
            confidence = prefs.get("confidence", 0.5)
            c5.metric("AI Confidence", f"{confidence:.0%}")
            if confidence < 0.5:
                st.warning("Low confidence — Claude wasn't sure how to map your request. Try being more specific.")

        st.info(f"**Why these songs?** {explanation}")

        st.subheader(f"Top {len(recommendations)} Songs")
        for rank, (song, score, reasons) in enumerate(recommendations, 1):
            with st.expander(f"{rank}. **{song['title']}** — {song['artist']}  ·  score: {score:.2f}"):
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
