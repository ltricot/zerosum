from __future__ import annotations

from typing import cast
from dataclasses import dataclass
import enum

from ..game import Player, Game


class Action(enum.IntEnum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2


@dataclass(slots=True, frozen=True)
class InfoSet:
    player: int

    def actions(self):
        return (Action.ROCK, Action.PAPER, Action.SCISSORS)


@dataclass(slots=True, frozen=True)
class RPS:
    history: tuple[Action, ...] = ()

    @property
    def terminal(self):
        return len(self.history) == 2

    def payoff(self, player: Player) -> float:
        a, b = self.history

        if a == b:
            return 0

        value = 1.0
        if (
            a == Action.ROCK
            and b == Action.PAPER
            or a == Action.PAPER
            and b == Action.SCISSORS
            or a == Action.SCISSORS
            and b == Action.ROCK
        ):
            value = -1

        if player == 1:
            value = -value

        return value

    @property
    def chance(self):
        return False

    def chances(self) -> dict[Action, float]:
        raise NotImplementedError

    def sample(self) -> Action:
        raise NotImplementedError

    @property
    def active(self) -> Player:
        return cast(Player, len(self.history))

    def infoset(self, player: Player) -> InfoSet:
        return InfoSet(player)

    def apply(self, action: Action) -> RPS:
        return self.__class__(self.history + (action,))


if __debug__:
    _: Game[Action, InfoSet] = RPS()
