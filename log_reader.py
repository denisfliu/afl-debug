import fileinput
from itertools import tee
import subprocess

class LogReader():
    def __init__(self, path, checkpoint_frequency = 100000):
        self.file = fileinput.input([path])
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
        If indices are the same, just compare the values.
        Otherwise, check a certain amount of checkpoints.
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
