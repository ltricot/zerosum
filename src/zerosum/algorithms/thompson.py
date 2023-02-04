import numpy as np

from typing import Generic, TypeVar
from dataclasses import dataclass
import abc

from ..game import A_inv, I, Game, Player


P = TypeVar("P")


@dataclass
class Thompson(Generic[A_inv, I, P]):
    def __post_init__(self):
        self.priors = {}
        self.touched = 0

    def once(self, game: Game[A_inv, I]):
        self.walk(game, Player(0))
        self.walk(game, Player(1))

    def walk(self, game: Game[A_inv, I], player: Player):
        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            return self.walk(game.apply(game.sample()), player)

        iset = game.infoset(game.active)
        actions = iset.actions()

        if iset not in self.priors:
            self.priors[iset] = {a: self.default(iset, a) for a in actions}

        priors = self.priors[iset]
        action = max(actions, key=lambda a: self.sample(priors[a]))
        payoff = self.walk(game.apply(action), player)

        if game.active == player:
            priors[action] = self.update(priors[action], payoff)

        return payoff

    @abc.abstractmethod
    def default(self, infoset: I, action: A_inv) -> P:
        ...

    @abc.abstractmethod
    def sample(self, prior: P) -> float:
        ...

    @abc.abstractmethod
    def update(self, prior: P, payoff: float) -> P:
        ...


class ESThompson(Thompson[A_inv, I, P]):

    # External Thompson Sampling ?
    # When the chosen player is active, play all actions and return average
    # payoff

    def walk(self, game: Game[A_inv, I], player: Player):
        self.touched += 1

        if game.terminal:
            return game.payoff(player)

        if game.chance:
            return self.walk(game.apply(game.sample()), player)

        iset = game.infoset(game.active)
        actions = iset.actions()

        if iset not in self.priors:
            self.priors[iset] = {a: self.default(iset, a) for a in actions}

        priors = self.priors[iset]

        if game.active != player:
            action = max(actions, key=lambda a: self.sample(priors[a]))
            return self.walk(game.apply(action), player)

        value = 0
        for action, p in zip(actions, self.dist(priors)):
            payoff = self.walk(game.apply(action), player)
            priors[action] = self.update(priors[action], payoff)
            value += p * payoff

        return value

    @abc.abstractmethod
    def dist(self, priors: tuple[P, ...]) -> tuple[float, ...]:
        ...


_BetaPrior = tuple[float, float]


@dataclass
class BetaThompson(Thompson[A_inv, I, _BetaPrior]):
    payoffrange: tuple[float, float]

    def default(self, infoset: I, action: A_inv):
        return (1, 1)

    def sample(self, prior: _BetaPrior):
        return np.random.beta(*prior)

    def update(self, prior: _BetaPrior, payoff: float):
        l, r = self.payoffrange
        payoff = (payoff - l) / (r - l)
        return (prior[0] + payoff, prior[1] + 1 - payoff)


@dataclass
class LinearBetaThompson(BetaThompson[A_inv, I]):
    periods: int

    # Thompson sampling solves the stationary armed bandit problem
    # When learning to play by playing yourself, you are playing against
    # an evolving strategy and are therefore really solving a non-stationary
    # bandit ; discounting priors just increases their variance to
    # acknowledge the fact they are likely more inaccurate than we believe

    def __post_init__(self):
        super().__post_init__()
        self._period = 1

    def forget(self):
        factor = self._period / (1 + self._period)
        self._period += 1

        for priors in self.priors.values():
            for action, p in priors.items():
                priors[action] = (p[0] * factor, p[0] * factor)

    def once(self, game: Game[A_inv, I]):
        super().once(game)

        while self.touched // self.periods > self._period:
            self.forget()
