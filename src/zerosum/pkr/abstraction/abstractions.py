import eval7

from typing import cast
from typing import Callable
from dataclasses import dataclass
from functools import lru_cache
import math

from ...abstraction import algebraic
from ...game import InfoSet as PInfoSet
from ..game import InfoSet, Action, RiverOfBlood
from ..game import Allin, RaiseHalfPot, Raise75Pot, RaisePot
from ..game import Bet, Call, Check, Fold
from ..game import Draw, Flop, Turn, River, Run
from .hands import hs


_cards = eval7.Deck().cards


def pseudoharmonic(x: int, A: int, B: int) -> float:
    return (B - x) * (1 + A) / (B - A) / (1 + x)


_bet_action = (Bet, Allin, RaiseHalfPot, Raise75Pot, RaisePot)


@dataclass(frozen=True)
class Translation(RiverOfBlood):
    def _qty_of(self, action: Action) -> int:
        pot = self.pot + sum(self.pips)

        if isinstance(action, Bet):
            return action.bet
        elif isinstance(action, Allin):
            return self.stacks[self.active] - self.pips[self.active]
        elif isinstance(action, RaisePot):
            return pot
        elif isinstance(action, RaiseHalfPot):
            return pot // 2
        elif isinstance(action, Raise75Pot):
            return (3 * pot) // 4
        elif isinstance(action, Call):
            return abs(self.pips[self.active] - self.pips[1 - self.active])
        elif isinstance(action, Check):
            return 0
        elif isinstance(action, Fold):
            return -1
        raise ValueError

    def _similarity(self, action: Action, other: Action) -> float:
        if isinstance(action, _bet_action):

            if isinstance(other, _bet_action):
                relative = self._qty_of(other) / self._qty_of(action)
                if relative > 1:
                    relative = 1 / relative
                return relative

            if isinstance(other, (Call, Check)):
                return 0

        elif isinstance(action, Call):
            if isinstance(other, Call):
                return 1

        elif isinstance(action, Check):
            if isinstance(other, Check):
                return 1
            if isinstance(other, _bet_action):
                return 0

        elif isinstance(action, Fold):
            if isinstance(other, Fold):
                return 1

        return -1

    def translate(self, action: Action) -> Action:
        if self.chance:
            return action

        sim, best = -2, None
        for other in self.infoset(self.active).actions():
            s = self._similarity(action, other)
            if s > sim:
                sim, best = s, other
        return cast(Action, best)

    def apply(self, action: Action):
        return RiverOfBlood.apply(self, self.translate(action))


@algebraic
def will_have_run(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    if len(infoset.community) >= 5:
        return (True, _cards[infoset.community[-1]].suit in (0, 3))
    return (False, False)


@algebraic
def street(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return len(infoset.community)


@algebraic
def player(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return infoset.player


# it is vital that this function be cached
# not for performance reasons, but because an infoset
# should always be abstracted in the same way
# otherwise bad things happen
@lru_cache(maxsize=2 ** 24)
def _ehs(
    hand: tuple[eval7.Card, eval7.Card],
    community: tuple[eval7.Card, ...],
    buckets: int,
):
    strength = hs(hand, community, 200)
    return round(strength * buckets)


def ehs(buckets: int):
    @algebraic
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        hand = (_cards[infoset.hand[0]], _cards[infoset.hand[1]])
        community = tuple(_cards[i] for i in infoset.community)

        # must be cached !!
        return _ehs(hand, community, buckets)

    return inner


@algebraic
def singlebet(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return _alreadybet(infoset)


# technically buggy but we can't change it as abstractions rely on it
def _alreadybet(infoset: InfoSet):
    raised = False
    if infoset.stacks[0] == 400:
        if infoset.pips[infoset.player] > 2:
            raised = True
    elif infoset.pips[infoset.player] > 0:
        raised = True

    return raised


_chance_action = (Draw, Flop, Turn, River, Run)


def how_many_bets(cap: int):
    @algebraic
    def how_many_bets(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        return min(cap, _bets(infoset))

    return how_many_bets


def _bets(infoset: InfoSet):
    bets = 0
    for action in reversed(infoset.history):
        if isinstance(action, _chance_action):
            break
        if isinstance(action, _bet_action):
            bets += 1
    return bets


def _bucket(qty: int, base: int) -> int:
    if qty <= 0:
        return -1
    return math.ceil(math.log(qty, base))


def _unbucket(qty: int, base: int) -> int:
    if qty == -1:
        return 0
    return base ** qty


def _linear_bucket(qty: int, base: int) -> int:
    if qty <= 0:
        return -1
    return math.ceil(qty / base)


def _linear_unbucket(qty: int, base: int) -> int:
    if qty == -1:
        return 0
    return base * qty


def pot(base: int):
    @algebraic
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        return _unbucket(_bucket(infoset.pot, base), base)

    return inner


@algebraic
def justpot(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return infoset.pot + sum(infoset.pips)


@algebraic
def justpips(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return infoset.pips


@algebraic
def justcost(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return max(infoset.pips) - min(infoset.pips)


def linearcost(acc: int):
    @algebraic
    def linearcost(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        cost = max(infoset.pips) - min(infoset.pips)
        pot = infoset.pot + sum(infoset.pips)
        return round(cost / pot * acc)

    return linearcost


def linearpot(base: int):
    @algebraic
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        return _linear_unbucket(
            _linear_bucket(infoset.pot + sum(infoset.pips), base),
            base,
        )

    return inner


def bounds(base: int):
    @algebraic
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        _lb, _ub = infoset._bounds()

        lb = _unbucket(_bucket(_lb, base), base)
        while lb < _lb:
            lb = _unbucket(_bucket(lb, base) + 1, base)

        ub = _unbucket(_bucket(_ub, base), base)
        while ub > _ub:
            ub = _unbucket(_bucket(ub, base) - 1, base)

        return lb, ub

    return inner


@algebraic
def non_bet_actions(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return infoset._non_bet_actions()


def withbets(better: Callable[[InfoSet], tuple[Action, ...]]):
    @algebraic
    def actions(infoset: PInfoSet) -> tuple[Action, ...]:
        infoset = cast(InfoSet, infoset)
        actions, bets = infoset._non_bet_actions()

        if bets and not _alreadybet(infoset):
            return (*actions, *better(infoset))

        return actions

    return actions


def capped_bets(better: Callable[[InfoSet], tuple[Action, ...]], cap: int = 3):
    @algebraic
    def actions(infoset: PInfoSet) -> tuple[Action, ...]:
        infoset = cast(InfoSet, infoset)
        actions, bets = infoset._non_bet_actions()

        if bets and _bets(infoset) < cap:
            return (*actions, *better(infoset))

        return actions

    return actions
