from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearodds, basic, potentials


actions = capped_bets(basic, 3)
_s3 = potentials((20,), dimension=30, future=3)
_ss = potentials((0,) + (20,) * 7, dimension=30, future=1)
cards = _s3 * _ss
states = run * street * player * linearodds(50) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
