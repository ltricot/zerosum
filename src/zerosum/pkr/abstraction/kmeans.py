from numba import njit
import numpy as np

from typing import Callable

from .hands import emd


Metric = Callable[[np.ndarray, np.ndarray], float]


def kmeanspp(vecs, k: int, metric: Metric = emd):
    centroids = []
    for _ in range(k):
        mi, md = 0, 0
        for i in np.random.choice(len(vecs), k, replace=False):
            if len(centroids) == 0:
                mi = i
                break

            ix = np.random.choice(len(centroids), min(len(centroids), 1000))
            d = min(metric(vecs[i], centroids[c]) for c in ix)
            if d > md:
                mi, md = i, d

        centroids.append(vecs[mi])
    return np.asarray(centroids)


# @njit
# can't njit because of metric argument, but this is fixable
def _pdist(vecs, centroids, metric):
    k, _ = centroids.shape
    n, _ = vecs.shape

    dists = np.empty((n, k))
    for i in range(n):
        for j in range(k):
            dists[i, j] = metric(centroids[j], vecs[i])

    return dists


def _labels(vecs, centroids, metric):
    dists = _pdist(vecs, centroids, metric)
    return np.argmin(dists, axis=1)


def kmeans(vecs, centroids, maxiter: int, metric: Metric = emd):
    k, _ = centroids.shape
    old = None

    for _ in range(maxiter):
        labels = _labels(vecs, centroids, metric)
        if old is not None and np.all(old == labels):
            break
        old = labels

        for j in range(k):
            members = vecs[labels == j]
            if len(members):
                centroids[j] = members.mean(axis=0)

    return centroids, _labels(vecs, centroids, metric)
