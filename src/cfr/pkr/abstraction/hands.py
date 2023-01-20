from numba import njit
import numpy as np
import eval7

from typing import Iterator, Tuple
import itertools
import random


Card = eval7.Card
Hand = tuple[Card, ...]


def hands(k=2) -> Iterator[Tuple[Card, ...]]:
    return itertools.combinations(eval7.Deck().cards, k)


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
    cards = [
        card
        for card in eval7.Deck().cards
        if card not in hand and card not in community
    ]

    dist = []
    for _ in range(maxiter):
        _, completion = _draw(community, cards)
        strength = hs(hand, completion, 30)
        dist.append(strength)

    hist, _ = np.histogram(dist, bins=d, range=(0, 1))
    return hist / hist.sum()


@njit
def emd(h1: list[float], h2: list[float]) -> float:
    d = 0

    carry = 0
    for v1, v2 in zip(h1, h2):
        d += abs(carry)
        carry = v1 + carry - v2

    return d
