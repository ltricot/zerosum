from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import (
    Translation,
    capped_bets,
    non_bet_actions,
)
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearpot, basic, equities


bets = capped_bets(basic, 8)
states = run * street * player * linearpot(20) * equities((30,) * 8) * bets


@abstract(Translation, states, bets)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, bets)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
