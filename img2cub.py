#! /usr/bin/env python

"""img2cub.py - Convert NAC image to calibrated ISIS cub file

    Usage:
        img2cub.py <img_file> <cub_path>

    Usage examples:
        If img2cub.py is executable and on the path:
            img2cub.py IMG/M101963963LE.IMG CUB/M101963963LE.cal.cub
        If img2cub.py is executable and not on the path:
            ./img2cub.py IMG/M101963963LE.IMG CUB/M101963963LE.cal.cub
        If img2cub.py is not executable and not on the path:
            python img2cub.py IMG/M101963963LE.IMG CUB/M101963963LE.cal.cub

    This program uses the ISIS routines to convert the input PDS IMG
    file into a calibrated CUB file.  The routines used are: lronac2isis,
    lronaccal and spiceinit.
    
"""

import os, sys, getopt
from string import strip
import tempfile
from pipes import quote

def img2cub(img, cub):
    if os.path.exists(cub):
        os.remove(cub)
    tmp = tempfilename()
    cmd = 'lronac2isis from=%s to=%s'%(img, tmp)
    status = os.system(cmd)
    if status > 0:
        raise ISISError("Execution of lronac2isis failed.")
    cmd = 'lronaccal from=%s to=%s'%(tmp, cub.replace(".cub", ""))
    status = os.system(cmd)
    if status > 0:
        raise ISISError("Execution of lronaccal failed.")
    os.remove(tmp)
    print 'spiceinit...'
    cmd = 'spiceinit from=%s'%cub
    status = os.system(cmd)
    if status > 0:
        raise ISISError("Execution of spiceinit failed.")
    print 'done'

def tempfilename():
    f = tempfile.NamedTemporaryFile(mode='w+t', suffix='.cub', delete=False)
    tmp = f.name
    f.close()
    return quote(tmp)

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class ISISError(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hf", ["help", "force"])
        except getopt.error, msg:
            raise Usage(msg)
        clobber = False
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                return 1
            if o in ("-f", "--force"):
                clobber = True
        if len(args) == 2:
            img_file, cub_file = args
            if not os.path.exists(img_file):
                raise Usage("Input IMG file does not exist: %s"%img_file)
            elif os.path.exists(cub_file) and (not clobber):
                raise Usage("Output CUB file already exists: %s\nUse -f to overwrite."%cub_file)
            else:
                img2cub(img_file, cub_file)
        else:
            raise Usage("Wrong number of arguments")
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2
    except ISISError, err:
        print >>sys.stderr, "ISIS Error: %s"%err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
