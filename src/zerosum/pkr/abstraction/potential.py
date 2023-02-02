from numba import njit
import numpy as np

from ..game import RiverOfBlood, Check, Call


def atstreet(street: int, strategy):
    g = RiverOfBlood()

    while g._street < street:
        if g.terminal:
            return atstreet(street, strategy)

        if g.chance:
            g = g.apply(g.sample())
            continue

        iset = g.infoset(g.active)
        if iset not in strategy:
            action = Check() if Check() in iset.actions() else Call()
        else:
            s = strategy[iset]
            action = max(s, key=s.__getitem__)

        g = g.apply(action)

    return g


def onestreet(g, strategy):
    street = g._street + 1

    while g._street < street and not g.terminal:
        if g.chance:
            g = g.apply(g.sample())
            continue

        iset = g.infoset(g.active)
        if iset not in strategy:
            action = Check() if Check() in iset.actions() else Call()
        else:
            s = strategy[iset]
            action = max(s, key=s.__getitem__)

        g = g.apply(action)

    return g


def potential(g, strategy, pot, d, maxiter):
    root = g

    pots = []
    while maxiter > 0:
        g = onestreet(root, strategy)
        if g.terminal:
            continue

        pots.append(pot(g.infoset(g.active)))
        maxiter -= 1

    h, _ = np.histogram(pots, bins=d, range=(0, d))
    return h / h.sum()


@njit
def emd2(sorteddists, dists, p1, p2):
    p2 = list(p2)

    cost = 0
    for i, v in enumerate(p1):
        for j in sorteddists[i]:
            if p2[j] > 0:
                moved = min(p2[j], v)
                v -= moved
                p2[j] -= moved
                cost += moved * dists[i, j]

            if v == 0:
                continue

    return cost
