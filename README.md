# Zero sum games

## Games

Imperfect information games are classes which follow the following protocol ([game.py](src/zerosum/game.py)):

```python
class Game(Protocol[A_inv, I]):
    @property
    def terminal(self) -> bool:
        ...

    def payoff(self, player: Player) -> float:
        ...

    @property
    def chance(self) -> bool:
        ...

    # unnecessary for Monte Carlo CFR algorithms
    def chances(self) -> dict[A_inv, float]:
        ...

    # chance sampling - useful for Monte Carlo algorithms
    def sample(self) -> A_inv:
        ...

    @property
    def active(self) -> Player:
        ...

    def infoset(self, player: Player) -> I:
        ...

    def apply(self, action: A_inv) -> Game[A_inv, I]:
        ...
```

Notice the `apply()` method returns a new game instance rather than modifying the instance in place. This is very useful when traversing the game tree. Game instances should be immutable objects which represent the game state.

The `infoset()` method returns an object which contains all the information the active player has when it is their turn to act. It will become obvious why it is useful to make the information set explicit in our code when we start looking at action abstractions. The infoset object has the following interface:

```python
class InfoSet(Hashable, Protocol[A_cov]):
    def actions(self) -> tuple[A_cov, ...]:
        ...
```

The `actions()` method returns a tuple of all the actions the active player can take at the current game tree node.

## Abstractions

The Kuhn Poker game comes with an example of an [abstraction](zerosum/kuhn/abstraction.py). Notice it comes in the form of a simple subclass !

We now develop the concept of abstractions much further. Intuitively, a state abstraction is simply the game you obtain by hiding some usually available information from the players. Essentially, some situations become undistinguishable, although they were different in the original game. In poker, you can tell the player the ranks of his cards and whether they are suited, but hide their colors. This is an abstraction which reduces the amount of starting hands from 1326 to 169. An action abstraction forbids you from taking certain actions. Together, these ideas help create smaller game trees for which we can find Nash equilibria using a CFR implementation.

One can impose a monoidal structure on the set of abstractions of a game. Letting A and B be different abstractions, A * B is the smallest abstraction which allows to differentiate between information sets whenever either A or B allows it. The identity element of the monoid is the trivial abstraction, which gives no information. We call this idea algebraic abstractions. In practice we develop algebraic abstractions as objects which give access to a subset of the information available in an infoset.

The elegance of this idea is best illustrated through a collection of examples taken from [blood/basic.py](blood/basic.py):

```python
@algebraic
def street(infoset: PInfoSet):
    return len(cast(InfoSet, infoset).community)


def linearcost(acc: int):
    @algebraic
    def linearcost(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        cost = abs(infoset.pips[0] - infoset.pips[1])
        pot = infoset.pot + sum(infoset.pips)
        return round(cost / pot * acc)

    return linearcost


@algebraic
def player(infoset: PInfoSet):
    return cast(InfoSet, infoset).player


def linearpot(acc: int):
    @algebraic
    def linearpot(infoset: PInfoSet):
        infoset = cast(InfoSet, infoset)
        pot = infoset.pot + sum(infoset.pips)
        return round(pot / 800 * acc)

    return linearpot
```

The `@algebraic` decorator marks a function as being a state abstraction, which follows the following protocol:

```python
class StateAbstraction(Protocol[A_con]):
    def __call__(self, infoset: InfoSet[A_con]) -> Hashable:
        ...
```

Algebraic abstractions can then be multiplied together to form a new abstraction:

```python
from dataclasses import dataclass

from zerosum.abstraction import abstract
from zerosum.pkr.abstraction.abstractions import Translation, capped_bets
from zerosum.pkr.game import RiverOfBlood

from .basic import run, street, player, linearpot, basic, equities


actions = capped_bets(basic, 8)
cards = equities((8,) + (40,) * 7, dimension=50, maxiter=30)
states = run * street * player * linearpot(20) * cards * actions


@abstract(Translation, states, actions)
@dataclass(frozen=True)
class Abstraction(Translation):
    ...


@abstract(RiverOfBlood, states, actions)
@dataclass(frozen=True)
class TrainingAbstraction(RiverOfBlood):
    ...
```

The basic betting abstraction used in the above code is simply defined as follows:
```python
@algebraic
def basic(infoset: PInfoSet):
    infoset = cast(InfoSet, infoset)
    lb, ub = infoset._bounds()

    pot = infoset.pot + sum(infoset.pips)
    stack = infoset.stacks[infoset.player] - infoset.pips[infoset.player]

    bets = []
    if lb <= pot // 2 <= ub:
        bets.append(RaiseHalfPot())
    if lb <= pot <= ub:
        bets.append(RaisePot())
    if lb <= stack <= ub:
        bets.append(Allin())

    return tuple(bets)
```

## Don't read the CFR papers ; find slides

CFR is really a collection of regret learners, each associated to an information set. Starting from there we'd like to let each of them learn independently what to do in each situation. The only complication comes from the fact that information sets contain game tree nodes which won't be reached with uniform probability, because the other players can distinguish between nodes which are equivalent from the player's point of view.

A regret learner selects an action, is rewarded, and updates its strategy accordingly. It knows nothing of how the rewarded is computed. In our case it seems the reward is computed by letting the player and its opponent finish the game. This isn't quite true: unlike perfect information games, the reward also depends on the past (so to speak). We can model the regret learner's game by bringing the past in the future: that is, after the learner selects an action, one of the game tree nodes of the information set is sampled and the game continues until it yields a reward. The probability distribution over the game tree nodes in the information set depends on the strategies of the other players (chance, and the opponent !). CFR is the algorithm we use to compute this distribution.

Some variants of CFR are implemented in `zerosum.algorithms`:
- Vanilla CFR
- External Sampling MCCFR
- External Sampling MCCFR with regret-matching+ instead of vanilla regret matching
- External Sampling MCCFR with linear discounting of regrets and the average strategy

In practice the latter variant worked well.