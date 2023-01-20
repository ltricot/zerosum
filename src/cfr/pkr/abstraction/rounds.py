from typing import Protocol, TypeVar
from typing import Tuple

from .hands import Card


I = TypeVar("I", covariant=True)


class Mapper(Protocol[I]):
    def map(self, hand: Tuple[Card, Card], community: tuple[Card, ...]) -> I:
        ...


class PreFlop:
    def map(self, hand: Tuple[Card, Card], community: tuple[Card, ...]):
        if community:
            raise ValueError

        a, b = hand
        suited = a.suit == b.suit
        ranks = tuple(sorted((a.rank, b.rank)))

        return (suited, *ranks)
