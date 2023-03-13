from utils import *
import os
import time
import struct

# too lazy to use asserts
# testing the iterator is working properly
# tests file expanding during iteration and 
def log_reader_test1():
    f1 = open('temp.txt', 'wt')
    reader = LogReader('temp.txt')

    def end(stop_point=None):
        f1.close()
        os.remove('temp.txt')
        reader.close()
        if stop_point is not None:
            print(f'log_reader_test1 stopped at {stop_point}')
        return False

    for i in range(10):
        s = str(i) + '\n'
        f1.write(s)
        f1.flush()
    
    for i in range(9):
        reader.next()
        if str(i) != reader.value: return end(1)
    
    f1.write('10\n')
    f1.flush()
    f1.write('11\n')
    f1.flush()
    f1.write('12\n')
    f1.flush()
    
    for i in range(9, 13):
        reader.next()
        if str(i) != reader.value: return end(2)
    
    for _ in range(3):
        reader.next()
        if '12' != reader.value: return end(3)

    f1.write('13\n')
    f1.flush()
    f1.write('14\n')
    f1.flush()
    for i in range(13, 15):
        reader.next()
        if str(i) != reader.value: return end(4)
    
    end()
    return True

# tests speed of log reader
def manual_test1():
    start = time.perf_counter()
    reader = LogReader('~/Thesis/fuzzing_xpdf/outputs/bad1/replay3/default/replay/check.txt')
    while not reader.is_done():
        reader.next()
    end = time.perf_counter()
    print(f'{end - start} seconds to finish reading {reader.count_lines()} lines')

# this test sucks
def seed_comparator_test1():
    file_names = ['temp.so', 'temp1.so']
    files = []
    seed_cmp = SeedComparator(file_names[0])
    for name in file_names:
        files.append(open(name, 'wb'))
        
    def end(stop_point=None):
        for file in files:
            file.close()
        for name in file_names:
            os.remove(name)
        if stop_point is not None:
            print(f'seed_comparator_test1 failed at {stop_point}')
        return False
    
    def write_to_files(a, b=None):
        if b is None:
            for file in files:
                file.write(a)
        else:
            files[0].write(a)
            files[1].write(b)
        files[0].flush()
        files[1].flush()

    x = 4
    random_vars = [b'4', x.to_bytes(2, 'little'), bytearray(struct.pack('f', 4.3)), b'1234', bytes((1, 4, 3))]
    fname = file_names[1]

    if seed_cmp.compare_to_target(fname) != 0: return end(1)

    write_to_files(random_vars[0])
    if seed_cmp.compare_to_target(fname) != 0: return end(2)

    write_to_files(random_vars[1])
    if seed_cmp.compare_to_target(fname) != 0: return end(3)
    
    write_to_files(random_vars[2], random_vars[3])
    if seed_cmp.compare_to_target(fname) != 1: return end(4)

    for _ in range(4):
        write_to_files(random_vars[3], random_vars[2])
    if seed_cmp.compare_to_target(fname) != 2: 
        print(seed_cmp.compare_to_target(fname))
        return end(5)

    write_to_files(random_vars[3])
    if seed_cmp.compare_to_target(fname) != 2: return end(6)

    for _ in range(4):
        write_to_files(random_vars[3], random_vars[2])
    if seed_cmp.compare_to_target(fname) != 3: return end(7)

    end()
    return True


def main():
    failures = []
    tests = [log_reader_test1, seed_comparator_test1]
    
    for test in tests:
        if not test():
            failures.append(test.__name__)
    
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
    #manual_test1()
