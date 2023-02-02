from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearpot, basic, equities, potentials


actions = capped_bets(basic, 8)
_eq = equities((20,) * 8, dimension=30)
_p3 = potentials((20,), dimension=30, future=3)
_po = potentials((0,) + (20,) * 2, dimension=30, future=1)
cards = _eq * _p3 * _po
states = run * street * player * linearpot(20) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
