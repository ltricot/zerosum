import numpy as np
import eval7

from collections import defaultdict
import re


def rangeof(log):
    rounds = []

    round = []
    for line in log.split("\n"):
        if not line:
            rounds.append(round)
            round = []
            continue

        round.append(line)

    table = defaultdict(list)
    for round in rounds[:700]:
        if len(round) < 3:
            continue

        if round[1].startswith("B posts"):
            hand = round[3][-7:]
            a, b = hand.strip("[]").split()
            a, b = eval7.Card(a), eval7.Card(b)

            ri, rj = a.rank, b.rank
            si, sj = a.suit, b.suit

            l, r = 12 - min(ri, rj), 12 - max(ri, rj)
            if si == sj:
                ix = l, r
            else:
                ix = r, l

            plays = 1 if "raises" in round[5] else 0.5 if "calls" in round[5] else 0
            plays = 1 if "folds" not in round[5] else 0
            table[ix].append(plays)

    tab = np.zeros((13, 13))
    for (i, j), v in table.items():
        tab[i, j] = np.mean(v)

    return tab


def curve(log):
    rounds = []

    round = []
    for line in log.split("\n"):
        if not line:
            rounds.append(round)
            round = []
            continue

        round.append(line)

    curve = []
    for round in rounds[:700]:
        if len(round) < 3:
            continue

        sco = re.search(r"A \((-?\d+)\)", round[0]).group(1)  # type: ignore
        curve.append(int(sco))

    return curve


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import sys

    log = sys.stdin.read()
    c = curve(log)
    plt.plot(c)
    plt.show()
    # tab = rangeof(log)

    # plt.matshow(tab)
    # plt.show()
