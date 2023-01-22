from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

from typing import Protocol, Generic
from typing import Callable, Dict, Optional
from dataclasses import dataclass
import itertools
import pickle

from ..game import Game, A_inv, I


class Implementation(Protocol[A_inv, I]):
    @property
    def regrets(self) -> Dict[I, Dict[A_inv, float]]:
        ...

    @property
    def strategies(self) -> Dict[I, Dict[A_inv, float]]:
        ...

    @property
    def touched(self) -> int:
        # how many nodes touched
        ...

    def _run_iteration(self, game: Callable[[], Game[A_inv, I]]):
        ...


@dataclass
class Runner(Generic[A_inv, I]):
    impl: Implementation[A_inv, I]
    game: Callable[[], Game[A_inv, I]]

    pattern: str
    until: int
    checkpt: Optional[int] = None

    def run(self):
        impl, game = self.impl, self.game
        checkpt = self.checkpt

        for it in range(self.until):
            impl._run_iteration(game)

            if not it % 10:
                logger.info(
                    "iteration",
                    it=it,
                    touched=impl.touched,
                    infosets=len(impl.regrets),
                )

            if checkpt is not None and not (1 + it) % checkpt:
                logger.info(f"saving to {self.pattern.format((1 + it) // checkpt)}")
                self.save((1 + it) // checkpt)

    def save(self, it: int):
        path = self.pattern.format(it)
        with open(path, "wb") as f:
            progress = (self.impl.regrets, self.impl.strategies)
            pickle.dump(progress, f)
