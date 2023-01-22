from typing import cast, Generic
from typing import Dict, Callable
from dataclasses import dataclass, field
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


# https://arxiv.org/pdf/1407.5042.pdf
# the only differences with external sampling cfr are:
# - the strategy updates are linearly weighted (as in linear CFR)
# - the regrets are clipped above 0 when the strategy is updated
#   (regret matching+ learner)
#
# in this implementation we weigh by t^2 rather than t
# https://dl.acm.org/doi/pdf/10.1609/aaai.v33i01.33011829
@dataclass
class ESCFRP(Generic[A_inv, I]):
    regrets: Dict[I, Dict[A_inv, float]] = field(default_factory=dict)
    strategies: Dict[I, Dict[A_inv, float]] = field(default_factory=dict)
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
        regrets: Dict[I, Dict[A_inv, float]],
        strategies: Dict[I, Dict[A_inv, float]],
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
                S[action] += (t ** 2) * p
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
