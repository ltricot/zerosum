from typing import Protocol, TypeVar
from typing import Tuple

from .hands import Card


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
