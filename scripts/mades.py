import numpy as np
from tqdm import tqdm

from zerosum.pkr.abstraction.hands import made, rhand
from zerosum.pkr.abstraction.kmeans import kmeanspp, kmeans

import argparse
import pickle
import sys, os


def main():
    parser = argparse.ArgumentParser(
        "hands", description="cluster hands to create potentials"
    )
    parser.add_argument("--street", type=int, required=True)
    parser.add_argument("--clusters", type=int, required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("-f", "--future", type=int, default=1)
    args = parser.parse_args()

    centroids = cluster(args.street, args.clusters, args.batch, future=args.future)
    with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as stdout:
        pickle.dump(centroids, stdout)


def cluster(street: int, clusters: int, batch: int, future: int):
    equities = {}

    for _ in tqdm(range(batch)):
        h = rhand(2 + street)
        equities[h] = made(h[:2], h[2:], 10, 100, future=future)

    vecs = np.vstack(list(equities.values()))
    centroids = kmeanspp(vecs, clusters)
    centroids, labels = kmeans(vecs, centroids, 1000)

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
        centroids, labels = kmeans(vecs, centroids, 1000)

    return centroids
