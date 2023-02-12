from __future__ import annotations

import numpy as np

from typing import Protocol, TypeVar, NewType, Hashable
from typing import Any, ClassVar


A_cov = TypeVar("A_cov", covariant=True)
A_inv = TypeVar("A_inv")


class InfoSet(Hashable, Protocol[A_cov]):
    def actions(self) -> tuple[A_cov, ...]:
        ...


I = TypeVar("I", bound=InfoSet)
Player = NewType("Player", int)

_T = TypeVar("_T", bound="Game")


class Game(Protocol[A_inv, I]):
    players: ClassVar[int]

    @classmethod
    def default(cls: type[_T]) -> _T:
        ...

    @property
    def terminal(self) -> bool:
        ...

    def payoff(self, player: Player) -> float:
        ...

    @property
    def chance(self) -> bool:
        ...

    def chances(self) -> dict[A_inv, float]:
        ...

    # chance sampling
    def sample(self) -> A_inv:
        ...

    @property
    def active(self) -> Player:
        ...

    def infoset(self, player: Player) -> I:
        ...

    def apply(self, action: A_inv) -> Game[A_inv, I]:
        ...


def mc(game: Game):
    while not game.terminal:
        if game.chance:
            action = game.sample()
        else:
            infoset = game.infoset(game.active)
            actions = infoset.actions()
            action = np.random.choice(actions)

        yield action
        game = game.apply(action)


def normalize(dct: dict[Any, float]):
    denom = sum(dct.values())
    if denom <= 0:
        return {k: 1 / len(dct) for k in dct}
    return {k: v / denom for k, v in dct.items()}


def play(game: Game[A_inv, I], strategies: dict[I, dict[A_inv, float]]):
    while not game.terminal:
        if game.chance:
            action = game.sample()
        else:
            infoset = game.infoset(game.active)
            actions = infoset.actions()

            if infoset in strategies:
                p = np.asarray(list(normalize(strategies[infoset]).values()))
                action = np.random.choice(actions, p=p)
            else:
                actions = infoset.actions()
                action = np.random.choice(actions)

        yield action
        game = game.apply(action)
