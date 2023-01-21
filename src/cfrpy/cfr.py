from typing import List, Dict

from .game import Game, Player, A_inv, I


def matching(regrets: List[float]):
    regrets = [max(0, r) for r in regrets]
    denom = sum(regrets)

    if denom > 0:
        return [r / denom for r in regrets]

    return [1 / len(regrets)] * len(regrets)


def walk(
    game: Game[A_inv, I],
    player: Player,
    p0: float,
    p1: float,
    regrets: Dict[I, Dict[A_inv, float]],
    strategies: Dict[I, Dict[A_inv, float]],
    t: int,
):
    if p0 == p1 == 0:
        return 0

    if game.terminal:
        return game.payoff(player)

    if game.chance:
        value = 0
        for action, p in game.chances().items():
            p0p = p0 if player == 0 else p0 * p
            p1p = p1 if player == 1 else p1 * p
            value += p * walk(
                game.apply(action), player, p0p, p1p, regrets, strategies, t
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
        cf = walk(game.apply(action), player, p0p, p1p, regrets, strategies, t)

        cfs[action] = cf
        value += p * cf

    pi, pmi = p0, p1
    if player == 1:
        pi, pmi = p1, p0

    if game.active == player:
        for action, p in zip(actions, strategy):
            R[action] += pmi * (cfs[action] - value)
            S[action] += t * (pi * p)

    return value
