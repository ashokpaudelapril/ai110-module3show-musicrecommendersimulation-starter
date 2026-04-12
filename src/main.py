"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


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


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    experiments = [
        ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.85}, "balanced"),
        ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.40}, "mood_first"),
        ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.92}, "genre_first"),
    ]

    for label, user_prefs, scoring_mode in experiments:
        recommendations = recommend_songs(user_prefs, songs, k=5, scoring_mode=scoring_mode)
        print_recommendations(f"Top recommendations for {label} ({scoring_mode}):", recommendations)


if __name__ == "__main__":
    main()
