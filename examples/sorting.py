import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

a = np.random.default_rng(3).permutation(16) + 1
frames = [a.copy()]
for end in range(len(a) - 1, 0, -1):  # bubble sort, one frame per swap
    for j in range(end):
        if a[j] > a[j + 1]:
            a[j], a[j + 1] = a[j + 1], a[j]
            frames.append(a.copy())

fig, ax = plt.subplots(figsize=(5, 2.5))
bars = ax.bar(range(16), frames[0])
ax.axis("off")


def update(i):
    for bar, h in zip(bars, frames[i], strict=True):
        bar.set_height(h)
        bar.set_color(plt.cm.viridis(h / 16))


anim_to_svg(fig, update, len(frames), fps=20, path="sorting.svg")
