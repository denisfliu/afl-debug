import subprocess
import os

from dataclasses import dataclass
from enum import Enum
from typing import Union
from omegaconf import DictConfig, ListConfig

from src.util import fancy_print
from src.fuzz import FuzzRunner


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
    output_dir: str
    input_dir: str
    force: bool = False
    double_force: bool = False
    write_results: bool = False

    def __post_init__(self):
        if self.binary_dir.lower() == "xpdf":
            self.binary_type = BinaryType.XPDF
            bin_config = self.config.bench.xpdf
        elif self.binary_dir.lower() == "sleep":
            self.binary_type = BinaryType.SLEEP
            bin_config = self.config.bench.sleep
        elif self.binary_dir.lower() == "objdump":
            self.binary_type = BinaryType.OBJDUMP
            bin_config = self.config.bench.objdump
        else:
            self.binary_type = BinaryType.CUSTOM

        if self.binary_type != BinaryType.CUSTOM:
            self.binary_dir = bin_config.bin_path
            if self.output_dir is None:
                self.output_dir = bin_config.output_path
            if self.input_dir is None:
                self.input_dir = bin_config.input_path

        self.base_dir = os.path.join(self.output_dir, "base")
        self.base_exists = not self.double_force and os.path.exists(
            os.path.join(self.base_dir, "default")
        )

        assert (
            self.binary_dir is not None
        ), "binary_dir cannot be None; must be specified by either config.yaml or input flags"
        assert (
            self.output_dir is not None
        ), "output_dir cannot be None; must be specified by either config.yaml or input flags"
        assert (
            self.input_dir is not None
        ), "input_dir cannot be None; must be specified by either config.yaml or input flags"

    def bench(self):
        saved_percentages = []
        self.__bench_asserts()

        # Create parent output directory (for benchmark runs) if it doesn't exist
        if not os.path.exists(self.output_dir):
            subprocess.run(f"mkdir {self.output_dir}".split())

        # Do base run
        if not self.base_exists:
            self.exec_fuzz(self.input_dir, self.base_dir, is_replay=False)

        # Do benchmark runs and save percentage similarities
        for i in range(self.iterations):
            fuzz_path = os.path.join(self.output_dir, f"bench{i}")
            percent, bad, total = self.exec_fuzz(
                self.input_dir, fuzz_path, is_replay=True
            )
            print(f"Benchmark {i}:")
            print(f"Percentage similarity: {(1 - percent) * 100}%\n")
            print(f"Correct/Total: {total - bad}/{total}\n")
            saved_percentages.append(1 - percent)

        # Print out similarities after all iterations completed
        fancy_print("PERCENTAGE SIMILARITY")
        for i in range(self.iterations):
            iter_path = os.path.join(self.output_dir, f"bench{i}")
            print(f"{self.base_dir} vs. {iter_path}: {saved_percentages[i]*100:.3f}%")

    def exec_fuzz(self, input_dir, output_dir, is_replay=True):
        fancy_print(f"Starting fuzzing process for {self.binary_dir}...")
        command = ""
        # TODO: this is kinda scuffed, probably best to add like a "format" variable with the default as "@@"
        # NOTE: -r {self.base_dir} is phased out
        if self.binary_type == BinaryType.OBJDUMP:
            command = f"{self.config.afl_path} -i {input_dir} -o {output_dir} -- {self.binary_dir} -d @@"
        else:
            command = f"{self.config.afl_path} -i {input_dir} -o {output_dir} -- {self.binary_dir} @@"
        if is_replay:
            return FuzzRunner(
                fuzz_command=command,
                base_dir=self.base_dir,
                is_replay=True,
                do_compare=True,
                time=self.time,
            ).run()
        else:
            return FuzzRunner(
                fuzz_command=command,
                base_dir=self.base_dir,
                is_replay=False,
                do_compare=False,
                time=self.time,
            ).run()

    def __bench_asserts(self):
        # Delete benchmark runs if they exist (AFL++ won't run otherwise)
        if self.double_force:
            bench_path = os.path.join(self.output_dir, "base")
            subprocess.run(f"rm -r {bench_path}".split())
        if os.path.exists(os.path.join(self.output_dir, "bench0")) and self.force:
            for i in range(self.iterations):
                bench_path = os.path.join(self.output_dir, f"bench{i}")
                subprocess.run(f"rm -r {bench_path}".split())
        assert not os.path.exists(
            os.path.join(self.output_dir, "bench0")
        ), f"Existing benchmark found at {self.output_dir}. Use --force to overwrite it."
        """
        assert os.path.exists(
            os.path.join(self.base_dir, "default")
        ), f"No fuzzing output found for the base run at {self.base_dir}."
        """
        assert os.path.exists(
            self.input_dir
        ), f"No input directory found at {self.input_dir}. Please verify your inputs."
        assert os.listdir(
            self.input_dir
        ), f"No valid seeds found at {self.input_dir}. Please verify your inputs."
