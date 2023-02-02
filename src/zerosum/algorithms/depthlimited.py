from typing import cast, Generic
from typing import Callable
from dataclasses import dataclass, field
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


@dataclass
class DepthLimited(Generic[A_inv, I]):
    depth: int
    maxiter: int
    equilibirum: dict[I, dict[A_inv, float]]

    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), self.regrets, self.strategies, 0)

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
        depth: int,
    ):
        if depth > self.depth:
            return self._value(game, player)

        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            action = game.sample()
            return self.walk(game.apply(action), player, regrets, strategies, depth)

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
            value = self.walk(
                game.apply(action), player, regrets, strategies, depth + 1
            )

            for action, p in zip(actions, strategy):
                S[action] += p

            return value

        cfs = {action: 0 for action in actions}
        value = 0

        for action, p in zip(actions, strategy):
            cf = 0
            if p > 1e-3:
                cf = self.walk(
                    game.apply(action), player, regrets, strategies, depth + 1
                )
            cfs[action] = cf
            value += p * cf

        for action in actions:
            R[action] += cfs[action] - value

        return value

    # as of today the following is simply incorrect:
    # knowing the value of game tree nodes is simply not enough to
    # perform search, unlike the case of perfect information games

    def _value(self, game: Game[A_inv, I], player: Player) -> float:
        return (
            sum(self._mc_value(game, player) for _ in range(self.maxiter))
            / self.maxiter
        )

    def _mc_value(self, game: Game[A_inv, I], player: Player) -> float:
        while not game.terminal:
            if game.chance:
                game = game.apply(game.sample())
                continue

            infoset = game.infoset(game.active)
            if infoset not in self.equilibirum:
                action = random.choice(infoset.actions())
            else:
                s = self.equilibirum[infoset]
                action = max(s, key=s.__getitem__)

            game = game.apply(action)

        return game.payoff(player)
