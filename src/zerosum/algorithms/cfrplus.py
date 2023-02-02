from typing import cast, Generic
from typing import Callable
from dataclasses import dataclass, field
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


# https://arxiv.org/pdf/1407.5042.pdf
# the only differences with external sampling cfr are:
# - the strategy updates are linearly weighted (as in linear CFR)
# - the regrets are clipped above 0 when the strategy is updated
#   (regret matching+ learner)
# apparently CFR+ doesn't help when used with MCCFR, so maybe this file is
# useless
@dataclass
class ESCFRP(Generic[A_inv, I]):
    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0
    t: int = 1

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), self.regrets, self.strategies, self.t)

        self.t += 1

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
        t: int,
    ):
        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            action = game.sample()
            return self.walk(game.apply(action), player, regrets, strategies, t)

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
            value = self.walk(game.apply(action), player, regrets, strategies, t)

            for action, p in zip(actions, strategy):
                S[action] += t * p
                R[action] = max(0, R[action])

            return value

        cfs = {action: 0 for action in actions}
        value = 0

        for action, p in zip(actions, strategy):
            cf = self.walk(game.apply(action), player, regrets, strategies, t)
            cfs[action] = cf
            value += p * cf

        for action in actions:
            R[action] += cfs[action] - value

        return value


from typing import cast, Generic
from typing import Callable
from dataclasses import dataclass, field

from ..game import Game, Player, A_inv, I


def matching(regrets: list[float], inplace: bool = True):
    regrets = [max(0, r) for r in regrets]
    denom = sum(regrets)

    if denom > 0:
        if inplace:
            for i, r in enumerate(regrets):
                regrets[i] = r / denom
            return regrets
        return [r / denom for r in regrets]

    return [1 / len(regrets)] * len(regrets)


@dataclass
class CFRP(Generic[A_inv, I]):
    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), 1, 1, self.regrets, self.strategies)

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        p0: float,
        p1: float,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
    ):
        self.touched += 1

        # pruning
        if p0 == p1 == 0:
            return 0

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            value = 0
            for action, p in game.chances().items():
                p0p = p0 if player == 0 else p0 * p
                p1p = p1 if player == 1 else p1 * p
                value += p * self.walk(
                    game.apply(action), player, p0p, p1p, regrets, strategies
                )
            return value

        infoset = game.infoset(game.active)
        actions = infoset.actions()

        if infoset not in regrets:
            regrets[infoset] = {action: 0 for action in actions}
        if infoset not in strategies:
            strategies[infoset] = {action: 0 for action in actions}

        R = regrets[infoset]
        S = strategies[infoset]

        strategy = matching(list(R.values()))
        cfs = {action: 0 for action in actions}
        value = 0

        for action, p in zip(actions, strategy):
            p0p = p0 * p if game.active == 0 else p0
            p1p = p1 * p if game.active == 1 else p1
            cf = self.walk(game.apply(action), player, p0p, p1p, regrets, strategies)

            cfs[action] = cf
            value += p * cf

        pi, pmi = p0, p1
        if player == 1:
            pi, pmi = p1, p0

        if game.active == player:
            for action, p in zip(actions, strategy):
                R[action] = max(0, R[action] + pmi * (cfs[action] - value))  # rm+
                S[action] += pi * p

        return value
