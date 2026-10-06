import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

rng = np.random.default_rng(0)
X = np.vstack([rng.normal(c, 0.8, (60, 2)) for c in ([0, 0], [4, 1], [1, 4])])
centers = X[rng.choice(len(X), 3, replace=False)]
states = []
for _ in range(20):  # Lloyd's algorithm, keeping every iteration until it converges
    labels = np.linalg.norm(X[:, None] - centers, axis=2).argmin(axis=1)
    states.append((labels, centers))
    new_centers = np.array([X[labels == j].mean(axis=0) for j in range(3)])
    if np.allclose(new_centers, centers):
        break
    centers = new_centers

colors = np.array(["#4c72b0", "#dd8452", "#55a868"])
fig, ax = plt.subplots(figsize=(5, 4))
points = ax.scatter(*X.T, c=colors[states[0][0]], s=14)
stars = ax.scatter(
    *states[0][1].T, c=colors, marker="X", s=160, edgecolors="black", zorder=3
)
ax.axis("off")


def update(i):
    labels, centers = states[i]
    points.set_facecolor(colors[labels])
    stars.set_offsets(centers)


anim_to_svg(fig, update, len(states), fps=1.5, interpolate=True, path="kmeans.svg")
