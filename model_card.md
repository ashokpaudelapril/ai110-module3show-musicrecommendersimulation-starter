# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**  

---

## 2. Intended Use  

This recommender suggests a few songs from a small catalog based on genre, mood, and energy. It is for classroom exploration, not real users.

---

## 3. How the Model Works  

The model compares each song to a user profile and gives points for matching genre, matching mood, and being close in energy. In the experiment version, energy mattered more than genre, which changed the rankings.

---

## 4. Data  

The catalog has 10 songs. It includes pop, lofi, rock, ambient, jazz, synthwave, and indie pop, but it is still a small dataset and does not cover every style equally.

---

## 5. Strengths  

The system works well when the user wants a clear vibe, like happy pop, chill lofi, or intense rock. It does a good job of putting songs with similar energy near the top.

---

## 6. Limitations and Bias 

The model can over-favor songs that match energy, even when the genre is not a perfect fit. It may also repeat the same songs for different users because the dataset is small. Since the catalog is not balanced, some genres and moods get more chances to appear near the top than others.

---

## 7. Evaluation  

Three profiles were tested: High-Energy Pop, Chill Lofi, and Deep Intense Rock. The results mostly made sense, but one surprise was that songs with very close energy could still outrank better genre matches after the energy weight was increased. That showed the scoring logic was sensitive to the weight settings.

---

## 8. Future Work  

More songs could be added, the weights could be rebalanced, and a simple diversity rule could keep the top results from becoming too similar. The explanation text could also stay short but clearer.

---

## 9. Personal Reflection  

I learned that recommender systems are mostly about tradeoffs. Small weight changes can make the output feel very different, which shows why real apps need testing and tuning.
