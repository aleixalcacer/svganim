import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

fig, ax = plt.subplots(figsize=(5, 3))
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))
ax.set_ylim(-1.2, 1.2)
sc = ax.scatter([1, 2], [0, 0], c=["r", "b"], zorder=3)


def update(i):
    line.set_ydata(np.sin(x + i / 10))
    sc.set_offsets([[1 + i / 20, 0.5], [2, -0.5 + i / 60]])


anim_to_svg(
    fig,
    update,
    n_frames=60,
    fps=20,
    hold=1.0,
    path=Path(__file__).with_name("wave.svg"),
)
