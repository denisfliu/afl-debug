import argparse
import os
import subprocess

from src.bench.compare import compare
from src.utils import fancy_print


def copy(output_dir: str):
    os.popen(f"mkdir {output_dir}/replay")
    os.popen(f"mv /tmp/*.rep {output_dir}/replay/")


def main(args):
    command = args.fuzz_command.split()
    for i, val in enumerate(command):
        if val == "-o":
            afl_output_dir = command[i + 1]
            break

    if args.is_replay:
        # Set LD_PRELOAD for replay so file and run args.fuzz_command
        raise NotImplementedError
        if args.do_compare:
            percent, bad, total, _, _ = compare(args.base_dir, afl_output_dir)
            fancy_print(
                f"Percentage similarity: {(1 - percent) * 100}%\nCorrect/Total: {total - bad}/{total}\n"
            )
    else:
        # Set LD_PRELOAD for base so file and run args.fuzz_command
        raise NotImplementedError
        copy(afl_output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--is_replay", action="store_true")
    parser.add_argument("-c", "--do_compare", action="store_true")
    parser.add_argument(
        "-b",
        "--base_dir",
        type=str,
        default="INSERT BETTER DEFAULT HERE",
    )
    parser.add_argument(
        "c",
        "--fuzz_command",
        type=str,
        default="INSERT BETTER DEFAULT HERE",
        required=True,
    )
    args = parser.parse_args()
    assert not args.is_replay or args.base_dir is not None, "Replaying requires -b"
    # print(args)
    main(args)
