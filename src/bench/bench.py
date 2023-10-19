from dataclasses import dataclass
from enum import Enum
from src.compare import compare
import argparse

class BinaryType(Enum):
    CUSTOM = 0
    XPDF = 1
    SLEEP = 2

@dataclass
class Bench:
    binary_type: BinaryType = BinaryType.XPDF
    custom_binary_dir: str = None
    time: int
    iterations: int
    output_dir: str

    def bench(self):
        for _ in range(self.iterations):
            self.exec_fuzz()

    def exec_fuzz(self, output_dir):
        raise NotImplementedError 


def main(args):
    Bench(binary_type=args.binary_type, custom_binary_dir=args.custom_binary_dir, time=args.time, iterations=args.iterations, output_dir=args.output_dir)
    Bench.bench()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--binary_type", type=int, required=True)
    parser.add_argument("-c", "--custom_binary_dir", type=str, required=False)
    parser.add_argument("-t", "--time", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, required=True)
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default="[INSERT DEFAULT HERE]",
    )
    args = parser.parse_args()
    main(args)