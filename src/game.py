from __future__ import annotations

from typing import Protocol, TypeVar, NewType, Hashable
from typing import Dict, Tuple


A_cov = TypeVar("A_cov", covariant=True)
A_inv = TypeVar("A_inv")


class InfoSet(Hashable, Protocol[A_cov]):
    def actions(self) -> Tuple[A_cov, ...]:
        ...


I = TypeVar("I", bound=InfoSet)
Player = NewType("Player", int)


class Game(Protocol[A_inv, I]):
    @property
    def terminal(self) -> bool:
        ...

    def payoff(self, player: Player) -> float:
        ...

    @property
    def chance(self) -> bool:
        ...

    def chances(self) -> Dict[A_inv, float]:
        ...

    @property
    def active(self) -> Player:
        ...

    def infoset(self, player: Player) -> I:
        ...

    def apply(self, action: A_inv) -> Game[A_inv, I]:
        ...
