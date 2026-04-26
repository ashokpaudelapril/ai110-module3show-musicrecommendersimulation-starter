# Model Card: AI Music Recommender

**Project name:** VibeFinder — AI Music Recommender
**Base project:** Music Recommender Simulation (CodePath Applied AI, Modules 1–3)
**Last updated:** April 2026

---

## 1. What This System Does

VibeFinder lets you describe what music you want in plain English and returns ranked song recommendations with a personalized explanation. It combines a content-based scoring engine (pure Python) with a Google Gemini AI layer that handles language understanding and explanation generation.

**RAG pipeline:**
1. Gemini parses your natural language description into structured preferences
2. The scoring engine retrieves matching songs from a 15-song catalog
3. Gemini explains why the songs fit, using a knowledge base of genre and mood descriptions

An optional **Agent Mode** adds a planning, evaluation, and refinement loop on top of this pipeline.

---

## 2. Base Model

- **AI model:** Google Gemini 2.0 Flash via the `google-genai` SDK
- **Specialization method:** Few-shot prompting — 5 curated examples guide Gemini toward more accurate genre/mood mappings for ambiguous inputs (e.g. "deep work music" → lofi, not ambient)
- **No fine-tuning** was performed; specialization is achieved through prompt engineering

---

## 3. Data

| Source | Description |
|--------|-------------|
| `data/songs.csv` | 15 handcrafted songs with genre, mood, energy, tempo, valence, danceability, acousticness |
| `data/genre_knowledge.json` | Descriptions, energy ranges, and use cases for 12 genres |
| `data/mood_knowledge.json` | Descriptions, energy hints, and avoidance notes for 11 moods |

The song catalog is intentionally small and manually curated. It covers 12 genres but some (folk, dream pop, reggaeton) have only one representative song each, which limits diversity in recommendations for those styles.

---

## 4. Intended Use

- **Intended:** Learning project demonstrating RAG, agentic workflows, and LLM integration in a Python application
- **Not intended for:** Real music discovery at scale, commercial use, or deployment without a larger catalog

---

## 5. Strengths

- Works well for clear, high-contrast requests ("intense gym music", "chill study beats")
- The confidence score flags when Gemini is uncertain, prompting the user to rephrase
- Agent Mode makes the reasoning process visible and correctable
- The pipeline is modular — the scoring engine works independently of the AI layer and has full unit test coverage

---

## 6. Limitations and Biases

**Catalog size:** 15 songs is too small for a real recommender. Several genres have only one song, so unusual requests in those genres always return the same track.

**Energy dominance:** The scoring engine weights energy closeness heavily. Songs with the right energy but wrong genre often outrank better genre matches with slightly off energy. This creates a weak filter bubble around energetic tracks.

**Gemini mapping quality:** When a user's description is vague or uses vocabulary outside the training data (e.g. "sigma playlist"), Gemini may map to a genre that technically fits the words but not the intent. The confidence score is the main guardrail here.

**Catalog bias:** The catalog was built by one person, so it reflects one perspective on what "lofi" or "jazz" sounds like. A more diverse catalog would produce fairer recommendations across different cultural backgrounds and tastes.

---

## 7. Testing and Evaluation

### Unit tests (`pytest`)

6 tests covering the scoring engine — no API calls needed:

| Test | Result |
|------|--------|
| Songs sorted by score | PASS |
| Explanation returns non-empty string | PASS |
| Genre match adds points | PASS |
| Acousticness penalty fires correctly | PASS |
| Artist diversity penalty reorders results | PASS |
| Result count never exceeds k | PASS |

**6/6 passed**

### AI evaluation script (mock mode)

`python tests/eval_ai.py --mock` — 6 end-to-end test cases with predefined responses, no API calls:

```
Results: 6 passed, 0 failed
Average confidence score: 0.87
```

All 6 cases (study/lofi, gym, jazz cafe, night drive, happy pop, acoustic/warm) retrieved the expected top song and passed all field checks.

### Few-shot vs baseline comparison

`python tests/eval_ai.py --compare` — measures the effect of few-shot specialization on 5 ambiguous inputs:

| Test Case | Baseline | Few-Shot | Improvement |
|-----------|----------|----------|-------------|
| Crying songs | 0.58 | 0.82 | +0.24 |
| Deep work | 0.65 | 0.91 | +0.26 |
| Pre-game hype | 0.70 | 0.90 | +0.20 |
| Night drive | 0.63 | 0.88 | +0.25 |
| Lazy Sunday | 0.62 | 0.86 | +0.24 |
| **Average** | **0.64** | **0.87** | **+0.24** |

Few-shot prompting improved average confidence by 0.24 and produced more accurate genre mappings in 4 of 5 cases.

---

## 8. AI Collaboration Notes

AI tools (Claude Code) were used throughout this project for:
- Writing boilerplate code (data classes, CSV loading, logging setup)
- Designing the RAG pipeline and agent loop architecture
- Debugging the `google-genai` SDK migration from the deprecated `google-generativeai` package
- Drafting the README and model card structure

All AI-generated code was reviewed, tested, and adjusted. Key decisions — what the scoring weights should be, which test cases to include, what the few-shot examples should cover — were made by me based on what I observed the system getting wrong.

The most useful AI contribution was catching the markdown code fence issue in the JSON parser (Gemini wrapping responses in ` ```json ``` `), which would have taken much longer to debug manually.

---

## 9. Reflection

Building this project changed how I think about AI in software. The most important lesson was that AI is most useful at the fuzzy edges of a problem — understanding language, explaining results — while deterministic code handles the precise, testable parts. Keeping those two layers separate made everything easier to build, debug, and prove correct.

I also learned that confidence scores are more useful than they first appear. They don't just rate Gemini's certainty; they surface when the system boundary between "things Gemini understands" and "things the catalog supports" is being stretched. A low confidence score is a meaningful signal, not just a number.

The few-shot experiments surprised me. I expected the examples to help a little. They helped a lot — not just by raising confidence, but by shifting the genre mapping in a meaningful direction on every ambiguous case I tested. That made the difference between a system that sometimes gets lucky and one that behaves predictably.

---

## 10. What This Project Says About Me as an AI Engineer

I approach AI features the way I approach any engineering problem: start with what can be measured, build the simplest thing that could work, and make it testable before making it smart. This project has unit tests for the scoring engine, a mock eval harness that runs without API quota, a confidence signal visible to the user, and an agent loop that shows its reasoning rather than hiding it.

I'm also comfortable sitting at the boundary between AI and traditional software. Not every problem needs a model. The scoring engine in this project is pure Python — fast, predictable, and fully tested. Gemini handles the parts that pure Python can't: language understanding and natural explanation. Knowing which layer to use for which job is the skill I'm most proud of developing here.
