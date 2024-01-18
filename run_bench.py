import argparse
import sys

from src.util import get_config
from src.bench.bench import Bench


def main(args):
    print(args)
    config = get_config()
    b = Bench(
        config=config,
        time=(args.time if args.time is not None else config.bench.time),
        iterations=(
            args.iterations if args.iterations is not None else config.bench.iterations
        ),
        binary_dir=args.binary_dir,
        output_dir=args.output_dir,
        input_dir=args.input_dir,
        force=args.force,
        double_force=args.double_force,
        write_results=args.write_results,
    )
    # print(b)
    b.bench()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.bench.bench -p [binary_path]")
        print("-t, --time : amount of time to run the benchmark for per run")
        print("-i, --iterations : number of iterations to run the benchmark")
        print(
            "-b, --binary_dir : xpdf/objdump/sleep OR path to the program/binary fuzzed"
        )
        print("-o, --output_dir : path to the directory to place the benchmark runs in")
        print(
            "-s, --input_dir : path to the directory with the seeds used in the base run"
        )
        print("-f, --force : use the force flag to remove existing benchmark runs")
        print("-ff, --double_force : use the force flag to remove existing base run")
        print(
            "-w, --write_results : write the similarity percentages to a file in output_dir"
        )
        print("Binaries supported:")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--time", type=int, required=False)
    parser.add_argument("-i", "--iterations", type=int, required=False)
    parser.add_argument("-b", "--binary_dir", type=str, required=True)
    parser.add_argument("-o", "--output_dir", type=str, required=False)
    parser.add_argument("-s", "--input_dir", type=str, required=False)
    parser.add_argument("-f", "--force", action="store_true", required=False)
    parser.add_argument("-ff", "--double_force", action="store_true", required=False)
    parser.add_argument("-w", "--write_results", action="store_false", required=False)
    args = parser.parse_args()
    # print(args)
    main(args)
