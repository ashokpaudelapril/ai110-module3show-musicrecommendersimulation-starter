from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs


def make_songs() -> list:
    return [
        Song(id=1, title="Test Pop Track", artist="Artist A", genre="pop",
             mood="happy", energy=0.8, tempo_bpm=120, valence=0.9,
             danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Artist A", genre="lofi",
             mood="chill", energy=0.4, tempo_bpm=80, valence=0.6,
             danceability=0.5, acousticness=0.9),
        Song(id=3, title="Rock Anthem", artist="Artist B", genre="rock",
             mood="intense", energy=0.9, tempo_bpm=150, valence=0.5,
             danceability=0.6, acousticness=0.1),
    ]


# ── Recommender class tests ───────────────────────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = Recommender(make_songs())
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = Recommender(make_songs())
    explanation = rec.explain_recommendation(user, rec.songs[0])

    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── score_song tests ──────────────────────────────────────────────────────────

def test_score_song_genre_match_adds_points():
    prefs = {"genre": "pop", "mood": "sad", "energy": 0.5, "likes_acoustic": False}
    song  = {"genre": "pop", "mood": "happy", "energy": 0.5, "acousticness": 0.1}
    score_with, _    = score_song(prefs, song)
    prefs_no_match   = {**prefs, "genre": "jazz"}
    score_without, _ = score_song(prefs_no_match, song)

    assert score_with > score_without


def test_score_song_acousticness_penalty_applied():
    prefs       = {"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": False}
    acoustic    = {"genre": "pop", "mood": "happy", "energy": 0.5, "acousticness": 0.9}
    not_acoustic = {"genre": "pop", "mood": "happy", "energy": 0.5, "acousticness": 0.1}

    score_acoustic, reasons_acoustic       = score_song(prefs, acoustic)
    score_not_acoustic, _                  = score_song(prefs, not_acoustic)

    assert score_acoustic < score_not_acoustic
    assert any("penalty" in r for r in reasons_acoustic)


def test_recommend_songs_applies_artist_diversity_penalty():
    # Artist A has two songs; the second should be penalised in favour of Artist B
    songs = [
        {"id": 1, "title": "A1", "artist": "Artist A", "genre": "pop",
         "mood": "happy", "energy": 0.8, "acousticness": 0.1},
        {"id": 2, "title": "A2", "artist": "Artist A", "genre": "pop",
         "mood": "happy", "energy": 0.79, "acousticness": 0.1},
        {"id": 3, "title": "B1", "artist": "Artist B", "genre": "pop",
         "mood": "happy", "energy": 0.75, "acousticness": 0.1},
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    results = recommend_songs(prefs, songs, k=3)

    artists = [song["artist"] for song, _, _ in results]
    # A1 wins rank 1 (best score). A2 gets the diversity penalty so B1 beats it to rank 2.
    # Expected order: [Artist A, Artist B, Artist A]
    assert artists[1] == "Artist B", f"Expected Artist B at rank 2, got {artists}"


def test_recommend_songs_returns_at_most_k():
    songs = [
        {"id": i, "title": f"Song {i}", "artist": "X", "genre": "pop",
         "mood": "happy", "energy": 0.5, "acousticness": 0.1}
        for i in range(10)
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": False}

    assert len(recommend_songs(prefs, songs, k=3)) == 3
    assert len(recommend_songs(prefs, songs, k=1)) == 1
