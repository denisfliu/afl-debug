import argparse
from src.fuzz import FuzzRunner

def main(args):
    FuzzRunner(
        fuzz_command=args.fuzz_command,
        base_dir=args.base_dir,
        is_replay=args.is_replay,
        do_compare=args.do_compare
    ).run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--is_replay", action="store_true")
    parser.add_argument("-p", "--print_compare", action="store_true")
    parser.add_argument(
        "-b",
        "--base_dir",
        type=str,
        default="INSERT BETTER DEFAULT HERE",
    )
    parser.add_argument(
        "-c",
        "--fuzz_command",
        type=str,
        default="INSERT BETTER DEFAULT HERE",
        required=True,
    )
    args = parser.parse_args()
    assert not args.is_replay or args.base_dir is not None, "Replaying requires -b"
    # print(args)
    main(args)
