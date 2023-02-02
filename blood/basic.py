import eval7

from typing import cast
from typing import Optional
from functools import lru_cache
import pickle
import math

from zerosum.game import InfoSet as PInfoSet
from zerosum.abstraction import algebraic
from zerosum.pkr.abstraction.hands import equity, potential, emd
from zerosum.pkr.game import InfoSet, RaiseHalfPot, Raise75Pot, RaisePot, Allin, Bet


Card = eval7.Card
_cards = eval7.Deck().cards


MAXITER = 1000


@algebraic
def lastaction(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    if infoset.history:
        return infoset.history[-1]


@algebraic
def run(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    if len(infoset.community) >= 5:
        card = cast(InfoSet, infoset).community[-1]
        return _cards[card].suit in (0, 3)


@algebraic
def street(infoset: PInfoSet):
    return len(cast(InfoSet, infoset).community)


def linearcost(acc: int):
    @algebraic
    def linearcost(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        cost = abs(infoset.pips[0] - infoset.pips[1])
        pot = infoset.pot + sum(infoset.pips)
        return round(cost / pot * acc)

    return linearcost


@algebraic
def player(infoset: PInfoSet):
    return cast(InfoSet, infoset).player


def linearpot(acc: int):
    @algebraic
    def linearpot(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        pot = infoset.pot + sum(infoset.pips)
        return round(pot / 800 * acc)

    return linearpot


_bet_action = (RaiseHalfPot, RaisePot, Allin, Bet)


def linearodds(acc: int):
    @algebraic
    def linearodds(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)

        if not infoset.history or not isinstance(infoset.history[-1], _bet_action):
            return None

        pot = infoset.pot + sum(infoset.pips)
        cost = abs(infoset.pips[0] - infoset.pips[1])
        return round(cost / pot * acc)

    return linearodds


@algebraic
def basic(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    lb, ub = infoset._bounds()

    pot = infoset.pot + sum(infoset.pips)
    stack = infoset.stacks[infoset.player] - infoset.pips[infoset.player]

    bets = []
    if lb <= pot // 2 <= ub:
        bets.append(RaiseHalfPot())
    if lb <= pot <= ub:
        bets.append(RaisePot())
    if lb <= stack <= ub:
        bets.append(Allin())

    return tuple(bets)


@algebraic
def advanced(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    lb, ub = infoset._bounds()

    pot = infoset.pot + sum(infoset.pips)
    stack = infoset.stacks[infoset.player] - infoset.pips[infoset.player]

    bets = []
    if lb <= 2 <= ub:
        bets.append(Bet(2))
    if lb <= pot // 2 <= ub:
        bets.append(RaiseHalfPot())
    if lb <= 3 * pot // 4 <= ub:
        bets.append(Raise75Pot())
    if lb <= pot <= ub:
        bets.append(RaisePot())
    if lb <= stack <= ub:
        bets.append(Allin())

    return tuple(bets)


@lru_cache(maxsize=2 ** 10)
def _equity(hand: tuple[Card, Card], community: tuple[Card, ...], d: int, maxiter: int):
    return equity(hand, community, d, maxiter)


def _equity_abstraction(street, centroids, dimension=10, maxiter=MAXITER):
    @algebraic
    def _equity_abstraction(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)

        if len(infoset.community) != street:
            return -1

        hand = tuple(_cards[i] for i in infoset.hand)
        community = tuple(_cards[i] for i in infoset.community)
        h = _equity(hand, community, dimension, maxiter)

        mi, md = 0, math.inf
        for i, c in enumerate(centroids):
            d = emd(h, c)
            if d < md:
                mi, md = i, d

        return mi

    return _equity_abstraction


def equities(
    accs: tuple[int, ...],
    dimension: Optional[int] = None,
    maxiter: int = MAXITER,
):
    abstractions = []

    for street, acc in zip((0, 3) + tuple(range(4, 15)), accs):
        if acc == 0:
            continue

        path = f"centroids/{street}-{acc}.pkl"
        if dimension is not None:
            path = f"centroids/{street}-{acc}-{dimension}.pkl"
        with open(path, "rb") as f:
            centroids = pickle.load(f)

        a = _equity_abstraction(street, centroids, dimension or 10, maxiter)
        abstractions.append(a)

    a = abstractions.pop()
    while abstractions:
        a = a * abstractions.pop()

    return a


@lru_cache(maxsize=2 ** 10)
def _potential(
    hand: tuple[Card, Card],
    community: tuple[Card, ...],
    d: int,
    maxiter: int,
    future: int,
):
    return potential(hand, community, d, maxiter, future)


def _potential_abstraction(street, centroids, future, dimension):
    @algebraic
    def _potential_abstraction(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)

        if len(infoset.community) != street:
            return -1

        hand = tuple(_cards[i] for i in infoset.hand)
        community = tuple(_cards[i] for i in infoset.community)
        h = _potential(hand, community, dimension, MAXITER, future)

        mi, md = 0, math.inf
        for i, c in enumerate(centroids):
            d = emd(h, c)
            if d < md:
                mi, md = i, d

        return mi

    return _potential_abstraction


def potentials(accs: tuple[int, ...], future: int, dimension: Optional[int] = None):
    abstractions = []

    for street, acc in zip((0, 3) + tuple(range(4, 15)), accs):
        if acc == 0:
            continue

        path = f"potentials/{street}-f{future}-{acc}.pkl"
        if dimension is not None:
            path = f"potentials/{street}-f{future}-{acc}-{dimension}.pkl"
        with open(path, "rb") as f:
            centroids = pickle.load(f)

        a = _potential_abstraction(street, centroids, future, dimension or 10)
        abstractions.append(a)

    a = abstractions.pop()
    while abstractions:
        a = a * abstractions.pop()

    return a


_ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

from ._preflop import clusters

_reverse = {}
for i, cluster in enumerate(clusters):
    for hand in cluster:
        _reverse[hand] = i


def _represent(hand: tuple[Card, Card]):
    ci, cj = hand
    ri, rj = sorted((ci.rank, cj.rank), reverse=True)
    if ri == rj:
        return f"{_ranks[ri]}{_ranks[rj]}"

    suited = "s" if ci.suit == cj.suit else "o"
    return f"{_ranks[ri]}{_ranks[rj]}{suited}"


@algebraic
def colorsuited(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    ci, cj = infoset.hand
    ci, cj = _cards[ci], _cards[cj]

    if ci.suit == cj.suit:
        return ci.suit in (0, 3)
    return None


@algebraic
def preflop(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    if len(infoset.community) != 0:
        return -1

    ci, cj = infoset.hand
    hand = _cards[ci], _cards[cj]
    return _reverse[_represent(hand)]
