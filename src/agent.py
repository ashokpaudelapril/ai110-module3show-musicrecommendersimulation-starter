"""
Multi-step recommendation agent with observable intermediate steps.

Pipeline:
  1. plan     — Gemini identifies what musical qualities to prioritize
  2. parse    — Gemini converts the description into structured preferences (few-shot)
  3. retrieve — Enhanced RAG: songs + genre/mood knowledge base
  4. evaluate — Gemini scores how well the top results match the intent
  5. refine   — If match score < 0.6, Gemini adjusts preferences and retries (max 1x)
  6. explain  — Gemini writes a context-aware explanation using the knowledge base

Each step produces a visible AgentStep that the UI can display.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ai_assistant import (
    _MODEL,
    _SYSTEM_PROMPT,
    _get_client,
    _parse_prefs_json,
    explain_recommendations,
    parse_user_intent,
)
from retriever import retrieve

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    name: str
    output: object

    def summary(self) -> str:
        if self.name == "plan":
            return str(self.output)
        if self.name == "parse":
            p = self.output
            return (
                f"genre={p['genre']}, mood={p['mood']}, "
                f"energy={p['energy']:.2f}, confidence={p.get('confidence', 0):.2f}"
            )
        if self.name == "retrieve":
            o = self.output
            return (
                f"{o['songs_found']} songs found — "
                f"genre context: {'yes' if o['genre_context'] else 'no'}, "
                f"mood context: {'yes' if o['mood_context'] else 'no'}"
            )
        if self.name == "evaluate":
            ev = self.output
            return f"match score: {ev['score']:.2f} — {ev['feedback']}"
        if self.name == "refine":
            p = self.output
            return f"adjusted → genre={p['genre']}, mood={p['mood']}, energy={p['energy']:.2f}"
        if self.name == "explain":
            text = str(self.output)
            return text[:120] + ("..." if len(text) > 120 else "")
        return str(self.output)[:120]


class RecommendationAgent:
    """
    Runs the full multi-step recommendation pipeline.
    Returns (recommendations, explanation, steps) so the caller can display
    intermediate reasoning.
    """

    def run(
        self,
        description: str,
        songs: List[Dict],
        k: int = 5,
        scoring_mode: str = "balanced",
    ) -> Tuple[List[Tuple], str, List[AgentStep]]:
        steps: List[AgentStep] = []

        # ── Step 1: Plan ───────────────────────────────────────────────────────
        plan = self._plan(description)
        steps.append(AgentStep("plan", plan))
        logger.info("[Agent] Plan: %s", plan)

        # ── Step 2: Parse (few-shot specialization) ────────────────────────────
        prefs = parse_user_intent(description, few_shot=True)
        steps.append(AgentStep("parse", prefs))
        logger.info("[Agent] Parsed: %s", prefs)

        # ── Step 3: Retrieve (enhanced RAG: songs + knowledge base) ────────────
        recommendations, context = retrieve(prefs, songs, k=k, scoring_mode=scoring_mode)
        steps.append(AgentStep("retrieve", {
            "songs_found":    len(recommendations),
            "genre_context":  bool(context.get("genre")),
            "mood_context":   bool(context.get("mood")),
        }))
        logger.info("[Agent] Retrieved %d songs", len(recommendations))

        # ── Step 4: Evaluate ───────────────────────────────────────────────────
        evaluation = self._evaluate(description, prefs, recommendations)
        steps.append(AgentStep("evaluate", evaluation))
        logger.info("[Agent] Evaluation score=%.2f: %s", evaluation["score"], evaluation["feedback"])

        # ── Step 5: Refine if needed (max 1 retry) ─────────────────────────────
        if evaluation["score"] < 0.6:
            refined = self._refine(description, prefs, evaluation["feedback"])
            if refined != prefs:
                recommendations, context = retrieve(refined, songs, k=k, scoring_mode=scoring_mode)
                prefs = refined
                steps.append(AgentStep("refine", prefs))
                logger.info("[Agent] Refined preferences: %s", prefs)

        # ── Step 6: Explain (uses knowledge base context) ─────────────────────
        explanation = explain_recommendations(description, prefs, recommendations, context=context)
        steps.append(AgentStep("explain", explanation))

        return recommendations, explanation, steps

    # ── Private step implementations ──────────────────────────────────────────

    def _plan(self, description: str) -> str:
        """Claude describes what musical qualities to prioritize."""
        client = _get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=60,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": (
                f'User wants: "{description}"\n\n'
                "In one sentence, describe what musical characteristics "
                "(genre, energy level, mood, acoustic vs electronic) to prioritize."
            )}],
        )
        return response.content[0].text.strip()

    def _evaluate(
        self,
        description: str,
        prefs: Dict,
        recommendations: List[Tuple],
    ) -> Dict:
        """Gemini rates how well the top 3 songs match the user's original intent."""
        top3 = "\n".join(
            f"- {s['title']} by {s['artist']} (genre={s['genre']}, mood={s['mood']}, energy={s['energy']:.2f})"
            for s, _, _ in recommendations[:3]
        )
        client = _get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=100,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": (
                f'User asked for: "{description}"\n'
                f"Top retrieved songs:\n{top3}\n\n"
                "Rate how well these match the request.\n"
                'Reply with ONLY valid JSON: {"score": 0.0–1.0, "feedback": "one sentence"}\n'
                "score=1.0 means perfect match, score=0.0 means completely wrong."
            )}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            result = json.loads(raw)
            result["score"] = float(result.get("score", 0.7))
            return result
        except Exception:
            return {"score": 0.7, "feedback": "Evaluation inconclusive — proceeding with current results."}

    def _refine(self, description: str, prefs: Dict, feedback: str) -> Dict:
        """Adjusts preferences based on the evaluator's feedback."""
        client = _get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=100,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": (
                f'Original request: "{description}"\n'
                f"Current preferences: {json.dumps(prefs)}\n"
                f"Evaluator feedback: {feedback}\n\n"
                "Adjust the preferences to better match the request.\n"
                "Reply with ONLY valid JSON: "
                "genre, mood, energy (0.0–1.0), likes_acoustic (true/false), confidence (0.0–1.0)"
            )}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            return _parse_prefs_json(raw)
        except Exception:
            logger.warning("[Agent] Refine parse failed — keeping original preferences")
            return prefs
