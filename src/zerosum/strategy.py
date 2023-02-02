# something of an outdated file to run local tournaments
# unused

from tqdm import tqdm

from typing import Protocol, Generic, cast
from typing import Callable
from dataclasses import dataclass
import itertools
import math
import abc

from .game import Player, Game, A_inv, I


class Strategy(Protocol[A_inv, I]):
    def round(self):
        ...

    def payoff(self, payoff: float):
        ...

    def apply(self, action: A_inv):
        ...

    def act(self, game: Game[A_inv, I]) -> A_inv:
        ...


@dataclass
class Leader(Generic[A_inv, I], abc.ABC):
    strategies: dict[I, dict[A_inv, float]]
    game: Callable[[], Game[A_inv, I]]

    def round(self):
        self.instance = self.game()

    def payoff(self, payoff: int):
        ...

    def apply(self, action: A_inv):
        self.instance = self.instance.apply(action)

    @abc.abstractmethod
    def default(self, game: Game[A_inv, I]) -> A_inv:
        # a necessary consequence of action translation
        ...

    @abc.abstractmethod
    def translate(self, game: Game[A_inv, I], action: A_inv) -> A_inv:
        # action translation
        ...

    def act(self, game: Game[A_inv, I]) -> A_inv:
        return self.translate(game, self._act(game))

    def _act(self, game: Game[A_inv, I]) -> A_inv:
        if self.instance.terminal or self.instance.chance:
            return self.default(game)

        assert self.instance.active == game.active
        assert self.instance.chance == game.chance == False

        infoset = self.instance.infoset(self.instance.active)
        if infoset not in self.strategies:
            return self.default(game)

        strategy = self.strategies.get(infoset, {})
        return max(strategy, key=strategy.__getitem__)


def play(game: Game[A_inv, I], p0: Strategy[A_inv, I], p1: Strategy[A_inv, I]):
    players = (p0, p1)

    p0.round()
    p1.round()

    while not game.terminal:
        if game.chance:
            action = game.sample()

        else:
            player = players[game.active]
            action = player.act(game)

        game = game.apply(action)
        p0.apply(action)
        p1.apply(action)

    # only zero sums
    payoff = game.payoff(cast(Player, 0))
    p0.payoff(payoff)
    p1.payoff(-payoff)

    return payoff


def match(
    game: Callable[[], Game[A_inv, I]],
    p0: Strategy[A_inv, I],
    p1: Strategy[A_inv, I],
    n: int,
):
    bankroll = 0
    for _ in range(n // 2):
        bankroll += play(game(), p0, p1)
        bankroll -= play(game(), p1, p0)
    return bankroll


@dataclass
class Tournament(Generic[A_inv, I]):
    game: Callable[[], Game[A_inv, I]]
    players: tuple[Callable[[], Strategy[A_inv, I]], ...]
    n: int

    def __post_init__(self):
        self.elos: list[int] = [1000] * len(self.players)
        self.wins: list[int] = [0] * len(self.players)

    def update(self, i, j, win):
        ri = 10 ** (self.elos[i] / 400)
        rj = 10 ** (self.elos[j] / 400)
        ei, ej = ri / (ri + rj), rj / (ri + rj)

        ri = ri + 32 * (win - ei)
        rj = rj + 32 * (1 - win - ej)

        self.elos[i] = round(math.log10(ri) * 400)
        self.elos[j] = round(math.log10(rj) * 400)

        if win == 1:
            self.wins[i] += 1
        elif win == 0:
            self.wins[j] += 1

    def round(self, i: int, j: int):
        si, sj = self.players[i](), self.players[j]()
        payoff = match(self.game, si, sj, self.n)
        return 1 if payoff > 0 else 0.5 if payoff == 0 else 0

    def turn(self):
        combinations = list(itertools.combinations(range(len(self.players)), 2))

        for (i, j) in tqdm(combinations):
            if i != j:
                win = self.round(i, j)
                self.update(i, j, win)
