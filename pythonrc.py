# Python Startup File
# Steven Bamford

# Output to check working
print('Hello, Steven')

# Enable completion
import rlcompleter
import readline

readline.parse_and_bind("tab: complete")

# Save history
import atexit
import os
import sys

if sys.argv[0].find('pyraf') >= 0:
    historyPathLocal = "./.pyrafhistory"
    if os.path.exists(historyPathLocal):
        historyPath = os.path.expanduser(historyPathLocal)
    else:
        historyPath = os.path.expanduser("~/.pyrafhistory")
else:
    historyPathLocal = "./.pyhistory"
    if os.path.exists(historyPathLocal):
        historyPath = os.path.expanduser(historyPathLocal)
    else:
        historyPath = os.path.expanduser("~/.pyhistory")

if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

def save_history(historyPath=historyPath):
    import readline
    readline.write_history_file(historyPathLocal)
    readline.write_history_file(historyPath)

atexit.register(save_history)

# Add directories to search path
import sys

del os, atexit, readline, rlcompleter, save_history, historyPath

# load common modules
import time
from math import *
import numpy
N = numpy
import scipy
#import pyfits
#import pylab
