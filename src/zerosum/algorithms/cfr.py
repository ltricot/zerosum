from typing import Generic
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
class CFR(Generic[A_inv, I]):
    regrets: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    strategies: dict[I, dict[A_inv, float]] = field(default_factory=dict)
    touched: int = 0

    def _run_iteration(self, game: type[Game[A_inv, I]]):
        for p in range(game.players):
            self.walk(game.default(), Player(p), 1, 1, self.regrets, self.strategies)

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
                R[action] += pmi * (cfs[action] - value)
                S[action] += pi * p

        return value
