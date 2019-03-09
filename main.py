# coding=utf-8
"""Script entry."""

import sys
import dataprocess

if __name__ == '__main__':
    process = dataprocess.Dataprocess()
    process.readarg(sys.argv)
