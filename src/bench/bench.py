import argparse
import subprocess
import os
import sys

from dataclasses import dataclass
from enum import Enum
from typing import Union
from omegaconf import DictConfig, ListConfig

from src.bench.compare import compare
from src.utils import get_config, fancy_print

class BinaryType(Enum):
    CUSTOM = 0
    XPDF = 1
    SLEEP = 2
    OBJDUMP = 3

@dataclass
class Bench:
    config: Union[DictConfig, ListConfig]
    binary_type: BinaryType
    time: int
    iterations: int
    custom_binary_dir: str = None
    base_run: str = None
    force: bool = False
    
    def bench(self):
        base_path = self.base_run if self.base_run != None else os.path.join(self.config.fuzz.fuzz_folder, self.config.bench.base_folder_path)
        output_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.bench.output_path)
        inputs_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.fuzz.inputs)
        results_file = os.path.join(output_path, self.config.bench.output_file)
        saved_percentages = []
        
        # Delete benchmark runs if they exist (AFL++ won't run otherwise)
        if os.path.exists(os.path.join(output_path, "bench0")) and self.force:
            for i in range(self.iterations):
                bench_path = os.path.join(output_path, f"bench{i}")
                subprocess.run(f"rm -r {bench_path}".split())
        assert not os.path.exists(os.path.join(output_path, "bench0")), f"Existing benchmark found at {output_path}. Use --force to overwrite it."
        assert os.path.exists(os.path.join(base_path, "default")), f"No fuzzing output found for the base run at {base_path}."
        assert os.path.exists(inputs_path), f"No input directory found at {inputs_path}. Please verify your inputs."
        assert os.listdir(inputs_path), f"No valid seeds found at {inputs_path}. Please verify your inputs."
        if not os.path.exists(output_path):
            subprocess.run(f"mkdir {output_path}".split())
        # TODO: Ask for base run

        for i in range(self.iterations):
            fuzz_path = os.path.join(output_path, f"bench{i}")
            self.exec_fuzz(inputs_path, fuzz_path)
            percent, bad, total, _, _ = compare(base_path, fuzz_path)
            print(f"Percentage similarity: {(1 - percent) * 100}\n")
            saved_percentages.append(1 - percent)
        
        # Print out similarities after all iterations completed
        with open(results_file, "w") as f:
            fancy_print("PERCENTAGE SIMILARITY")
            f.write("-" * 15 + "\nPERCENTAGE SIMILARITY\n" + "-" * 15 + "\n")
            for i in range(self.iterations):
                iter_path = os.path.join(output_path, f"bench{i}")
                print(f"{base_path} vs. {iter_path}: {saved_percentages[i]*100:.3f}%")
                f.write(f"{base_path} vs. {iter_path}: {saved_percentages[i]*100:.3f}%\n")

    # TODO: change this so it's more modular (we will need to implement different exec_fuzz functions for different fuzzers)
    def exec_fuzz(self, input_dir, output_dir):
        fancy_print(f"Starting fuzzing process for {self.config.fuzz.binary}...")
        try:
            if self.custom_binary_dir is not None:
                subprocess.run(f"{self.config.afl_path} -i {input_dir} -o {output_dir} -- {self.custom_binary_dir} @@".split(), timeout=self.time+2) # 2 seconds for startup
            else:
                binary_path = os.path.join(self.config.fuzz.fuzz_folder, self.config.fuzz.binary)
                subprocess.run(f"{self.config.afl_path} -i {input_dir} -o {output_dir} -- {binary_path} @@".split(), timeout=self.time+2) # 2 seconds for startup
        except subprocess.TimeoutExpired:
            fancy_print(f"Completed fuzzing process for {self.config.fuzz.binary}.\nResults in: {output_dir}")

def main(args):
    config = get_config()
    b = Bench(config=config, binary_type=args.binary_type, time=args.time, iterations=args.iterations, custom_binary_dir=args.custom_binary_dir, base_run=args.base_run, force=args.force)
    b.bench()
    

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python -m src.bench.bench -b [# of binary] -t [time] -i [iterations]")
        print("Binaries supported:")
        sys.exit(1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--binary_type", type=int, required=True)
    parser.add_argument("-t", "--time", type=int, required=True)
    parser.add_argument("-i", "--iterations", type=int, required=True)
    parser.add_argument("-c", "--custom_binary_dir", type=str, required=False)
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default="~/outputs/",
        required=False
    )
    parser.add_argument("-r", "--base_run", type=str, required=False)
    parser.add_argument("-f", "--force", action='store_true', required=False)
    args = parser.parse_args()
    # print(args)
    main(args)