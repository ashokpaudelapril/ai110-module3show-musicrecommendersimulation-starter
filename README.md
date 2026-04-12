# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This project builds a simple content-based music recommender. It compares each song to a user's preferences, such as favorite genre, mood, and target energy, and gives each song a score. Songs with higher scores are shown first. This simulates a small part of what real systems do at large scale.

---

## How The System Works

Real recommendation systems usually combine two ideas: collaborative filtering, which learns from patterns across many users such as likes, skips, playlists, and watch or listening time, and content-based filtering, which uses item attributes such as genre, mood, tempo, or energy. This simulator focuses on content-based filtering, so it recommends songs by comparing each song's attributes to one user's stated preferences. My version prioritizes genre, mood, and especially energy closeness, with a small acousticness penalty to avoid highly acoustic songs for users who do not want them.

### Data Plan

The catalog now has 15 songs with genre, mood, energy, tempo, valence, danceability, and acousticness. I expanded it with additional genres and moods such as reggaeton, electronic, folk, dream pop, and hip hop so the recommender has more variety to compare.

Prompt for Copilot Chat:

> Generate 5-10 additional songs in valid CSV format using the same headers as `songs.csv`. Keep the songs realistic and diverse.

### User Profile

The initial taste profile is:

```python
user_profile = {
  "favorite_genre": "rock",
  "favorite_mood": "intense",
  "target_energy": 0.88,
  "likes_acoustic": False,
}
```

This should help the system separate intense rock from chill lofi.

### Algorithm Recipe

- Add points for a genre match.
- Add points for a mood match.
- Add a larger energy score based on how close the song's energy is to the user's target energy.
- Apply a small penalty when a user does not like acoustic songs and the song's acousticness is very high.
- Rank the full song list from highest score to lowest score.

The scoring rule is for one song, and the ranking rule sorts all songs by score so the top matches come first. In the current implementation, the exact weights can shift by scoring mode, but the main idea stays the same: energy similarity matters most, while genre and mood help define the vibe.

### Flow

```mermaid
flowchart LR
  A[User Prefs] --> B[Score Each Song]
  C[CSV Catalog] --> B
  B --> D[Rank Songs]
  D --> E[Top K Recommendations]
```

### Bias Notes

This system may over-favor genre if the dataset is small or uneven. It can also miss good songs that match mood and energy but not genre.
It may also under-recommend newer genres if there are still only one or two examples of them in the catalog.

### Features Used In This Simulation

`Song` object fields stored:
- `id`, `title`, `artist`
- `genre`, `mood`
- `energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`

`UserProfile` object fields stored:
- `favorite_genre`
- `favorite_mood`
- `target_energy`
- `likes_acoustic`

Features currently used for scoring:
- `genre`
- `mood`
- `energy`
- `acousticness`

The basic idea is to score one song at a time, then rank all songs from best match to worst match.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
  ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

Sample CLI output:

```text
Loaded songs: 15
Sunrise City | Score: 5.45
Gym Hero | Score: 4.17
Rooftop Lights | Score: 3.40
```

Evaluation notes:

- High-Energy Pop: Sunrise City stayed near the top.
- Chill Lofi: Midnight Coding and Library Rain ranked highest.
- Deep Intense Rock: Storm Runner ranked first.

Screenshots included for submission:

- High-Energy Pop recommendations:

  ![High-Energy Pop recommendations](images/Screenshot%202026-04-12%20at%205.41.53%E2%80%AFPM.png)

- Chill Lofi recommendations:

  ![Chill Lofi recommendations](images/Screenshot%202026-04-12%20at%205.42.10%E2%80%AFPM.png)

- Deep Intense Rock recommendations:

  ![Deep Intense Rock recommendations](images/Screenshot%202026-04-12%20at%205.42.28%E2%80%AFPM.png)

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over-favor genre
- It could miss songs that match the mood but not the genre
- It may reflect the taste of the person who made the data

This system can also favor songs that look similar to the starter catalog, even after expansion.

You will go deeper on this in your model card.

---

## Reflection

[**Model Card**](model_card.md)

The model card explains the final system in more detail, including the data, strengths, limitations, and bias notes.


## 7. Evaluation

I checked the system by running multiple user profiles and comparing the rankings to the vibe each profile was supposed to represent. High-Energy Pop, Chill Lofi, and Deep Intense Rock each produced different top results, which showed that the scoring logic was responding to genre, mood, and energy as expected. I also ran the starter tests and verified that the CLI printed readable recommendation tables.

---

## 8. Future Work

If I had more time, I would expand the catalog, balance the genres and moods more evenly, and add more song features so the ranking has richer information to use. I would also improve diversity so the same songs or artists do not appear too often across different profiles.

---

## 9. Personal Reflection

What surprised me most was how much the ranking changed when I changed the scoring weights, even on a small catalog. A small rule change could move a song from the top to the middle of the list.

Building this made me think of real music recommenders as systems that make tradeoffs, not perfect predictors. They can match mood and genre well, but they still depend on limited data and simple assumptions.

Human judgment still matters when deciding what songs should count as a good recommendation, whether the results feel fair, and whether the system is repeating the same patterns too often. A model can look smart, but people still need to check if the output actually makes sense.
