from numba import njit
import numpy.typing as npt
import numpy as np

from .hands import emd


def kmeanspp(vecs: npt.NDArray[np.float64], k: int):
    centroids = []
    for _ in range(k):
        mi, md = 0, 0
        for i in np.random.choice(len(vecs), k, replace=False):
            if len(centroids) == 0:
                mi = i
                break

            ix = np.random.choice(len(centroids), min(len(centroids), 10))
            d = min(emd(vecs[i], centroids[c]) for c in ix)
            if d > md:
                mi, md = i, d

        centroids.append(vecs[mi])
    return np.asarray(centroids)


@njit
def _pdist(vecs: npt.NDArray[np.float64], centroids: npt.NDArray[np.float64]):
    k, _ = centroids.shape
    n, _ = vecs.shape

    dists = np.empty((n, k))
    for i in range(n):
        for j in range(k):
            dists[i, j] = emd(centroids[j], vecs[i])

    return dists


def _labels(vecs: npt.NDArray[np.float64], centroids: npt.NDArray[np.float64]):
    dists = _pdist(vecs, centroids)
    return np.argmin(dists, axis=1)


def kmeans(
    vecs: npt.NDArray[np.float64], centroids: npt.NDArray[np.float64], maxiter: int
):
    k, d = centroids.shape

    for _ in range(maxiter):
        labels = _labels(vecs, centroids)
        for j in range(k):
            members = vecs[labels == j]
            if len(members):
                centroids[j] = members.mean(axis=0)

    return centroids, _labels(vecs, centroids)
