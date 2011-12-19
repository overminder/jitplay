import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

def localpath(filename):
    path = os.path.join(HERE, filename)
    assert os.path.isfile(path)
    return path

def load_descr_file(filename):
    with open(localpath(filename)) as f:
        return filter(bool, (line.split('#')[0].strip() for line in f))

