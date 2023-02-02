from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearodds, basic, potentials


actions = capped_bets(basic, 3)
cards = potentials((10,), future=3) * potentials((0,) + (10,) * 7, future=1)
states = run * street * player * linearodds(50) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
