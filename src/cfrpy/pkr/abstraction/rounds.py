from typing import Protocol, TypeVar
from typing import Tuple
from functools import lru_cache

from .hands import Card, hs


I = TypeVar("I", covariant=True)


class Mapper(Protocol[I]):
    def __call__(self, hand: Tuple[Card, Card], community: tuple[Card, ...]) -> I:
        ...


def preflop(hand: Tuple[Card, Card], community: tuple[Card, ...]):
    if community:
        raise ValueError

    a, b = hand
    suited = a.suit == b.suit
    ranks = tuple(sorted((a.rank, b.rank)))

    return (suited, *ranks)


def naive(hand: Tuple[Card, Card], community: tuple[Card, ...]):
    return preflop(hand, ())


@lru_cache
def ehs(hand: Tuple[Card, Card], community: tuple[Card, ...]):
    s = hs(hand, community, 30)
    return round(100 * s) // 10
