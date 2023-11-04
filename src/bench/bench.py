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
    time: int
    iterations: int
    binary_dir: str
    base_dir: str
    output_dir: str
    input_dir: str
    force: bool = False
    write_results: bool = False

    def __post_init__(self):
        if self.binary_dir.lower() == "xpdf":
            self.binary_type = BinaryType.XPDF
            self.binary_dir = self.config.bench.xpdf.bin_path
            if self.base_dir is None:
                self.base_dir = self.config.bench.xpdf.base_path
            if self.output_dir is None:
                self.output_dir = self.config.bench.xpdf.output_path
            if self.input_dir is None:
                self.input_dir = self.config.bench.xpdf.input_path
        elif self.binary_dir.lower() == "sleep":
            self.binary_type = BinaryType.SLEEP
            self.binary_dir = self.config.bench.sleep.bin_path
            if self.base_dir is None:
                self.base_dir = self.config.bench.sleep.base_path
            if self.output_dir is None:
                self.output_dir = self.config.bench.sleep.output_path
            if self.input_dir is None:
                self.input_dir = self.config.bench.sleep.input_path
        elif self.binary_dir.lower() == "objdump":
            self.binary_type = BinaryType.OBJDUMP
            self.binary_dir = self.config.bench.objdump.bin_path
            if self.base_dir is None:
                self.base_dir = self.config.bench.objdump.base_path
            if self.output_dir is None:
                self.output_dir = self.config.bench.objdump.output_path
            if self.input_dir is None:
                self.input_dir = self.config.bench.objdump.input_path
        else:
            self.binary_type = BinaryType.CUSTOM
        
        assert self.binary_dir is not None, "binary_dir cannot be None; must be specified by either config.yaml or input flags"
        assert self.base_dir is not None, "base_dir cannot be None; must be specified by either config.yaml or input flags"
        assert self.output_dir is not None, "output_dir cannot be None; must be specified by either config.yaml or input flags"
        assert self.input_dir is not None, "input_dir cannot be None; must be specified by either config.yaml or input flags"

    def bench(self):
        saved_percentages = []

        # Delete benchmark runs if they exist (AFL++ won't run otherwise)
        if os.path.exists(os.path.join(self.output_dir, "bench0")) and self.force:
            for i in range(self.iterations):
                bench_path = os.path.join(self.output_dir, f"bench{i}")
                subprocess.run(f"rm -r {bench_path}".split())
        assert not os.path.exists(
            os.path.join(self.output_dir, "bench0")
        ), f"Existing benchmark found at {self.output_dir}. Use --force to overwrite it."
        assert os.path.exists(
            os.path.join(self.base_dir, "default")
        ), f"No fuzzing output found for the base run at {self.base_dir}."
        assert os.path.exists(
            self.input_dir
        ), f"No input directory found at {self.input_dir}. Please verify your inputs."
        assert os.listdir(
            self.input_dir
        ), f"No valid seeds found at {self.input_dir}. Please verify your inputs."
        # Create parent output directory (for benchmark runs) if it doesn't exist
        if not os.path.exists(self.output_dir):
            subprocess.run(f"mkdir {self.output_dir}".split())

        # Do benchmark runs and save percentage similarities
        for i in range(self.iterations):
            fuzz_path = os.path.join(self.output_dir, f"bench{i}")
            self.exec_fuzz(self.input_dir, fuzz_path)
            percent, bad, total, _, _ = compare(self.base_dir, fuzz_path)
            print(f"Benchmark {i}:")
            print(f"Percentage similarity: {(1 - percent) * 100}%\n")
            print(f"Correct/Total: {total - bad}/{total}\n")
            saved_percentages.append(1 - percent)

        # Print out similarities after all iterations completed
        results_file = os.path.join(self.output_dir, self.config.bench.output_file)
        with open(results_file, "w") as f:
            fancy_print("PERCENTAGE SIMILARITY")
            f.write("-" * 15 + "\nPERCENTAGE SIMILARITY\n" + "-" * 15 + "\n")
            for i in range(self.iterations):
                iter_path = os.path.join(self.output_dir, f"bench{i}")
                print(
                    f"{self.base_dir} vs. {iter_path}: {saved_percentages[i]*100:.3f}%"
                )
                f.write(
                    f"{self.base_dir} vs. {iter_path}: {saved_percentages[i]*100:.3f}%\n"
                )

    # TODO: change this so it's more modular (we will need to implement different exec_fuzz functions for different fuzzers)
    def exec_fuzz(self, input_dir, output_dir):
        fancy_print(f"Starting fuzzing process for {self.binary_dir}...")
        try:
            # TODO: this is kinda scuffed, probably best to add like a "format" variable with the default as "@@"
            if self.binary_type == BinaryType.OBJDUMP:
                subprocess.run(
                    f"{self.config.afl_path} -i {input_dir} -o {output_dir} -r {self.base_dir} -- {self.binary_dir} -d @@".split(),
                    timeout=self.time + 2,
                )  # 2 seconds for startup
            else:
                subprocess.run(
                    f"{self.config.afl_path} -i {input_dir} -o {output_dir} -r {self.base_dir} -- {self.binary_dir} @@".split(),
                    timeout=self.time + 2,
                )  # 2 seconds for startup
        except subprocess.TimeoutExpired:
            fancy_print(
                f"Completed fuzzing process for {self.binary_dir}.\nResults in: {output_dir}"
            )


def main(args):
    print(args)
    config = get_config()
    b = Bench(
        config=config,
        time=(args.time if args.time is not None else config.bench.time),
        iterations=(args.iterations if args.iterations is not None else config.bench.iterations),
        binary_dir=args.binary_dir,
        base_dir=args.base_dir,
        output_dir=args.output_dir,
        input_dir=args.input_dir,
        force=args.force,
        write_results=args.write_results,
    )
    # print(b)
    b.bench()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.bench.bench -p [binary_path]")
        print("-t, --time : amount of time to run the benchmark for per run")
        print("-i, --iterations : number of iterations to run the benchmark")
        print("-p, --binary_dir : path to the program/binary fuzzed")
        print("-b, --base_dir : path to the base fuzz run directory")
        print("-o, --output_dir : path to the directory to place the benchmark runs in")
        print("-s, --input_dir : path to the directory with the seeds used in the base run")
        print("-f, --force : use the force flag to remove existing benchmark runs")
        print("-w, --write_results : write the similarity percentages to a file in output_dir")
        print("Binaries supported:")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--time", type=int, required=False)
    parser.add_argument("-i", "--iterations", type=int, required=False)
    parser.add_argument("-p", "--binary_dir", type=str, required=True)
    parser.add_argument("-b", "--base_dir", type=str, required=False)
    parser.add_argument("-o", "--output_dir", type=str, required=False)
    parser.add_argument("-s", "--input_dir", type=str, required=False)
    parser.add_argument("-f", "--force", action="store_true", required=False)
    parser.add_argument("-w", "--write_results", action="store_false", required=False)
    args = parser.parse_args()
    # print(args)
    main(args)
