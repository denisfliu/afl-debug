import argparse

from src.bench.compare import compare


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--dir_a", type=str, required=True)
    parser.add_argument(
        "-b", "--dir_b", type=str, default="~/outputs/", required=False
    )
    args = parser.parse_args()
    # print(args)
    print(compare(args.dir_a, args.dir_b))
