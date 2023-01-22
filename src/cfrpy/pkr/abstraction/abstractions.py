from typing import cast
from typing import Tuple, Callable
from functools import cache
import math

from ...abstraction import algebraic
from ...game import InfoSet as PInfoSet
from ..game import InfoSet, Action
from .hands import hs


@algebraic
def street(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return len(infoset.community)


@algebraic
def player(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return infoset.player


def ehs(buckets: int):
    # it is vital that this function be cached
    # not for performance reasons, but because an infoset
    # should always be abstracted in the same way
    # otherwise bad things happen

    @algebraic
    @cache
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        strength = hs(infoset.hand, infoset.community, 100)
        return round(strength * buckets)

    return inner


@algebraic
def singlebet(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    return _alreadybet(infoset)


def _alreadybet(infoset: InfoSet):
    raised = False
    if infoset.stacks[0] == 400:
        if infoset.pips[infoset.player] > 2:
            raised = True
    elif infoset.pips[infoset.player] > 0:
        raised = True

    return raised


def _bucket(qty: int, base: int) -> int:
    if qty == 0:
        return -1
    return math.ceil(math.log(qty, base))


def _unbucket(qty: int, base: int) -> int:
    if qty == -1:
        return 0
    return base ** qty


def pot(base: int):
    @algebraic
    def inner(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        return _unbucket(_bucket(infoset.pot, base), base)

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


def withbets(better: Callable[[InfoSet], Tuple[Action, ...]]):
    def actions(infoset: PInfoSet) -> Tuple[Action, ...]:
        infoset = cast(InfoSet, infoset)
        actions, bets = infoset._non_bet_actions()

        if bets and not _alreadybet(infoset):
            return (*actions, *better(infoset))

        return actions

    return actions
