from __future__ import annotations

from typing import TypeVar, Hashable, Generic, Protocol, cast
from typing import Type, Callable, Optional
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
    state: Callable[[InfoSet[A_inv]], H]
) -> AlgebraicStateAbstraction[A_inv, H]:
    class _Algebraic(AlgebraicStateAbstraction):
        def __call__(self, infoset: InfoSet[A_inv]) -> H:
            return state(infoset)

    _Algebraic.__name__ = state.__name__
    _Algebraic.__qualname__ = state.__qualname__

    return _Algebraic()


@dataclass(frozen=True)
class _ProductStateAbstraction(AlgebraicStateAbstraction[A_con, H]):
    abstractions: tuple[StateAbstraction, ...]

    def __call__(self, infoset: InfoSet[A_con]) -> Hashable:
        return tuple(a(infoset) for a in self.abstractions)


class ActionAbstraction(Protocol[A_inv]):
    # we want `I` to be _bounded_ by `InfoSet[A_cov]`
    # but I don't know how to specify that

    def __call__(self, infoset: InfoSet[A_inv]) -> tuple[A_inv, ...]:
        ...


class _InfoSet(Generic[A_cov]):
    __slots__ = (
        "_infoset",
        "state",
        "action",
        "_saved",
        "_saved_state",
        "_saved_actions",
    )

    _infoset: InfoSet[A_cov]
    state: StateAbstraction
    action: ActionAbstraction

    _saved: bool
    _saved_state: Optional[Hashable]
    _saved_actions: Optional[tuple[A_cov, ...]]

    def __init__(
        self,
        infoset: InfoSet[A_cov],
        state: StateAbstraction,
        action: ActionAbstraction,
    ):
        self._infoset = infoset
        self.state = state
        self.action = action
        self._saved = False
        self._saved_state = None
        self._saved_actions = None

    def actions(self) -> tuple[A_cov, ...]:
        if self._saved:
            return cast(tuple[A_cov, ...], self._saved_actions)
        return self.action(self._infoset)

    @property
    def _state(self):
        if self._saved:
            return self._saved_state
        return self.state(self._infoset)

    def __eq__(self, other: object):
        return isinstance(other, _InfoSet) and self._state == other._state

    def __hash__(self):
        return hash(self._state)

    def __repr__(self):
        return repr(self._state)

    def __getstate__(self):
        return self._state, self.actions()

    def __setstate__(self, state):
        state, actions = state
        object.__setattr__(self, "_saved", True)
        object.__setattr__(self, "_saved_state", state)
        object.__setattr__(self, "_saved_actions", actions)


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
            return dataclass(frozen=True)(_Abstracted)

        return _Abstracted

    return decorator
