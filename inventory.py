#!/usr/bin/python3

import fcntl
import sys


class Inventory(object):
    def __init__(self, filename):
        self.filename = filename


    def append(self, val):
        with open(self.filename, 'a') as F:
            fcntl.flock(F, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(val, file=F)
            fcntl.flock(F, fcntl.LOCK_UN)


    def __len__(self):
        lines = 0

        with open(self.filename, 'r') as F:
            fcntl.flock(F, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for line in F:
                line = line.strip()
                if line:
                    lines += 1
            fcntl.flock(F, fcntl.LOCK_UN)

        return lines


    def contents(self):
        with open(self.filename, 'r') as F:
            fcntl.flock(F, fcntl.LOCK_EX | fcntl.LOCK_NB)
            ret = list(
                    filter(
                        None,
                        (line.strip() for line in F)
                        )
                    )
            fcntl.flock(F, fcntl.LOCK_UN)
        return ret


if __name__ == '__main__':
    filename = sys.argv[1]

    inv = Inventory(filename)

    for val in sys.argv[2:]:
        inv.append(val)

    for line in inv.contents():
        print(line)
