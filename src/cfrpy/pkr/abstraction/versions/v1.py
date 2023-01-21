from typing import Protocol
from typing import Tuple
from dataclasses import dataclass
import math

from ....game import Player, Game
from ...game import RiverOfBlood as _RiverOfBlood, InfoSet as _InfoSet, Action, Bet
from ..rounds import Mapper, ehs


# some abstractions:
# - only 1 bet per player per street
# - pot is bucketed geometrically
# - bet range: pot, all-in
# - hand: EHS


class Bucketer(Protocol):
    def __call__(self, pot: int) -> int:
        ...


def _default_bucketer(base: int):
    def bucketer(pot: int) -> int:
        if pot == 0:
            return -1
        return math.ceil(math.log(pot, base))

    def unbucketer(pot: int) -> int:
        if pot == -1:
            return 0
        return base ** pot

    return bucketer, unbucketer


_bucketer, _unbucketer = _default_bucketer(4)
_mapper = ehs


@dataclass(slots=True, frozen=True)
class InfoSet:
    chance: int
    player: Player
    pot: int
    bounds: Tuple[int, int]
    nonbetactions: Tuple[Tuple[Action, ...], bool]
    alreadybet: bool

    @classmethod
    def mapper(cls, infoset: _InfoSet):
        chance = _mapper(infoset.hand, ())
        player = infoset.player
        pot = _unbucketer(_bucketer(infoset.pot))
        bounds = cls._bounds(infoset)
        nbactions = infoset._non_bet_actions()

        alreadybet = False
        if infoset.stacks[0] == 400:
            if infoset.pips[infoset.player] > 2:
                alreadybet = True
        elif infoset.pips[infoset.player] > 0:
            alreadybet = True

        return cls(chance, player, pot, bounds, nbactions, alreadybet)

    @staticmethod
    def _bounds(infoset: _InfoSet):
        _lb, _ub = infoset._bounds()

        lb = _unbucketer(_bucketer(_lb))
        while lb < _lb:
            lb = _unbucketer(_bucketer(lb) + 1)

        ub = _unbucketer(_bucketer(_ub))
        while ub > _ub:
            ub = _unbucketer(_bucketer(ub) - 1)

        return lb, ub

    def _bets(self):
        qties = sorted(list(set((self.pot, 2 * self.pot, *self.bounds))))

        lb, ub = self.bounds
        for qty in qties:
            if lb <= qty <= ub:
                yield Bet(qty)

    def actions(self):
        actions, bets = self.nonbetactions
        if bets and not self.alreadybet:
            return (*actions, *self._bets())
        return actions


@dataclass(slots=True, frozen=True)
class RiverOfBlood(_RiverOfBlood):
    def infoset(self, player: Player) -> InfoSet:
        # super() doesn't work with slots
        infoset = _RiverOfBlood.infoset(self, player)
        return InfoSet.mapper(infoset)

    # this is fast with external sampling because we only walk
    # the abstraction's tree ; vanilla cfr however will walk the
    # full unabstracted tree so long as we do not override the
    # chances() method


if __debug__:
    game: Game[Action, InfoSet] = RiverOfBlood()
