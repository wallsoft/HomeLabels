#!/usr/bin/python3


import sys


class Inventory(object):
    def __init__(self, filename):
        self.filename = filename


    def append(self, val):
        with open(self.filename, 'a') as F:
            print(val, file=F)


if __name__ == '__main__':
    filename = sys.argv[1]

    inv = Inventory(filename)

    for val in sys.argv[2:]:
        inv.append(val)
