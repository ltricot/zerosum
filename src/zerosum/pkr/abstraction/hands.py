from numba import njit
import numpy.typing as npt
import numpy as np
import eval7

from typing import Iterator
import warnings
import itertools
import random


Card = eval7.Card
Hand = tuple[Card, ...]


ACCURACY = 100


def hands(k: int = 2) -> Iterator[tuple[Card, ...]]:
    return itertools.combinations(eval7.Deck().cards, k)


def rhand(k: int):
    return tuple(random.sample(eval7.Deck().cards, k))


def _draw(community: tuple[Card, ...], cards: list[Card]):
    i = 0  # typing

    for i in range(len(cards)):
        j = random.randint(1 + i, len(cards) - 1)
        cards[i], cards[j] = cards[j], cards[i]

        if (i >= 1 and len(community) > 0) or i > 1:
            last = community[-1] if i == 1 else cards[i]
            if len(community) + i - 1 >= 5 and last.suit not in (1, 2):
                break

    return tuple(cards[:2]), community + tuple(cards[2 : i + 1])


def hs(hand: tuple[Card, Card], community: tuple[Card, ...], maxiter: int):
    warnings.warn(
        "hand strength is implemented with Cython in the eval7 fork, "
        "this version is python and much slower",
        category=DeprecationWarning,
    )

    cards = [
        card
        for card in eval7.Deck().cards
        if card not in hand and card not in community
    ]

    sco = 0
    for _ in range(maxiter):
        other, completion = _draw(community, cards)
        us = eval7.evaluate(hand + completion)
        op = eval7.evaluate(other + completion)
        sco += 2 if us > op else 1 if us == op else 0

    return sco / (2 * maxiter)


def equity(hand: tuple[Card, Card], community: tuple[Card, ...], d: int, maxiter: int):
    if maxiter < 20:
        warnings.warn(f"low monte carlo accuracy: {maxiter}")

    s = eval7.hequity(hand, community, maxiter, ACCURACY)
    h, _ = np.histogram(s, bins=d, range=(0, 1))
    return h / h.sum()


def potential(
    hand: tuple[Card, Card],
    community: tuple[Card, ...],
    d: int,
    maxiter: int,
    future: int,
):
    if maxiter < 20:
        warnings.warn(f"low monte carlo accuracy: {maxiter}")

    cards = [
        card
        for card in eval7.Deck().cards
        if card not in hand and card not in community
    ]

    dist = []
    for _ in range(maxiter):
        additional = tuple(random.sample(cards, k=future))
        strength = eval7.strength(hand, community + additional, ACCURACY)
        dist.append(strength)

    hist, _ = np.histogram(dist, bins=np.linspace(0, 1, d + 1), range=(0, 1))
    return hist / hist.sum()


def made(
    hand: tuple[Card, Card],
    community: tuple[Card, ...],
    d: int,
    maxiter: int,
    future: int,
):
    if maxiter < 20:
        warnings.warn(f"low monte carlo accuracy: {maxiter}")

    cards = [
        card
        for card in eval7.Deck().cards
        if card not in hand and card not in community
    ]

    dist = []
    for _ in range(maxiter):
        additional = tuple(random.sample(cards, k=future))
        strength = eval7.made(hand, community + additional, 100)
        dist.append(strength)

    hist, _ = np.histogram(dist, bins=np.linspace(0, 1, d + 1), range=(0, 1))
    return hist / hist.sum()


@njit
def emd(h1: npt.NDArray[np.float64], h2: npt.NDArray[np.float64]) -> float:
    d = 0

    carry = 0
    for v1, v2 in zip(h1, h2):
        d += abs(carry)
        carry = v1 + carry - v2

    return d
