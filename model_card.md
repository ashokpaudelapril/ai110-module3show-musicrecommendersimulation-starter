# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**  

---

## 2. Intended Use  

Goal / Task: This recommender suggests a few songs from a small catalog based on genre, mood, and energy.

Intended use: It is for classroom exploration.

Non-intended use: It should not be used for real music recommendations.

---

## 3. Algorithm Summary  

The model compares each song to a user profile and gives points for matching genre, matching mood, and being close in energy. It can also subtract a small amount when a user does not want very acoustic songs. After that, it ranks all songs from highest score to lowest score. In one experiment, energy mattered more than genre, which changed the rankings.

---

## 4. Data Used  

The catalog has 15 songs. Each song has a title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness. It includes pop, lofi, rock, ambient, jazz, synthwave, indie pop, reggaeton, electronic, folk, dream pop, and hip hop. It is still a small dataset and does not cover every style equally.

---

## 5. Strengths  

The system works well when the user wants a clear vibe, like happy pop, chill lofi, or intense rock. It does a good job of putting songs with similar energy near the top.

---

## 6. Observed Behavior and Biases

The model can over-favor songs that match energy, even when the genre is not a perfect fit. In my tests, songs like Gym Hero and Golden Hour Ride stayed near the top for multiple profiles because their energy values were close to the target, even when the mood or genre was only a partial match. This creates a small filter bubble around energetic songs and makes the recommender less flexible for users with mixed preferences. The catalog is also still small and uneven, so some genres have fewer chances to appear in the top results. A larger and more balanced catalog, plus better weight tuning, would reduce that bias.

---

## 7. Evaluation Process

Three profiles were tested: High-Energy Pop, Chill Lofi, and Deep Intense Rock. The results mostly matched the expected vibe for each profile: Sunrise City ranked first for High-Energy Pop, Midnight Coding ranked first for Chill Lofi, and Storm Runner ranked first for Deep Intense Rock. That made sense because each of those songs matched the target vibe on more than one feature instead of relying on only one lucky score.

I also ran a small scoring experiment by switching some profiles to the `energy_focused` mode. That change made the top rankings more dependent on energy closeness, and songs like Golden Hour Ride and Static Hearts stayed high even without matching the target genre. This showed that the recommender was sensitive to weight changes and that stronger energy weighting made the output more consistent numerically, but not always more accurate to human intuition.

---

## 8. Future Work  

More songs could be added, the weights could be rebalanced, and a simple diversity rule could keep the top results from becoming too similar. The explanation text could also stay short but clearer. A better next step would be to test the system with a larger and more balanced catalog.

---

## 9. Personal Reflection  

My biggest learning moment was seeing how much a small weight change could reorder the whole list. That showed me that recommenders are really about tradeoffs, not magic. AI tools helped me brainstorm prompts, dataset ideas, and explanations faster, but I still had to double-check the code, the weights, and whether the written description matched the real output. What surprised me most was that a simple scoring system could still feel believable when the data lined up with the user's vibe. If I kept going, I would add more songs, test more edge-case users, and improve diversity so the same songs do not appear so often.
