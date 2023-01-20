from typing import Dict
import random

from .cfr import matching
from .game import Game, Player, I, A_inv


def eswalk(
    game: Game[A_inv, I],
    player: Player,
    regrets: Dict[I, Dict[A_inv, float]],
    strategies: Dict[I, Dict[A_inv, float]],
):
    if game.terminal:
        return game.payoff(player)

    if game.chance:
        chances = game.chances()
        (action,) = random.choices(list(chances.keys()), weights=list(chances.values()))
        return eswalk(game.apply(action), player, regrets, strategies)

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
        value = eswalk(game.apply(action), player, regrets, strategies)

        for action, p in zip(actions, strategy):
            S[action] += p

        return value

    cfs = {action: 0 for action in actions}
    value = 0

    for action, p in zip(actions, strategy):
        cf = eswalk(game.apply(action), player, regrets, strategies)
        cfs[action] = cf
        value += p * cf

    for action in actions:
        R[action] += cfs[action] - value

    return value
