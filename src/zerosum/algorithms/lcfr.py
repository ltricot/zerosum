from typing import cast, Generic
from typing import Callable
from dataclasses import dataclass, field
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


# LCFR or linear CFR: the idea is to discount regrets rather
# than strategies ; it can be mixed with MCCFR. LCFR can supposedly
# help when the payoff range is large (notably, some actions lead to large
# negative regret - they are blunders).
# https://dl.acm.org/doi/pdf/10.1609/aaai.v33i01.33011829
@dataclass
class ESLCFR(Generic[A_inv, I]):
    threshold: int = 10 ** 7

    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)

    _touched: int = 0
    touched: int = 0
    period: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), self.regrets, self.strategies)

        if self._touched > self.threshold:
            self._touched = 0
            self.period += 1
            self._discount()

    def _discount(self):
        factor = self.period / (self.period + 1)

        for R in self.regrets.values():
            for action in R:
                R[action] *= factor

        for S in self.strategies.values():
            for action in S:
                S[action] *= factor

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
    ) -> float:
        self._touched += 1
        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            action = game.sample()
            return self.walk(game.apply(action), player, regrets, strategies)

        infoset = game.infoset(game.active)
        actions = infoset.actions()

        if infoset not in regrets:
            regrets[infoset] = {action: 0 for action in actions}
        if infoset not in strategies:
            strategies[infoset] = {action: 0 for action in actions}

        R = regrets[infoset]
        S = strategies[infoset]

        strategy = matching(list(R.values()))

        if game.active != player:
            (action,) = random.choices(actions, weights=strategy)
            value = self.walk(game.apply(action), player, regrets, strategies)

            for action, p in zip(actions, strategy):
                S[action] += p

            return value

        cfs = {action: 0.0 for action in actions}
        value = 0.0

        for action, p in zip(actions, strategy):
            cf = self.walk(game.apply(action), player, regrets, strategies)
            cfs[action] = cf
            value += p * cf

        for action in actions:
            R[action] += cfs[action] - value

        return value
