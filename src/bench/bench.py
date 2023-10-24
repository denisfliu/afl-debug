import argparse
import subprocess
import os
import sys

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
    time: int
    iterations: int
    config: Union[DictConfig, ListConfig]
    binary_type: BinaryType = BinaryType.XPDF
    custom_binary_dir: str = None

    def bench(self):
        base_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.bench.base_folder_path)
        output_path = os.path.join(self.config.fuzz.fuzz_folder, "outputs")
        inputs_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.fuzz.inputs)
        assert not os.path.exists(os.path.join(output_path, "bench0")), f"Existing benchmark found at {output_path}."
        assert os.path.exists(inputs_path), f"No input directory found at {inputs_path}. Please verify your inputs."
        assert os.listdir(inputs_path), f"No valid seeds found at {inputs_path}. Please verify your inputs."
        if not os.path.exists(output_path):
            subprocess.run(f"mkdir {output_path}".split())

        for i in range(self.iterations):
            fuzz_path = os.path.join(output_path, f"outputs/bench{i}")
            self.exec_fuzz(inputs_path, fuzz_path)
            compare(base_path, fuzz_path)

    # TODO: change this so it's more modular (we will need to implement different exec_fuzz functions for different fuzzers)
    def exec_fuzz(self, input_dir, output_dir):
        fancy_print(f"Starting fuzzing process for {self.config.afl_path}...")
        try:
            if self.custom_binary_dir is not None:
                subprocess.run(f"sudo {self.config.afl_path} -i {input_dir} -o {output_dir} -- {self.custom_binary_dir} @@".split(), timeout=self.time+2) # 2 seconds for startup
            else:
                binary_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.fuzz.binary)
                subprocess.run(f"sudo {self.config.afl_path} -i {input_dir} -o {output_dir} -- {binary_path} @@".split(), timeout=self.time+2) # 2 seconds for startup
        except subprocess.TimeoutExpired:
            fancy_print(f"Completed fuzzing process for {self.config.afl_path}.\nResults in: {output_dir}")

def main(args):
    config = get_config()
    b = Bench(binary_type=args.binary_type, custom_binary_dir=args.custom_binary_dir, time=args.time, iterations=args.iterations, config=config)
    print(b.bench)
    print(type(b.bench))
    

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python -m src.bench.bench -b [# of binary] -t [time] -i [iterations]")
        print("Binaries supported:")
        sys.exit(1)
    
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
        required=False
    )
    args = parser.parse_args()
    main(args)