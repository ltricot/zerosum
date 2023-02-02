from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

from typing import Generic, Protocol
from typing import Callable, Optional
from dataclasses import dataclass
import pathlib
import pickle

from ..game import Game, A_inv, I


class Implementation(Protocol[A_inv, I]):
    @property
    def regrets(self) -> dict[I, dict[A_inv, float]]:
        ...

    @property
    def strategies(self) -> dict[I, dict[A_inv, float]]:
        ...

    @property
    def touched(self) -> int:
        # how many nodes touched
        ...

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        ...


@dataclass
class Algorithm(Generic[A_inv, I]):
    impl: Implementation[A_inv, I]
    game: Callable[[], Game[A_inv, I]]

    def once(self):
        self.impl._run_iteration(self.game)


@dataclass
class Runner(Generic[A_inv, I]):
    impl: Implementation[A_inv, I]
    game: Callable[[], Game[A_inv, I]]

    path: str | pathlib.Path
    until: int
    checkpt: Optional[int] = None

    logging: int = 10

    def run(self):
        impl, game = self.impl, self.game
        checkpt = self.checkpt

        for it in range(self.until):
            impl._run_iteration(game)

            if not it % self.logging:
                logger.info(
                    "iteration",
                    it=it,
                    touched=impl.touched,
                    infosets=len(impl.regrets),
                )

            if checkpt is not None and not (1 + it) % checkpt:
                self.save()

    def save(self):
        logger.info(f"saving to {self.path}")
        with open(self.path, "wb") as f:
            pickle.dump(self.impl, f)

    @classmethod
    def load(
        cls,
        path: str | pathlib.Path,
        game: Callable[[], Game[A_inv, I]],
        until: int,
        checkpt: Optional[int] = None,
    ):
        with open(path, "rb") as f:
            impl = pickle.load(f)

        return cls(impl, game, path, until, checkpt)
