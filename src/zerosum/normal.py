from dataclasses import dataclass
from typing import TypeVar
from typing import ClassVar, NoReturn
import abc

from .game import Player


Matrix = tuple[tuple[tuple[float, float], ...], ...]
ZSMatrix = tuple[tuple[float, ...], ...]


def normal(matrix: Matrix):
    @dataclass(slots=True, frozen=True)
    class Normal(NormalForm):
        _matrix = matrix
        _ns = (len(matrix), len(matrix[0]))

    return Normal


def zerosum(matrix: ZSMatrix):
    return normal(tuple(tuple((x, -x) for x in row) for row in matrix))


@dataclass(slots=True, frozen=True)
class InfoSet:
    player: Player
    n: int

    def actions(self):
        return tuple(range(self.n))


_T = TypeVar("_T", bound="NormalForm")


@dataclass(slots=True, frozen=True)
class NormalForm:
    players: ClassVar[int] = 2

    history: tuple[int, ...] = ()

    @property
    @abc.abstractmethod
    def _matrix(self) -> Matrix:
        ...

    @property
    @abc.abstractmethod
    def _ns(self) -> tuple[int, int]:
        ...

    @classmethod
    def default(cls: type[_T]) -> _T:
        return cls()

    @property
    def terminal(self):
        return len(self.history) == 2

    def payoff(self, player: int) -> float:
        i, j = self.history
        return self._matrix[i][j][player]

    @property
    def chance(self) -> bool:
        return False

    def chances(self) -> NoReturn:
        raise NotImplementedError

    def sample(self) -> NoReturn:
        raise NotImplementedError

    @property
    def active(self) -> Player:
        return Player(len(self.history))

    def infoset(self, player: Player):
        return InfoSet(player, self._ns[player])

    def apply(self, action: int):
        return self.__class__(self.history + (action,))
