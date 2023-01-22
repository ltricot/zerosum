from __future__ import annotations

from typing import Protocol, TypeVar, Hashable, Generic
from typing import Tuple, Type, Callable
from dataclasses import dataclass, is_dataclass
import abc

from .game import InfoSet, A_cov, A_inv, I, Game, Player


A_con = TypeVar("A_con", contravariant=True)


class StateAbstraction(Protocol[A_con]):
    def __call__(self, infoset: InfoSet[A_con]) -> Hashable:
        ...


H = TypeVar("H", bound=Hashable)


class AlgebraicStateAbstraction(StateAbstraction[A_con], Generic[A_con, H], abc.ABC):
    def __mul__(self, other: StateAbstraction) -> AlgebraicStateAbstraction:
        # vital to combine into single product instance, otherwise performance
        # suffers greatly due to the explosion in function calls
        if isinstance(self, _ProductStateAbstraction):
            if isinstance(other, _ProductStateAbstraction):
                return _ProductStateAbstraction(self.abstractions + other.abstractions)
            return _ProductStateAbstraction(self.abstractions + (other,))
        if isinstance(other, _ProductStateAbstraction):
            return _ProductStateAbstraction((self,) + other.abstractions)
        return _ProductStateAbstraction((self, other))

    @abc.abstractmethod
    def __call__(self, infoset: InfoSet[A_con]) -> H:
        ...


def algebraic(
    state: Callable[[InfoSet[A_con]], H]
) -> AlgebraicStateAbstraction[A_con, H]:
    class _Algebraic(AlgebraicStateAbstraction):
        def __call__(self, infoset: InfoSet[A_con]) -> H:
            return state(infoset)

    _Algebraic.__name__ = state.__name__
    _Algebraic.__qualname__ = state.__qualname__

    return _Algebraic()


@dataclass(slots=True, frozen=True)
class _ProductStateAbstraction(AlgebraicStateAbstraction[A_con, H]):
    abstractions: Tuple[StateAbstraction, ...]

    def __call__(self, infoset: InfoSet[A_con]) -> Hashable:
        return tuple(a(infoset) for a in self.abstractions)


class ActionAbstraction(Protocol[A_inv]):
    # we want `I` to be _bounded_ by `InfoSet[A_cov]`
    # but I don't know how to specify that

    def __call__(self, infoset: InfoSet[A_inv]) -> Tuple[A_inv, ...]:
        ...


@dataclass(slots=True, frozen=True)
class _InfoSet(Generic[A_cov]):
    _infoset: InfoSet[A_cov]
    state: StateAbstraction
    action: ActionAbstraction

    def actions(self) -> Tuple[A_cov, ...]:
        return self.action(self._infoset)

    @property
    def _state(self):
        return self.state(self._infoset)

    def __eq__(self, other: object):
        return isinstance(other, _InfoSet) and self._state == other._state

    def __hash__(self):
        return hash(self._state)

    def __repr__(self):
        return repr(self._state)


def abstract(
    game: Type[Game[A_inv, I]],
    states: StateAbstraction[A_inv],
    actions: ActionAbstraction[A_inv],
) -> Callable[[Type[Game[A_inv, I]]], Type[Game[A_inv, I]]]:
    def decorator(cls: Type[Game[A_inv, I]]) -> Type[Game[A_inv, I]]:
        class _Abstracted(cls):  # type: ignore
            def infoset(self, player: Player) -> _InfoSet:
                return _InfoSet(game.infoset(self, player), states, actions)

        _Abstracted.__name__ = cls.__name__
        _Abstracted.__qualname__ = cls.__qualname__
        if is_dataclass(cls):
            return dataclass(slots=True, frozen=True)(_Abstracted)

        return _Abstracted

    return decorator
