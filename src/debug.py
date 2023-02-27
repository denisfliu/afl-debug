#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This exploit template was generated via:
# $ pwn template /home/denis/AFLplusplus/afl-fuzz
from pwn import *
from log_reader import *
from omegaconf import OmegaConf
from tqdm import tqdm

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
        '''Start the exploit against the target.'''
        self.io = gdb.debug([self.exe.path] + self.gdb_obj.argv, gdbscript=self.gdb_obj.gdbscript, api=True)
        self.io.gdb.continue_and_wait()
        self.stop()

    def stop(self):
        raise NotImplementedError

class Replay(DebugType):
    def __init__(
            self, 
            gdb_obj,
            log_increment,
    ):
        super().__init__(
            gdb_obj=gdb_obj,
        )
        self.log_increment = log_increment
    
    def stop(self):
        # create log reader for the replay run
        self.base_reader = LogReader(os.path.join(self.fuzz_base, self.gdb_obj.base_folder_path, self.log_path))
        self.replay_reader = LogReader(os.path.join(self.fuzz_base, self.gdb_obj.replay_folder_path, self.log_path))

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
                while self.log_comparator.progress_readers(self.log_increment) != Progress.PROGRESSION_FINISHED:
                    difference_found = not self.log_comparator.compare()
                    if difference_found: break
                pbar.update(self.replay_reader.file_line_count - pbar.last_print_n)

                if not difference_found:
                    difference_found = not self.log_comparator.compare()
                
                self.io.gdb.continue_and_wait()

            # since we found a difference, let's see if we can do anything about it
            self.log_comparator.print_debug()
            self.io.interactive()
        pbar.close()

class Line(DebugType):
    def __init__(
            self, 
            gdb_obj,
            line_stop,
    ):
        super().__init__(
            gdb_obj=gdb_obj,
        )
        self.line_stop = line_stop
    
    def stop(self):
        # create log reader for the replay run
        self.replay_reader = LogReader(os.path.join(self.fuzz_base, self.gdb_obj.replay_folder_path, self.log_path))

        pbar = tqdm(total=self.line_stop)
        line_reached = False
        while not line_reached:
            if self.replay_reader.file_line_count < self.line_stop:
                while self.replay_reader.next():
                    pass
            else:
                for _ in range(self.replay_reader.index, self.line_stop):
                    self.replay_reader.next()
                if self.replay_reader.index == self.line_stop:
                    line_reached = True
            pbar.update(self.replay_reader.index - pbar.last_print_n)
            self.io.gdb.continue_and_wait()

        # since we found a difference, let's see if we can do anything about it
        print(self.replay_reader.to_string())
        self.io.interactive()
        self.replay_reader.close()
        pbar.close()

class GDBScript:
    """
    This gives the args to run afl-fuzz and the function name
    to break at. We will check for substantial differences when we
    reach the function with the log reader.
    """
    def __init__(self, config):
        self.gdbscript = f'''
                        set pagination off
                        '''.format(**locals())
        
        for breakpoint in config.gdb.breakpoints:
            self.gdbscript += f'break {breakpoint}\n'.format(**locals())

        self.afl_path = config.afl_path
        self.fuzz_folder = config.fuzz.fuzz_folder
        self.log_path = config.gdb.log_path
        binary_path = config.fuzz.binary
        inputs = config.fuzz.inputs

        if config.debug_mode == 'replay':
            self.base_folder_path = config.gdb.replay.outputs.base_folder_path
            self.replay_folder_path = config.gdb.replay.outputs.replay_folder_path
        elif config.debug_mode == 'line':
            self.base_folder_path = config.gdb.line.outputs.base_folder_path
            self.replay_folder_path = config.gdb.line.outputs.replay_folder_path
        else:
            raise NotImplementedError

        self.argv = [
            '-i',
            os.path.join(self.fuzz_folder, inputs),
            '-o',
            os.path.join(self.fuzz_folder, self.replay_folder_path),
            '-r',
            os.path.join(self.fuzz_folder, self.base_folder_path),
            '--',
            os.path.join(self.fuzz_folder, binary_path),
            '@@',
            '>',
            '/dev/null'
        ]

def main():
    # initialize parameters for instance of Debug
    config_path = 'config.yaml'
    config = OmegaConf.load(config_path)
    gdb_obj = GDBScript(config)

    if config.debug_mode == 'replay':
        debug = Replay(
            gdb_obj=gdb_obj,
            log_increment=config.gdb.replay.log_increment
        )
    elif config.debug_mode == 'line':
        debug = Line(
            gdb_obj=gdb_obj,
            line_stop=config.gdb.line.line_stop
        )
    else:
        raise NotImplementedError

    debug.debug()

if __name__ == '__main__':
    main()

