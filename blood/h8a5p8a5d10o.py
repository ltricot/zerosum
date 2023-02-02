from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearodds, basic, equities, potentials


actions = capped_bets(basic, 8)
_eq = equities((5,) * 8)
_p3 = potentials((5,), future=3)
_po = potentials((0,) + (5,) * 7, future=1)
cards = _eq * _p3 * _po
states = run * street * player * linearodds(50) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
