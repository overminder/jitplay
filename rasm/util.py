import os
import sys

def path2dir(path):
    return os.path.dirname(os.path.abspath(path))

def localpath(caller_path, filename):
    path = os.path.join(path2dir(caller_path), filename)
    assert os.path.isfile(path)
    return path

def load_descr_file(caller_path, filename):
    with open(localpath(caller_path, filename)) as f:
        return filter(bool, (line.split('#')[0].strip() for line in f))

