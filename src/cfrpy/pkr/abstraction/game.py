from typing import Protocol
from dataclasses import dataclass
import math

from ...game import Player, Game
from ..game import RiverOfBlood as _RiverOfBlood, InfoSet as _InfoSet, Action, Bet
from .rounds import Mapper, ehs


class Bucketer(Protocol):
    def __call__(self, pot: int) -> int:
        ...


def _default_bucketer(pot: int) -> int:
    # 10 levels
    if pot == 0:
        return -1
    return math.ceil(math.log(pot, 4))


_bucketer: Bucketer = _default_bucketer
_mapper = ehs


@dataclass(slots=True, frozen=True)
class InfoSet:
    _infoset: _InfoSet

    @property
    def _abstraction(self):
        infoset = self._infoset

        chance = _mapper(infoset.hand, ())
        player = infoset.player

        pot = _bucketer(infoset.pot)
        cost = _bucketer(infoset.pips[1 - player] - infoset.pips[player])
        actions = self.actions()

        return (chance, player, pot, cost, actions)

    def _bets(self):
        qties = {
            _bucketer(qty): qty
            for qty in range(*self._infoset._bounds())
            if _bucketer(qty + 1) != _bucketer(qty)
        }
        for qty in sorted(list(qties.values())):
            if qty < 60:
                yield Bet(qty)

    def actions(self):
        actions, bets = self._infoset._non_bet_actions()
        if bets:
            return (*actions, *self._bets())
        return actions

    def __hash__(self):
        return hash(self._abstraction)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, InfoSet) and self._abstraction == __o._abstraction


@dataclass(slots=True, frozen=True)
class RiverOfBlood(_RiverOfBlood):
    def infoset(self, player: Player) -> InfoSet:
        # super() doesn't work with slots
        infoset = _RiverOfBlood.infoset(self, player)
        return InfoSet(infoset)


if __debug__:
    game: Game[Action, InfoSet] = RiverOfBlood()
