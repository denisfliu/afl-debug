#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This exploit template was generated via:
# $ pwn template /home/denis/AFLplusplus/afl-fuzz
from pwn import *
from log_reader import *
import time

class Debug:
    def __init__(
            self, 
            afl_path, 
            gdb_obj,
            fuzz_base,
            base_folder_path,
            log_path='default/replay/check.txt',
            is_clone=False
    ):
        # Set up pwntools for the correct architecture
        self.exe = context.binary = ELF(afl_path)
        self.gdb_obj = gdb_obj
        self.is_clone = is_clone
        self.io = None

        # create a log reader for the base folder
        self.base_reader = LogReader(os.path.join(fuzz_base, base_folder_path, log_path))
        self.fuzz_base = fuzz_base
        self.log_path = log_path
        self.replay_reader = None

    def debug(self, log_progress_count=50):
        '''Start the exploit against the target.'''
        self.io = gdb.debug([self.exe.path] + self.gdb_obj.argv, gdbscript=self.gdb_obj.gdbscript, api=True)
        self.io.gdb.continue_and_wait()

        # create log reader for the replay run
        self.replay_reader = LogReader(os.path.join(self.fuzz_base, self.gdb_obj.folder_path, self.log_path))

        # create log comparison object now that we have two readers
        self.log_comparator = LogComparator(self.base_reader, self.replay_reader)


        # Go to the end of the reader and check for differences
        # Might as well check for differences on the way there as well
        # TODO: Possibility of doing some nice function that decreases log_progress_count if it's close
        # To the end

        difference_found = False
        while not difference_found:
            while self.log_comparator.progress_readers(log_progress_count) != Progress.PROGRESSION_FINISHED:
                difference_found = self.log_comparator.compare(True)
                print('bye')
                if difference_found: break

            if not difference_found:
                print('hello')
                difference_found = self.log_comparator.compare(True)
            
            print(f'hi: difference found : {difference_found}')
            self.io.gdb.continue_and_wait()

        # since we found a difference, let's see if we can do anything about it
        self.io.interactive()

class GDBScript:
    """
    This gives the args to run afl-fuzz and the function name
    to break at. We will check for substantial differences when we
    reach the function with the log reader.
    """
    def __init__(self, function_name, folder_path, argv):
        self.gdbscript = f'''
                        break {function_name}
                        '''.format(**locals())
        self.argv = argv
        print(argv)
        self.folder_path = folder_path

def main():
    
    #context.terminal = 'zsh'

    # initialize parameters for instance of Debug
    afl_path = '/home/denis/AFLplusplus/afl-fuzz'
    fuzz_base = os.path.expanduser('~/Thesis/fuzzing_xpdf')
    replay_folder_path = 'outputs/replay'
    base_folder_path = 'outputs/unseed'
    log_path = 'default/replay/check.txt'
    gdb_obj = GDBScript(
        'save_if_interesting', 
        replay_folder_path,
        ['-i',
         os.path.join(fuzz_base, 'pdf_examples'),
         '-o',
         os.path.join(fuzz_base, replay_folder_path),
         '-r',
         os.path.join(fuzz_base, 'outputs/unseed'),
         '--',
         os.path.join(fuzz_base, 'install/bin/pdftotext'),
         '@@',
         '>',
         'temp']
    )

    debug = Debug(
        afl_path=afl_path,
        gdb_obj=gdb_obj,
        fuzz_base=fuzz_base,
        base_folder_path=base_folder_path,
        log_path=log_path,
        is_clone=False
    )
    debug.debug()

if __name__ == '__main__':
    main()

