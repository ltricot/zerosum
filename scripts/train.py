from typing import Callable
import importlib
import pathlib
import argparse

from zerosum.game import Game, A_inv, I
from zerosum.algorithms.algo import Implementation, Runner

# algorithms
from zerosum.algorithms.lcfr import ESLCFR
from zerosum.algorithms.escfr import ESCFR
from zerosum.algorithms.cfrplus import ESCFRP


FOREVER = 100000000000000
THRESHOLD = 300_000


def main():
    algos = {
        "LCFR": ESLCFR(THRESHOLD),
        "LCFR1M": ESLCFR(1_000_000),
        "ESCFR": ESCFR(),
        "CFR+": ESCFRP(),
    }

    parser = argparse.ArgumentParser("cfr")
    parser.add_argument("--abstraction", type=str, required=True)
    parser.add_argument("-b", "--blood", action="store_true", default=False)
    parser.add_argument("--checkpoint", type=pathlib.Path, required=True)
    parser.add_argument(
        "--algorithm", type=str, required=True, choices=list(algos.keys())
    )
    args = parser.parse_args()

    if not args.blood:
        abstraction = importlib.import_module(
            f".{args.abstraction}",
            package="zerosum.pkr.abstraction.versions",
        )
        game = abstraction.TrainingAbstraction
    else:
        abstraction = importlib.import_module(f".{args.abstraction}", package="blood")
        game = abstraction.TrainingAbstraction

    algo = algos[args.algorithm]
    train(game, algo, args.checkpoint)


def train(
    game: Callable[[], Game[A_inv, I]],
    impl: Implementation[A_inv, I],
    checkpt: pathlib.Path,
):
    runner = Runner(impl, game, checkpt, FOREVER, 1000)
    if checkpt.exists():
        runner = Runner.load(checkpt, game, FOREVER, 1000)

    try:
        runner.run()
    except KeyboardInterrupt:
        runner.save()
