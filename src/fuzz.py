import os
import subprocess
from typing import Tuple

from src.bench.compare import compare
from src.util import fancy_print

class FuzzRunner:
    """
    Class which runs fuzzers with the corresponding LD_PRELOAD stuff from src.components
    """
    def __init__(self, fuzz_command: str, base_dir: str = None, is_replay: bool=False, do_compare: bool=False, time: int = 720):
        assert not is_replay or base_dir is not None, "Replaying requires -b"
        self.fuzz_command = fuzz_command
        self.base_dir = base_dir
        self.is_replay = is_replay
        self.do_compare = do_compare
        self.time = time
        self.output_dir = ""

        command = fuzz_command.split()
        for i, val in enumerate(command):
            if val == "-o":
                self.output_dir = command[i + 1]
                break

    def __move_metadata_to_afl_folder(self):
        os.popen(f"mkdir {self.output_dir}/replay")
        os.popen(f"mv /tmp/*.rep {self.output_dir}/replay/")


    # We need to copy the metadata to tmp so that our ld_preload knows where to look for metadata
    def __copy_metadata_to_tmp(self):
        os.popen(f"cp {self.base_dir}/replay/* /tmp")

    def __delete_metata_in_tmp(self):
        os.popen(f"rm /tmp/*.rep")


    def run(self) -> Tuple[float, int, int]:
        try:
            if self.is_replay:
                # Set LD_PRELOAD for replay so file and run args.fuzz_command
                self.__copy_metadata_to_tmp()
                subprocess.run(self.fuzz_command.split(), timeout=self.time + 2, env={"LD_PRELOAD": "src/components/so/replay.so"})
                self.__delete_metata_in_tmp()

                if self.do_compare:
                    percent, bad, total, _, _ = compare(self.base_dir, self.output_dir)
                    fancy_print(
                        f"Percentage similarity: {(1 - percent) * 100}%\nCorrect/Total: {total - bad}/{total}\n"
                    )
                    return percent, bad, total
            else:
                # Set LD_PRELOAD for base so file and run args.fuzz_command
                subprocess.run(self.fuzz_command.split(), timeout=self.time + 2, env={"LD_PRELOAD": "src/components/so/base.so"})
                self.__move_metadata_to_folder()
                return None, None, None

        except subprocess.TimeoutExpired:
            fancy_print(
                f"Completed fuzzing process for {self.output_dir}."
            )
