import os
from enum import Enum
import subprocess

class LogReader():
    def __init__(self, path, checkpoint_frequency = 100000):
        self.file = open(os.path.expanduser(path), 'r')
        self.value_iterator = iter(self.file)
        self.path = path
        self.file_line_count = self.count_lines()
        self.value = None
        self.index = 0
        self.checkpoint_frequency = checkpoint_frequency
        self.checkpoints = []
    
    def iterate(self):
        """
        Don't use this, use next.
        """
        if self.is_done():
            self.value =  next(self.value_iterator).strip()
            return True
        return False
        
    def next(self):
        """
        goes to next value, if no next value, do nothing
        increments index and checks for checkpoint_frequency stuff as well
        assumes there are no intentional empty lines
        """

        success = self.iterate()
        if not success:
            return

        # if an iterator is updated there could be a \n read. skip it
        # this case should never result in a StopIteration case
        if not self.value:
            success = self.iterate()
            if not success:
                return

        if self.index % self.checkpoint_frequency == 0:
            self.checkpoints.append(self.value)
        self.index += 1


    def count_lines(self):
        return int(subprocess.check_output(f"wc -l {self.path}", shell=True).split()[0])

    def is_done(self):
        if self.index >= self.file_line_count:
            self.file_line_count = self.count_lines()
            if self.index >= self.file_line_count:
                return False
        return True
    
    def close(self):
        self.file.close()

    def print(self):
        print(self.value)
    
class LogComparator():
    def __init__(self, reader1: LogReader, reader2: LogReader):
        self.reader1 = reader1
        self.reader2 = reader2

    def compare(self):
        """
        If readers are reading together, then compre their values.
        Otherwise, compare checkpoints.
        """
        if self.reader1.index == self.reader2.index:
            return self.reader1.value == self.reader2.value
        else:
            min_len = min(len(self.reader1.checkpoints), len(self.reader2.checkpoints))
            if min_len < 2:
                return self.reader1.checkpoints[0] == self.reader2.checkpoints[0]
            else:
                # return the comparison of the last two checkpoints
                check1 = self.reader1.checkpoints[min_len - 1] == self.reader2.checkpoints[min_len - 1]
                check2 = self.reader1.checkpoints[min_len - 1] == self.reader2.checkpoints[min_len - 1]
                return check1 and check2
    
    def progress_readers(self, line_count=1):
        """
        If readers are at the same index, it's convenient
        to progress (both read a line) them at the same time.
        The variable line_count determines how many times the log_reader
        progresses. Using a sufficiently large number should completely progress
        one (or both) readers to the last line. Returns Fal
        """
        for _ in range(line_count):
            if self.reader1.index == self.reader2.index:
                if self.reader1.is_done() or self.reader2.is_done():
                    return Progress.PROGRESSION_FINISHED
                self.reader1.next()
                self.reader2.next()
            else:
                return Progress.PROGRESSION_FAILED
        return Progress.PROGRESSION_SUCCESSFUL
    
    def close_readers(self):
        """
        Close both the readers.
        """
        self.reader1.close()
        self.reader2.close()

class Progress(Enum):
    """
    SUCCESSFUL: Finished desired line count.
    PROGRESSION_FAILED: Index mismatch.
    PROGRESSION_FINISHED: One reader finished.
    """
    PROGRESSION_SUCCESSFUL = 1
    PROGRESSION_FAILED = 2
    PROGRESSION_FINISHED = 3
