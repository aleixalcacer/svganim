import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

theta = 0.8 * np.cos(np.linspace(0, 4 * np.pi, 80, endpoint=False))  # two swings

fig, ax = plt.subplots(figsize=(3, 3))
ax.set(xlim=(-1.2, 1.2), ylim=(-1.4, 0.2), aspect="equal")
ax.axis("off")
(rod,) = ax.plot([0, 0], [0, -1], "k", lw=2)
(bob,) = ax.plot([0], [-1], "o", ms=24, color="tab:red")


def update(i):
    x, y = np.sin(theta[i]), -np.cos(theta[i])
    rod.set_data([0, x], [0, y])
    bob.set_data([x], [y])


anim_to_svg(fig, update, len(theta), fps=30, hold=0, path="pendulum.svg")
