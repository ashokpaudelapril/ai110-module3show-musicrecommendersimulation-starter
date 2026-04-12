# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**  

---

## 2. Intended Use  

Goal / Task: This recommender suggests a few songs from a small catalog based on genre, mood, and energy.

Intended use: It is for classroom exploration.

Non-intended use: It should not be used for real music recommendations.

---

## 3. How the Model Works  

The model compares each song to a user profile and gives points for matching genre, matching mood, and being close in energy. In the experiment version, energy mattered more than genre, which changed the rankings.

---

## 4. Data  

The catalog has 10 songs. It includes pop, lofi, rock, ambient, jazz, synthwave, and indie pop. It is still a small dataset and does not cover every style equally.

---

## 5. Strengths  

The system works well when the user wants a clear vibe, like happy pop, chill lofi, or intense rock. It does a good job of putting songs with similar energy near the top.

---

## 6. Limitations and Bias 

The model can over-favor songs that match energy, even when the genre is not a perfect fit. It may also repeat the same songs for different users because the dataset is small. Since the catalog is not balanced, some genres and moods get more chances to appear near the top than others.

This means a user who just wants happy pop may still see Gym Hero often, because it matches the pop genre and the high-energy pattern. The system also has fewer choices for some moods, so the top results can feel a little repetitive. A larger and more balanced catalog would reduce that bias.

---

## 7. Evaluation  

Three profiles were tested: High-Energy Pop, Chill Lofi, and Deep Intense Rock. The results mostly matched the expected vibe for each profile. One surprise was that energy could push a song upward even when genre was not the strongest match, which showed that the weights have a big effect on the ranking.

The same songs also appeared near the top more than once, especially when they matched both genre and energy. That was useful because it showed how a small catalog can limit variety.

---

## 8. Future Work  

More songs could be added, the weights could be rebalanced, and a simple diversity rule could keep the top results from becoming too similar. The explanation text could also stay short but clearer. A better next step would be to test the system with a larger and more balanced catalog.

---

## 9. Personal Reflection  

I learned that recommender systems are mostly about tradeoffs. Small weight changes can make the output feel very different, which shows why real apps need testing and tuning. It was also interesting to see that simple rules can still feel convincing when the data lines up with the user's vibe.
