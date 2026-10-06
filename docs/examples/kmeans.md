# k-means

```{image} /_static/examples/kmeans.svg
:alt: k-means
:width: 440px
:align: center
```

Cluster assignments and centroids across the iterations of Lloyd's algorithm.
The algorithm runs first and its states are stored; `update` then replays them,
one frame per iteration, until the centroids stop moving.

## What changes in each frame

- `points.set_facecolor(colors[labels])` recolours the points by cluster.
- `stars.set_offsets(centers)` moves the three centroids.

## What svganim animates

The colour (`fill`, `stroke`) of the 51 points that change cluster at some
point, and the position of the centroids (`x`, `y`).

With `interpolate=True` the centroids slide to their next position and the
points fade to their new colour, instead of jumping from one state to the next.
Each iteration is a state, which is the case this option is meant for. See
[Smooth transitions](../usage.md#smooth-transitions).

4 frames at 1.5 fps, about 47 KiB. The loop stops when the algorithm converges: later iterations would be identical frames and only add dead time.

## Code

```{literalinclude} /../examples/kmeans.py
:language: python
```
