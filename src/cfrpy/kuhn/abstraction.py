from typing import Tuple
from dataclasses import dataclass

from ..game import Player, Game
from .game import Kuhn as _Kuhn, InfoSet as _InfoSet, Action


@dataclass(frozen=True)
class InfoSet:
    _infoset: _InfoSet

    @property
    def _abstraction(self):
        card = self._infoset.card
        if card == 2:
            card = 3
        return (self._infoset.player, card, self._infoset.history)

    def actions(self) -> Tuple[Action, ...]:
        # action abstraction
        return self._infoset.actions()

    def __hash__(self):
        # state abstraction
        return hash(self._abstraction)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, InfoSet) and self._abstraction == __o._abstraction


@dataclass(frozen=True)
class Kuhn(_Kuhn):
    def infoset(self, player: Player) -> InfoSet:
        infoset = super().infoset(player)
        return InfoSet(infoset)


if __debug__:
    game: Game[Action, InfoSet] = Kuhn()
