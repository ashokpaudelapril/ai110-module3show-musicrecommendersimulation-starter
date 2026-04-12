from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import csv


def _to_bool(value: Union[str, bool, int, float]) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _normalize_user_prefs(user_prefs: Union[Dict, "UserProfile"]) -> Dict:
    if isinstance(user_prefs, UserProfile):
        return {
            "genre": user_prefs.favorite_genre,
            "mood": user_prefs.favorite_mood,
            "energy": user_prefs.target_energy,
            "likes_acoustic": user_prefs.likes_acoustic,
        }
    return user_prefs


def _score_song_data(user_prefs: Dict, song: Dict, scoring_mode: str = "balanced") -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    genre_weight = 1.0
    mood_weight = 1.0
    energy_weight = 5.0

    if scoring_mode == "genre_first":
        genre_weight = 2.5
        mood_weight = 1.0
        energy_weight = 3.5
    elif scoring_mode == "mood_first":
        genre_weight = 1.0
        mood_weight = 2.5
        energy_weight = 3.5
    elif scoring_mode == "energy_focused":
        genre_weight = 0.5
        mood_weight = 0.5
        energy_weight = 6.5

    if song.get("genre") == user_prefs.get("genre"):
        score += genre_weight
        reasons.append(f"genre match (+{genre_weight:.1f})")

    if song.get("mood") == user_prefs.get("mood"):
        score += mood_weight
        reasons.append(f"mood match (+{mood_weight:.1f})")

    song_energy = float(song.get("energy", 0.0))
    target_energy = float(user_prefs.get("energy", 0.0))
    energy_score = energy_weight * (1 - abs(song_energy - target_energy))
    score += energy_score
    reasons.append(f"energy closeness (+{energy_score:.2f})")

    if "likes_acoustic" in user_prefs:
        likes_acoustic = _to_bool(user_prefs.get("likes_acoustic", False))
        acousticness = float(song.get("acousticness", 0.0))
        if not likes_acoustic and acousticness > 0.7:
            score -= 0.5
            reasons.append("high acousticness penalty (-0.50)")

    return score, reasons

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        scored_songs = sorted(
            self.songs,
            key=lambda song: _score_song_data(_normalize_user_prefs(user), song.__dict__)[0],
            reverse=True,
        )
        return scored_songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = _score_song_data(_normalize_user_prefs(user), song.__dict__)
        return ", ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if not row:
                continue
            song = {
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": int(float(row["tempo_bpm"])),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            }
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict, scoring_mode: str = "balanced") -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    return _score_song_data(user_prefs, song, scoring_mode=scoring_mode)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, scoring_mode: str = "balanced") -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    selected: List[Tuple[Dict, float, str]] = []
    used_artists: List[str] = []
    remaining_songs = [
        (song, *score_song(user_prefs, song, scoring_mode=scoring_mode))
        for song in songs
    ]

    while remaining_songs and len(selected) < k:
        best_index = 0
        best_score = float("-inf")
        best_song: Optional[Dict] = None
        best_reasons: List[str] = []

        for index, (song, score, reasons) in enumerate(remaining_songs):
            adjusted_score = score
            adjusted_reasons = list(reasons)

            if song["artist"] in used_artists:
                adjusted_score -= 0.75
                adjusted_reasons.append("artist diversity penalty (-0.75)")

            if adjusted_score > best_score:
                best_index = index
                best_score = adjusted_score
                best_song = song
                best_reasons = adjusted_reasons

        if best_song is None:
            break

        selected.append((best_song, best_score, ", ".join(best_reasons)))
        used_artists.append(best_song["artist"])
        remaining_songs.pop(best_index)

    return selected
