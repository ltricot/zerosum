from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets, how_many_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearpot, basic, equities


actions = capped_bets(basic, 8)
cards = equities((60,) * 2, dimension=30) * equities((0, 0) + (10,) * 6, dimension=30)
states = run * street * player * linearpot(50) * how_many_bets(8) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
