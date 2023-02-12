from __future__ import annotations

from typing import cast
from typing import ClassVar
from dataclasses import dataclass
import random
import enum

from ..game import Player, Game


class Action(enum.IntEnum):
    DRAW1 = 1
    DRAW2 = 2
    DRAW3 = 3
    BET = 4
    CHECK = 5
    CALL = 6
    FOLD = 7


Card = int


@dataclass(slots=True, frozen=True)
class InfoSet:
    player: Player
    card: Card
    history: tuple[Action, ...]

    def actions(self) -> tuple[Action, ...]:
        if len(self.history) == 0:
            return (Action.CHECK, Action.BET, Action.FOLD)
        elif len(self.history) == 1:
            last = self.history[-1]
            if last == Action.BET:
                return (Action.CALL, Action.FOLD)
            elif last == Action.CHECK:
                return (Action.BET, Action.CHECK)
            raise ValueError
        else:
            assert len(self.history) == 2 and self.history == (
                Action.CHECK,
                Action.BET,
            ), self.history
            return (Action.CALL, Action.FOLD)


@dataclass(slots=True, frozen=True)
class Kuhn:
    players: ClassVar[int] = 2

    history: tuple[Action, ...] = ()

    @classmethod
    def default(cls):
        return cls()

    @property
    def terminal(self):
        if not self.history:
            return False

        last = self.history[-1]
        if last == Action.FOLD:
            return True
        elif last == Action.CALL:
            return len(self.history) >= 4
        elif last == Action.CHECK:
            return len(self.history) >= 4

        return False

    def payoff(self, player: Player):
        value = 1
        if Action.BET in self.history and Action.CALL in self.history:
            value = 2

        if Action.FOLD in self.history:
            ix = self.history.index(Action.FOLD)
            winner = 1 - (ix % 2)
            return value if winner == player else -value

        if self.history[0] < self.history[1]:
            value = -value

        if player == 1:
            value = -value

        return value

    @property
    def chance(self):
        return len(self.history) <= 1

    def chances(self) -> dict[Action, float]:
        chances = {Action.DRAW1: 1 / 3, Action.DRAW2: 1 / 3, Action.DRAW3: 1 / 3}
        if not self.history:
            return chances

        chances.pop(self.history[0])
        for k in chances:
            chances[k] = 1 / 2

        return chances

    def sample(self) -> Action:
        return random.choice(list(self.chances().keys()))

    @property
    def active(self) -> Player:
        return cast(Player, len(self.history) % 2)

    def infoset(self, player: Player) -> InfoSet:
        return InfoSet(
            player=player,
            card=int(self.history[player]),
            history=self.history[2:],
        )

    def apply(self, action: Action):
        return self.__class__(self.history + (action,))


if __debug__:
    _: Game[Action, InfoSet] = Kuhn()
