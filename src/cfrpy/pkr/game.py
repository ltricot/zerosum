import eval7

from typing import cast
from typing import Tuple, Dict
from dataclasses import dataclass
import itertools
import random
import math

from ..game import Player, Game


Card = int
_cards = eval7.Deck().cards
_ix_cards = list(range(52))


@dataclass(slots=True, frozen=True)
class Draw:
    hand: tuple[Card, Card]


@dataclass(slots=True, frozen=True)
class Fold:
    ...


@dataclass(slots=True, frozen=True)
class Call:
    ...


@dataclass(slots=True, frozen=True)
class Check:
    ...


@dataclass(slots=True, frozen=True)
class Bet:
    bet: int


@dataclass(slots=True, frozen=True)
class _Reveal:
    cards: Tuple[Card, ...]


@dataclass(slots=True, frozen=True)
class Flop(_Reveal):
    ...


@dataclass(slots=True, frozen=True)
class Turn(_Reveal):
    ...


@dataclass(slots=True, frozen=True)
class River(_Reveal):
    ...


@dataclass(slots=True, frozen=True)
class Run(_Reveal):
    ...


Action = Draw | Fold | Call | Check | Bet | Flop | Turn | River | Run


@dataclass(slots=True, frozen=True)
class InfoSet:
    hand: Tuple[Card, Card]
    community: Tuple[Card, ...]

    player: Player
    stacks: Tuple[int, int]
    pips: Tuple[int, int]
    pot: int

    history: Tuple[Action, ...]

    def _bounds(self):
        player = self.player
        cost = self.pips[1 - player] - self.pips[player]
        maxbound = min(
            self.stacks[player] - self.pips[player],
            self.stacks[1 - player] - self.pips[1 - player] + cost,
        )
        minbound = min(maxbound, cost + max(cost, 2))
        return minbound, maxbound

    def _bets(self):
        # TODO: bottleneck
        lb, ub = self._bounds()
        yield from (Bet(bet) for bet in range(lb, ub + 1))

    def _non_bet_actions(self):
        player = self.player
        cost = self.pips[1 - player] - self.pips[player]

        if cost == 0:
            if self.stacks[0] > self.pips[0] and self.stacks[1] > self.pips[1]:
                return (Check(),), True
            return (Check(),), False

        if (
            cost < self.stacks[player] - self.pips[player]
            and self.stacks[1 - player] > self.pips[1 - player]
        ):
            return (Fold(), Call()), True
        return (Fold(), Call()), False

    def actions(self):
        actions, bets = self._non_bet_actions()
        if bets:
            return (*actions, *self._bets())
        return actions


@dataclass(slots=True, frozen=True)
class RiverOfBlood:
    history: Tuple[Action, ...] = ()
    community: Tuple[Card, ...] = ()
    active: Player = cast(Player, 0)

    stacks: Tuple[int, int] = (400, 400)
    pips: Tuple[int, int] = (1, 2)
    pot: int = 3

    @property
    def _street(self):
        return len(self.community)

    @property
    def terminal(self):
        if not self.history:
            return False

        last = self.history[-1]
        if isinstance(last, Fold):
            return True

        if self._street < 5:
            return False
        if _cards[self.community[-1]].suit in (1, 2):
            return False

        last = self.history[-1]
        if isinstance(last, Call):
            return True

        if isinstance(last, Check):
            before = self.history[-2]
            if isinstance(before, Check):
                return True

        return False

    def payoff(self, player: Player):
        pot = self.pot + sum(self.pips)

        last = self.history[-1]
        if isinstance(last, Fold):
            if self.active == player:
                return self.stacks[player] + pot - 400
            return self.stacks[player] - 400

        h0 = cast(Draw, self.history[0]).hand
        h1 = cast(Draw, self.history[1]).hand

        s0 = eval7.evaluate(tuple(_cards[i] for i in h0 + self.community))
        s1 = eval7.evaluate(tuple(_cards[i] for i in h1 + self.community))

        if s0 > s1:
            return pot // 2 if player == 0 else -pot // 2
        elif s1 > s0:
            return pot // 2 if player == 1 else -pot // 2

        return 0

    @property
    def chance(self):
        if len(self.history) <= 1:
            return True

        last = self.history[-1]
        if isinstance(last, Call):
            if self._street == 0:
                return len(self.history) >= 4
            return not self.terminal

        if isinstance(last, Check):
            before = self.history[-2]
            if isinstance(before, Check):
                return not self.terminal

        return False

    def chances(self) -> Dict[Action, float]:
        if len(self.history) == 0:
            # TODO: bottleneck
            return {
                Draw(hand): 1 / math.comb(52, 2)
                for hand in itertools.combinations(_ix_cards, 2)
            }

        elif len(self.history) == 1:
            hand = cast(Draw, self.history[0])
            deck = [card for card in _ix_cards if card not in hand.hand]
            # TODO: bottleneck
            return {
                Draw(hand): 1 / math.comb(50, 2)
                for hand in itertools.combinations(deck, 2)
            }

        seen = (
            self.community
            + cast(Draw, self.history[0]).hand
            + cast(Draw, self.history[1]).hand
        )
        deck = [card for card in _ix_cards if card not in seen]

        street = self._street
        if street == 0:
            # TODO: bottleneck
            return {
                Flop(cards): 1 / math.comb(48, 3)
                for cards in itertools.combinations(deck, 3)
            }
        elif street == 3:
            return {Turn((card,)): 1 / len(deck) for card in deck}
        elif street == 4:
            return {River((card,)): 1 / len(deck) for card in deck}
        else:
            return {Run((card,)): 1 / len(deck) for card in deck}

    def sample(self):
        if len(self.history) == 0:
            return Draw(tuple(random.sample(_ix_cards, 2)))
        elif len(self.history) == 1:
            hand = cast(Draw, self.history[0])
            deck = [card for card in _ix_cards if card not in hand.hand]
            return Draw(tuple(random.sample(deck, 2)))

        seen = (
            self.community
            + cast(Draw, self.history[0]).hand
            + cast(Draw, self.history[1]).hand
        )
        deck = [card for card in _ix_cards if card not in seen]

        street = self._street
        if street == 0:
            return Flop(tuple(random.sample(deck, 3)))
        elif street == 3:
            return Turn(tuple(random.sample(deck, 1)))
        elif street == 4:
            return River(tuple(random.sample(deck, 1)))
        else:
            return Run(tuple(random.sample(deck, 1)))

    def apply(self, action: Action):
        community = self.community
        player = cast(Player, 1 - self.active)

        stacks = self.stacks
        pips = self.pips
        pot = self.pot

        if isinstance(action, _Reveal):
            community = community + action.cards
            player = cast(Player, 1)
            stacks = (stacks[0] - pips[0], stacks[1] - pips[1])
            pot = pot + sum(pips)
            pips = (0, 0)

        elif isinstance(action, (Bet, Call)):
            if isinstance(action, Bet):
                qty = action.bet
            elif isinstance(action, Call):
                qty = abs(pips[0] - pips[1])

            pips = (
                (pips[0] + qty, pips[1])
                if self.active == 0
                else (pips[0], pips[1] + qty)
            )

        return self.__class__(
            self.history + (action,), community, player, stacks, pips, pot
        )

    def infoset(self, player: Player) -> InfoSet:
        return InfoSet(
            cast(Draw, self.history[player]).hand,
            self.community,
            player,
            self.stacks,
            self.pips,
            self.pot,
            self.history,
        )


if __debug__:
    _: Game[Action, InfoSet] = RiverOfBlood()
