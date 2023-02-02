from typing import cast
from typing import Optional, Union
from dataclasses import dataclass

from ..game import Player


@dataclass(slots=True, frozen=True)
class InfoSet:
    offer: Optional[int]
    utility: int

    def actions(self):
        if self.offer is None:
            return tuple(Offer(q) for q in range(0, 1 + self.utility))
        return (Reject(), Accept())


@dataclass(slots=True, frozen=True)
class Offer:
    offer: int


@dataclass(slots=True, frozen=True)
class Reject:
    ...


@dataclass(slots=True, frozen=True)
class Accept:
    ...


Action = Union[Offer, Reject, Accept]


@dataclass(slots=True, frozen=True)
class Game:
    utility: int
    history: tuple[Action, ...] = ()

    @property
    def terminal(self):
        return len(self.history) == 2

    def payoff(self, player: Player):
        if isinstance(self.history[1], Accept):
            offer = cast(Offer, self.history[0]).offer
            if player == 1:
                return offer
            return self.utility - offer
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
        if len(self.history) == 0:
            return InfoSet(None, self.utility)
        return InfoSet(cast(Offer, self.history[0]).offer, self.utility)

    def apply(self, action: Action):
        return Game(self.utility, self.history + (action,))
