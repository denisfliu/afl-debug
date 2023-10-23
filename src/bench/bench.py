import argparse
import subprocess
import os

from dataclasses import dataclass
from enum import Enum
from typing import Union
from omegaconf import DictConfig, ListConfig

from src.bench import compare
from src.utils import get_config, fancy_print

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
    config: Union[DictConfig, ListConfig]

    def bench(self):
        base_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.bench.base_folder_path)
        output_path = os.path.join(self.config.fuzz.fuzz_folder, "outputs")
        assert not os.path.exists(os.path.join(output_path, "bench0")), f"Existing benchmark found at {output_path}."

        for i in range(self.iterations):
            fuzz_path = os.path.join(output_path, f"outputs/bench{i}")
            self.exec_fuzz(fuzz_path)
            compare(base_path, fuzz_path)

    # TODO: change this so it's more modular (we will need to implement different exec_fuzz functions for different fuzzers)
    def exec_fuzz(self, output_dir):
        fancy_print(f"Starting fuzzing process for {output_dir}...")
        try:
            subprocess.run(f"{self.config.afl_path} -i {self.input_dir} -o {output_dir} -- {self.custom_binary_dir} @@".split(), timeout=self.time+2) # 2 seconds for startup
        except subprocess.TimeoutExpired:
            fancy_print(f"Completed fuzzing process for {output_dir}.")

def main(args):
    config = get_config()
    Bench(binary_type=args.binary_type, custom_binary_dir=args.custom_binary_dir, time=args.time, iterations=args.iterations, output_dir=args.output_dir, config=config)
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