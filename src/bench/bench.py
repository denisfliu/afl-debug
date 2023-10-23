from dataclasses import dataclass
from enum import Enum
from src.bench import compare
import argparse
import subprocess

class BinaryType(Enum):
    CUSTOM = 0
    XPDF = 1
    SLEEP = 2

@dataclass
class Bench:
    binary_type: BinaryType = BinaryType.XPDF
    afl_path: str
    custom_binary_dir: str = None
    time: int
    iterations: int
    input_dir: str
    output_dir: str

    def bench(self):
        self.exec_fuzz()
        # TODO: get output directory from config.yaml and pass to compare
        compare()

    def exec_fuzz(self, output_dir):
        print("Starting fuzzing process...")
        for i in range(self.iterations):
            try:
                subprocess.run(f"{self.afl_path} -i {self.input_dir} -o {self.output_dir}/{i} -- {self.custom_binary_dir} @@".split(), timeout=self.time+2) # 2 seconds for startup
            except subprocess.TimeoutExpired:
                continue
        print("Completed fuzzing process.")

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