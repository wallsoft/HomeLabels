#!/usr/bin/python3

import sys


class NotThreadSafeCounter(object):
    def __init__(self, filename):
        self.filename = filename


    def get(self):
        with open(self.filename, 'r') as F:
            line = F.readline()
            return int(line)

    def inc(self):
        val = self.get() + 1

        with open(self.filename, 'w') as F:
            print(val, file=F)

        return val


if __name__ == '__main__':
    print(NotThreadSafeCounter(sys.argv[1]).inc())
