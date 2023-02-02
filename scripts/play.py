from tqdm import tqdm

from typing import cast
import importlib
import pathlib
import argparse
import random

from zerosum.game import Player, Game, A_inv, I
from zerosum.algorithms.algo import Runner
from zerosum.pkr.abstraction.abstractions import Translation
from zerosum.pkr.game import Call, Check


def main():
    parser = argparse.ArgumentParser("cfr")
    parser.add_argument("--p1", type=str, required=True)
    parser.add_argument("--c1", type=pathlib.Path, required=True)
    parser.add_argument("--b1", action="store_true", default=False)
    parser.add_argument("--p2", type=str, required=True)
    parser.add_argument("--c2", type=pathlib.Path, required=True)
    parser.add_argument("--b2", action="store_true", default=False)
    parser.add_argument("-r", action="store_true", default=False)
    parser.add_argument("-n", type=int, required=True)
    args = parser.parse_args()

    if not args.b1:
        p1 = importlib.import_module(
            f".{args.p1}", package="zerosum.pkr.abstraction.versions"
        )
    else:
        p1 = importlib.import_module(f".{args.p1}", package="blood")

    if not args.b2:
        p2 = importlib.import_module(
            f".{args.p2}", package="zerosum.pkr.abstraction.versions"
        )
    else:
        p2 = importlib.import_module(f".{args.p2}", package="blood")

    s1 = Runner.load(args.c1, p1.Abstraction, 0, 0).impl.strategies
    s2 = Runner.load(args.c2, p2.Abstraction, 0, 0).impl.strategies

    payoffs, unknowns = [], [0, 0]
    for i in tqdm(range(args.n)):
        if i % 2:
            pf, unk = play(p1.Abstraction(), s1, p2.Abstraction(), s2, args.r)
        else:
            pf, unk = play(p2.Abstraction(), s2, p1.Abstraction(), s1, args.r)
            pf = -pf
        payoffs.append(pf)
        unknowns[0] += unk[0]
        unknowns[1] += unk[1]

    print(f"Mean: {sum(payoffs) / args.n}")
    print(f"Unknowns: {unknowns} ({[unknowns[0] / args.n, unknowns[1] / args.n]})")


def normalize(s):
    d = sum(s.values())
    if d > 0:
        return {k: v / d for k, v in s.items()}
    return {k: 1 / len(s) for k, v in s.items()}


def play(
    g1: Game[A_inv, I],
    p1: dict[I, dict[A_inv, float]],
    g2: Game[A_inv, I],
    p2: dict[I, dict[A_inv, float]],
    r: bool = False,
):
    unknowns = [0, 0]

    game = Translation()
    i = 0
    while not game.terminal:
        i += 1
        if i > 100:
            print(game)
            print()
            print(g1)
            print()
            print(g2)
            raise RuntimeError()

        if game.chance:
            action = game.sample()

        elif game.active == 0:
            iset = g1.infoset(g1.active)

            if iset in p1:
                s = p1[iset]
                action = max(s, key=s.__getitem__)
            else:
                unknowns[0] += 1
                action = random.choice(iset.actions())

        elif game.active == 1:
            iset = g2.infoset(g2.active)

            if iset in p2:
                s = normalize(p2[iset])
                if not r:
                    action = max(s, key=s.__getitem__)
                else:
                    (action,) = random.choices(list(s), weights=list(s.values()))
            else:
                unknowns[1] += 1
                action = random.choice(iset.actions())

        else:
            actions = game.infoset(game.active).actions()
            if Check() in actions:
                action = Check()
            elif Call() in actions:
                action = Call()
            else:
                raise RuntimeError()

        chance = game.chance
        game = game.apply(action)  # type: ignore
        action = game.history[-1]  # translated action

        if g1.chance == chance:
            g1 = g1.apply(action)  # type: ignore
        if g2.chance == chance:
            g2 = g2.apply(action)  # type: ignore

    p = cast(Player, 0)
    return game.payoff(p), unknowns
