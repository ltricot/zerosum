from typing import cast
from dataclasses import dataclass

from ..game import Player


@dataclass(slots=True, frozen=True)
class InfoSet:
    utility: int

    def actions(self):
        return tuple(Bid(q) for q in range(0, 1 + self.utility))


@dataclass(slots=True, frozen=True)
class Bid:
    bid: int


@dataclass(slots=True, frozen=True)
class Game:
    utility: int
    history: tuple[Bid, ...] = ()

    @property
    def terminal(self):
        return len(self.history) == 2

    def payoff(self, player: Player):
        b1, b2 = self.history
        if b1.bid + b2.bid <= self.utility:
            return self.history[player].bid
        return 0

    @property
    def chance(self):
        return False

    def chances(self):
        raise NotImplementedError

    def sample(self):
        raise NotImplementedError

    @property
    def active(self):
        return cast(Player, len(self.history))

    def infoset(self, player: Player):
        return InfoSet(self.utility)

    def apply(self, action: Bid):
        return Game(self.utility, self.history + (action,))
