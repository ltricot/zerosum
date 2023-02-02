import numpy as np
from tqdm import tqdm

from zerosum.pkr.abstraction.hands import rhand
from zerosum.pkr.abstraction.ochs import ochs
from zerosum.pkr.abstraction.kmeans import kmeanspp, kmeans

import argparse
import pickle
import os


def l2(a, b):
    return np.linalg.norm(a - b)


def main():
    parser = argparse.ArgumentParser(
        "hands", description="opponent cluster hand strength"
    )
    parser.add_argument("--street", type=int, required=True)
    parser.add_argument("--clusters", type=int, required=True)
    parser.add_argument("--batch", type=int, required=True)
    args = parser.parse_args()

    centroids = cluster(args.street, args.clusters, args.batch)

    path = f"ochs/{args.street}-{args.clusters}.pkl"
    if os.path.exists(path):
        raise RuntimeError

    with open(path, "wb") as f:
        pickle.dump(centroids, f)


def cluster(street: int, clusters: int, batch: int):
    equities = {}

    for _ in tqdm(range(batch)):
        h = rhand(2 + street)
        equities[h] = ochs(h[:2], h[2:])

    vecs = np.vstack(list(equities.values()))
    centroids = kmeanspp(vecs, clusters, metric=l2)
    centroids, labels = kmeans(vecs, centroids, 1000, metric=l2)

    bad = 1
    while bad > 0:
        ncentroids = []
        bad = 0

        for label, centroid in enumerate(centroids):
            if np.sum(labels == label) > 10:
                ncentroids.append(centroid)
            else:
                bad += 1

        centroids = np.vstack(ncentroids)
        centroids, labels = kmeans(vecs, centroids, 1000, metric=l2)

    return centroids
