import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

x, y = np.meshgrid(np.linspace(-3, 3, 90), np.linspace(-1.5, 1.5, 45))
p, steps = np.array([-2.8, 1.2]), []
for _ in range(40):  # f(x, y) = x^2 + 10 y^2
    steps.append(p)
    p = p - 0.09 * np.array([2 * p[0], 20 * p[1]])
steps = np.array(steps)

fig, ax = plt.subplots(figsize=(5, 3))
ax.contourf(x, y, x**2 + 10 * y**2, 12, cmap="Blues")
(trail,) = ax.plot(*steps[:1].T, "-", color="k", lw=1)
(dot,) = ax.plot(*steps[:1].T, "o", color="tab:red")


def update(i):
    trail.set_data(*steps[: i + 1].T)
    dot.set_data(*steps[i : i + 1].T)


anim_to_svg(fig, update, len(steps), fps=10, path="gradient_descent.svg")
