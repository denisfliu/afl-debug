from log_reader import LogReader
import os
import time

# testing the iterator is working properly
# tests file expanding during iteration and 
def test1():
    f1 = open('temp.txt', 'wt')
    reader = LogReader('temp.txt')

    def end():
        f1.close()
        os.remove('temp.txt')
        reader.close()

    for i in range(10):
        s = str(i) + '\n'
        f1.write(s)
        f1.flush()
    
    for i in range(9):
        reader.next()
        if str(i) != reader.value:
            end()
            return False
    
    f1.write('10\n')
    f1.flush()
    f1.write('11\n')
    f1.flush()
    f1.write('12\n')
    f1.flush()
    
    for i in range(9, 13):
        reader.next()
        if str(i) != reader.value:
            end()
            return False
    
    for _ in range(3):
        reader.next()
        if '12' != reader.value:
            end()
            return False

    f1.write('13\n')
    f1.flush()
    f1.write('14\n')
    f1.flush()
    for i in range(13, 15):
        reader.next()
        if str(i) != reader.value:
            end()
            return False
    
    end()
    return True

def manual_test1():
    start = time.perf_counter()
    reader = LogReader('~/Thesis/fuzzing_xpdf/outputs/bad1/replay3/default/replay/check.txt')
    while not reader.is_done():
        reader.next()
    end = time.perf_counter()
    print(f'{end - start} seconds to finish reading {reader.count_lines()} lines')

def main():
    failures = []
    
    if not test1():
        failures.append(test1.__name__)
    
    msg = ''
    if not failures:
        msg = 'All tests passed.'
    else:
        msg = f'{len(failures)} tests failed:\n'
        for failure in failures:
            msg += f'{failure}\n'

    print(msg)

if __name__ == "__main__":
    main()
    manual_test1()
