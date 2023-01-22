from typing import cast
from typing import Tuple
from dataclasses import dataclass

from ....abstraction import abstract
from ....game import InfoSet as PInfoSet
from ...game import RiverOfBlood, Action, InfoSet, Bet
from ..abstractions import (
    ehs,
    singlebet,
    pot,
    bounds,
    non_bet_actions,
    withbets,
    player,
    street,
)


_base = 2
_hand_buckets = 100
_bounds = bounds(_base)
_pot = pot(_base)


def bets(infoset: PInfoSet) -> Tuple[Action, ...]:
    infoset = cast(InfoSet, infoset)

    lb, ub = _bounds(infoset)
    pot = _pot(infoset)

    qties = sorted(list(set((pot, 2 * pot, 5 * pot, 10 * pot, 15 * pot))))
    return tuple(Bet(qty) for qty in qties if lb <= qty <= ub)


def identity(infoset: PInfoSet) -> Tuple[Action, ...]:
    infoset = cast(InfoSet, infoset)
    return tuple(infoset._non_bet_actions()[0])


@abstract(
    RiverOfBlood,
    player * street * ehs(_hand_buckets) * singlebet * _pot * non_bet_actions * _bounds,
    withbets(bets),
)
@dataclass(slots=True, frozen=True)
class Abstraction(RiverOfBlood):
    ...
