#!/usr/bin/env python3
import argparse
import sys
import os
import glob

from src.bench.compare import compare

PATH = "default/queue"
FILETEMPLATE = "id:"


def getfile(directory, number):
    files = glob.glob(f"{directory}{number:06}*")
    if len(files) == 0:
        return None
    elif len(files) > 1:
        print("Something is wrong, {files}")
        return None
    else:
        return files[0]


def same_content(file1, file2):
    with open(file1, "rb") as f:
        content1 = f.read()
    with open(file2, "rb") as f:
        content2 = f.read()
    if content1 == content2:
        return True
    else:
        return False


def compare(dir1, dir2):
    d1 = os.path.join(dir1, PATH)
    d2 = os.path.join(dir2, PATH)
    d1_len = len(
        [entry for entry in os.listdir(d1) if os.path.isfile(os.path.join(d1, entry))]
    )
    d2_len = len(
        [entry for entry in os.listdir(d2) if os.path.isfile(os.path.join(d2, entry))]
    )
    print(f"{d1} | Length: {d1_len}", f"{d2} | Length: {d2_len}", sep="\n")

    d1 = os.path.join(dir1, PATH, FILETEMPLATE)
    d2 = os.path.join(dir2, PATH, FILETEMPLATE)

    i = 0
    unidentical_count = 0
    unidentical_files = []
    first_files = []
    f1 = getfile(d1, i)
    f2 = getfile(d2, i)
    while (f1 is not None and f2 is not None) or i == 0:
        if i < 5:
            first_files.append((f1, f2))

        if not same_content(f1, f2):
            unidentical_files.append((f1, f2))
            unidentical_count += 1
        # else:
        #     print(f'{i:06}, Same')
        i += 1
        f1 = getfile(d1, i)
        f2 = getfile(d2, i)
    return unidentical_count / i, unidentical_count, i, unidentical_files, first_files


def print_files(files, prefix):
    for i, (f1, f2) in enumerate(files):
        print(f"{prefix} {i}:\n{f1}\n{f2}\n")


def main(args):
    """
    percentage, unidentical, total, files, first_files = compare(dir1, dir2)
    print(f"{unidentical} files differ out of {total} files\n")
    # print_files(first_files, 'File')
    # if percentage < .05:
    #    print_files(files, 'Difference')
    # print(f'{percentage * 100} percent of files differ')
    """
    print(compare(args.dir_a, args.dir_b))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--dir_a", type=str, required=True)
    parser.add_argument("-b", "--dir_b", type=str, default="~/outputs/", required=False)
    args = parser.parse_args()
    # print(args)
    main(args)
