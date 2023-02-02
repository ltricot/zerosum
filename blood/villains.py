import numpy as np
import eval7

from typing import cast
from functools import lru_cache
import pickle

from zerosum.game import InfoSet as PInfoSet
from zerosum.pkr.game import InfoSet
from zerosum.abstraction import algebraic
from zerosum.pkr.abstraction.ochs import ochs


Card = eval7.Card
_cards = eval7.Deck().cards


@lru_cache(maxsize=2 ** 10)
def _ochs(hand: tuple[Card, Card], community: tuple[Card, ...]):
    return ochs(hand, community)


def villain(street, centroids):
    @algebraic
    def villain(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)

        if len(infoset.community) != street:
            return -1

        hand = tuple(_cards[i] for i in infoset.hand)
        community = tuple(_cards[i] for i in infoset.community)
        h = _ochs(hand, community)

        return np.linalg.norm(centroids - h, axis=1).argmin()

    return villain


def villains(accs: tuple[int, ...]):
    abstractions = []

    for street, acc in zip((0, 3) + tuple(range(4, 15)), accs):
        if acc == 0:
            continue

        path = f"ochs/{street}-{acc}.pkl"
        with open(path, "rb") as f:
            centroids = pickle.load(f)

        a = villain(street, centroids)
        abstractions.append(a)

    a = abstractions.pop()
    while abstractions:
        a = a * abstractions.pop()

    return a
