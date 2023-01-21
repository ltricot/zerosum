from typing import Dict
import random

from .cfr import matching
from .game import Game, Player, I, A_inv


# not sure about correctness of this implementation
# for one, it is not vector form as the paper describes
# the only differences with external sampling cfr are:
# - the strategy updates are linearly weighted (as in linear CFR)
# - the regrets are clipped above 0 when the strategy is updated
#   (regret matching+ learner)


def eswalkplus(
    game: Game[A_inv, I],
    player: Player,
    regrets: Dict[I, Dict[A_inv, float]],
    strategies: Dict[I, Dict[A_inv, float]],
    t: int,
):
    if game.terminal:
        return game.payoff(player)

    if game.chance:
        action = game.sample()
        return eswalkplus(game.apply(action), player, regrets, strategies, t)

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
        value = eswalkplus(game.apply(action), player, regrets, strategies, t)

        for action, p in zip(actions, strategy):
            S[action] += t * p
            R[action] = max(0, R[action])

        return value

    cfs = {action: 0 for action in actions}
    value = 0

    for action, p in zip(actions, strategy):
        cf = eswalkplus(game.apply(action), player, regrets, strategies, t)
        cfs[action] = cf
        value += p * cf

    for action in actions:
        R[action] += cfs[action] - value

    return value
