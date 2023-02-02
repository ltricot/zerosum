import numpy as np
import eval7

from collections import defaultdict
from itertools import combinations

from blood.basic import preflop
from ..game import RiverOfBlood, Draw


Card = eval7.Card
_cards = eval7.Deck().cards


label = {}

for i, j in combinations(range(52), 2):
    g = RiverOfBlood().apply(Draw((i, j))).apply(Draw((i, j)))
    iset = g.infoset(g.active)
    label[i, j] = preflop(iset)

clusters = defaultdict(list)
for (i, j), l in label.items():
    clusters[l].append((_cards[i], _cards[j]))

villains = list(map(tuple, clusters.values()))
del clusters, label


def ochs(hand: tuple[Card, Card], community: tuple[Card, ...]):
    hist = np.empty(len(villains))
    for i, cluster in enumerate(villains):
        strength = 0
        for villain in cluster:
            strength += eval7.ochs(hand, villain, community, 100) / len(cluster)
        hist[i] = strength
    return hist
