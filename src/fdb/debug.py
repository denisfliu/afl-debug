from pwn import *
from tqdm import tqdm

import glob

import src.fdb.factory as factory
from src.fdb.utils import *


class DebugType:
    def __init__(
        self,
        gdb_obj,
    ):
        # Set up pwntools for the correct architecture
        self.exe = context.binary = ELF(gdb_obj.afl_path, checksec=False)
        self.gdb_obj = gdb_obj
        self.io = None
        self.fuzz_base = gdb_obj.fuzz_folder
        self.log_path = gdb_obj.log_path

    def debug(self):
        """Start the exploit against the target."""
        self.io = gdb.debug(
            [self.exe.path] + self.gdb_obj.argv,
            gdbscript=self.gdb_obj.gdbscript,
            api=True,
        )
        self.io.gdb.continue_and_wait()
        self.stop()

    def stop(self):
        raise NotImplementedError


class Replay(DebugType):
    def __init__(self, gdb_obj, config):
        super().__init__(
            gdb_obj=gdb_obj,
        )
        self.log_increment = config.gdb.replay.log_increment

    def stop(self):
        # create log reader for the replay run
        self.base_reader = LogReader(
            os.path.join(self.fuzz_base, self.gdb_obj.base_folder_path, self.log_path)
        )
        self.replay_reader = LogReader(
            os.path.join(self.fuzz_base, self.gdb_obj.replay_folder_path, self.log_path)
        )

        # create log comparison object now that we have two readers
        self.log_comparator = LogComparator(self.base_reader, self.replay_reader)

        # Go to the end of the reader and check for differences
        # Might as well check for differences on the way there as well
        # TODO: Possibility of doing some nice function that decreases log_increment if it's close
        # To the end

        pbar = tqdm(total=self.base_reader.file_line_count)
        while True:
            difference_found = False
            while not difference_found:
                while (
                    self.log_comparator.progress_readers(self.log_increment)
                    != Progress.PROGRESSION_FINISHED
                ):
                    difference_found = not self.log_comparator.compare()
                    if difference_found:
                        break
                pbar.update(self.replay_reader.file_line_count - pbar.last_print_n)

                if not difference_found:
                    difference_found = not self.log_comparator.compare()

                self.io.gdb.continue_and_wait()

            # since we found a difference, let's see if we can do anything about it
            self.log_comparator.print_debug()
            self.io.interactive()
        pbar.close()


class Line(DebugType):
    def __init__(self, gdb_obj, config):
        super().__init__(
            gdb_obj=gdb_obj,
        )
        self.line_stop = config.gdb.line.line_stop

    def stop(self):
        # create log reader for the replay run
        self.replay_reader = LogReader(
            os.path.join(self.fuzz_base, self.gdb_obj.replay_folder_path, self.log_path)
        )

        pbar = tqdm(total=self.line_stop)
        while True:
            while self.replay_reader.next():
                pass
            pbar.update(self.replay_reader.index - pbar.last_print_n)
            if self.replay_reader.index >= self.line_stop:
                break
            self.io.gdb.continue_and_wait()

        # since we found a difference, let's see if we can do anything about it
        print(self.replay_reader.to_string())
        self.io.interactive()
        self.replay_reader.close()
        pbar.close()


class Seed(DebugType):
    def __init__(self, gdb_obj, config):
        super().__init__(
            gdb_obj=gdb_obj,
        )
        target_path = os.path.join(gdb_obj.fuzz_folder, config.gdb.seed.target_path)
        seed_comparator_name = config.gdb.seed.seed_comparator
        self.seed_comparator = factory.seed_comparator(seed_comparator_name, target_path)
        self.max_distance=config.gdb.seed.max_distance
        self.queue_folder = os.path.join(gdb_obj.fuzz_folder, gdb_obj.replay_folder_path, 'default/queue')
    
    def stop(self):
        distance = self.check_latest_queue()
        while True:
            while distance > self.max_distance:
                self.io.gdb.continue_and_wait()
                distance = self.check_latest_queue()
            # since we found a difference, let's see if we can do anything about it
            self.io.interactive()

    # this is not efficient
    def check_latest_queue(self):
        list_of_files = glob.glob(f"{self.queue_folder}/*")
        if not list_of_files:
            return self.max_distance + 1
        latest_file = max(list_of_files, key=os.path.getctime)
        seed_distance = self.seed_comparator.compare_to_target(latest_file)
        print(f"Seed {latest_file} distance: {seed_distance}")
        return seed_distance


class GDBScript:
    """
    This gives the args to run afl-fuzz and the desired breakpoints.
    """

    def __init__(self, config):
        self.gdbscript = f"""
                        set pagination off
                        """.format(
            **locals()
        )

        for breakpoint in config.gdb.breakpoints:
            self.gdbscript += f"break {breakpoint}\n".format(**locals())

        self.afl_path = config.afl_path
        self.fuzz_folder = config.fuzz.fuzz_folder
        self.log_path = config.gdb.log_path
        self.base_folder_path = config.gdb.base_folder_path
        self.replay_folder_path = config.gdb.replay_folder_path
        binary_path = config.fuzz.binary
        inputs = config.fuzz.inputs

        self.argv = [
            "-i",
            os.path.join(self.fuzz_folder, inputs),
            "-o",
            os.path.join(self.fuzz_folder, self.replay_folder_path),
            "-r",
            os.path.join(self.fuzz_folder, self.base_folder_path),
            "--",
            os.path.join(self.fuzz_folder, binary_path),
            "@@",
            ">",
            "/dev/null",
        ]


def main():
    # initialize parameters for instance of Debug
    from src.utils import get_config

    config = get_config()
    gdb_obj = GDBScript(config)

    debug = factory.debug_type(config.debug_mode, gdb_obj, config)

    assert not os.path.exists(
        os.path.join(gdb_obj.fuzz_folder, gdb_obj.replay_folder_path)
    ), f"Path: {gdb_obj.replay_folder_path} already exists."
    assert (
        check_scaling_governor
    ), "Scaling governor check failed. Run an arbitrary AFL run for more info."

    debug.debug()


if __name__ == "__main__":
    main()
