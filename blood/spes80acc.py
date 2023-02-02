from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearpot, basic, equities


actions = capped_bets(basic, 8)
cards = equities((8,) + (80,) * 7, dimension=50, maxiter=1000)
states = run * street * player * linearpot(20) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
