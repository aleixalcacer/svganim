import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

s = np.ones((900, 3))
for k in range(899):  # Lorenz system, Euler steps
    x, y, z = s[k]
    s[k + 1] = s[k] + 0.01 * np.array(
        [10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z]
    )

fig, ax = plt.subplots(figsize=(4, 4))
ax.set(xlim=(-22, 22), ylim=(0, 52))
ax.axis("off")
(line,) = ax.plot(s[:1, 0], s[:1, 2], lw=0.8, color="tab:purple")
(head,) = ax.plot(s[:1, 0], s[:1, 2], "o", color="tab:red")


def update(i):
    n = 25 * (i + 1)
    line.set_data(s[:n, 0], s[:n, 2])
    head.set_data(s[n - 1 : n, 0], s[n - 1 : n, 2])


anim_to_svg(fig, update, 36, fps=15, precision=1, path="lorenz.svg")
