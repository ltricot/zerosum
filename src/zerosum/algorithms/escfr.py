import numpy as np

from typing import cast, Generic
from typing import Callable
from dataclasses import dataclass, field
from collections import defaultdict
import random

from ..game import Game, Player, I, A_inv
from .cfr import matching


# Externally Sampled CFR: a version of Monte Carlo CFR
# the idea is to sample chance's and the opponent's actions, but follow all
# of the player's actions. this is also simpler than CFR.
# http://mlanctot.info/files/papers/nips09mccfr.pdf
# http://mlanctot.info/files/papers/PhD_Thesis_MarcLanctot.pdf
@dataclass
class ESCFR(Generic[A_inv, I]):
    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), cast(Player, p), self.regrets, self.strategies)

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
    ):
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

        cfs = {action: 0 for action in actions}
        value = 0

        for action, p in zip(actions, strategy):
            cf = self.walk(game.apply(action), player, regrets, strategies)
            cfs[action] = cf
            value += p * cf

        for action in actions:
            R[action] += cfs[action] - value

        return value


# Outcome Sampling CFR
# TODO: implementation seems incorrect


@dataclass
class OSCFR(Generic[A_inv, I]):
    delta: float

    t: int = 1
    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    when: dict[I, int] = field(default_factory=lambda: defaultdict(int))
    touched: int = 0

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        for p in (0, 1):
            self.walk(game(), Player(p), 1, 1, self.regrets, self.strategies, 1, self.t)
        self.t += 1

    def walk(
        self,
        game: Game[A_inv, I],
        player: Player,
        pi: float,
        pmi: float,
        regrets: dict[I, dict[A_inv, float]],
        strategies: dict[I, dict[A_inv, float]],
        s: float,
        t: int,
    ):
        self.touched += 1

        if game.terminal:
            return game.payoff(player) / s, 1

        if game.chance:
            action = game.sample()
            return self.walk(
                game.apply(action), player, pi, pmi, regrets, strategies, s, t
            )

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
            sampling = self._delta(strategy)

            i = np.random.choice(len(actions), p=sampling)
            action = actions[i]
            prob = strategy[i]

            u, tail = self.walk(
                game.apply(action),
                player,
                pi,
                pmi * prob,
                regrets,
                strategies,
                s * sampling[i],
                t,
            )

            ci = self.when[infoset]
            for a, p in zip(actions, strategy):
                S[a] += (t - ci) * pmi * p
            self.when[infoset] = t

            return u, tail * prob

        sampling = self._delta(strategy)

        i = np.random.choice(len(actions), p=sampling)
        action = actions[i]
        prob = strategy[i]

        u, tail = self.walk(
            game.apply(action),
            player,
            pi * prob,
            pmi,
            regrets,
            strategies,
            s * sampling[i],
            t,
        )

        w = u * pmi
        for a in actions:
            if a == action:
                R[a] += w * tail * (1 - prob)
            else:
                R[a] += w * tail * (-prob)

        return u, tail * prob

    def _delta(self, strategy: list[float]):
        d = self.delta
        q = 1 / len(strategy)
        return [(1 - d) * p + d * q for p in strategy]
