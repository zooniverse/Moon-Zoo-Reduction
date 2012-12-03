#! /usr/bin/env python

"""pix2latlong.py - Convert NAC image pixel coords to lat, long

    Version 2012-12-03

    Usage:
        pix2latlong.py <crater_csv> <output_csv> <cub_file>

    Usage examples:
        If pix2latlong.py is executable and on the path:
            pix2latlong.py craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub
        If pix2latlong.py is executable and not on the path:
            ./pix2latlong.py craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub
        If pix2latlong.py is not executable and not on the path:
            python pix2latlong.py craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub

    This program uses the ISIS routine 'campt' to convert the input
    pixel coordinates and sizes into latitude, longitude and size in
    metres.
    
    The crater_csv file is expected to contain x, y and radius as the
    first three columns, but it may contain further columns, which are
    ignored.

    The product is another csv file, containing x, y and radius in
    pixel space from the input file, with the addition of the
    latitude, longitude and size in metres for each entry.
    
"""

import os, sys, getopt
from string import strip

def pix2latlong(crater_csv, output_csv, cub_file, flipwidth=0):
    # Open output file for writing
    out = file(output_csv, 'w')
    out.write('x_pix, y_pix, size_pix, lat, long, size_metres\n')
    # Open input file
    f = file(crater_csv) 
    # Loop over each line, send line,sample to campt
    i = 0
    for i, inLine in enumerate(f):
        # Output progress
        if i%100 == 0 and i > 0: print 'On crater %i'%i
        # Following line is for testing on small sample
        # if i > 10: break
        # Get data for one object from input file
        try:
            sample, line, diam = [float(x) for x in inLine.split(',')[:3]]
        except ValueError:
            if i == 0:
                continue  # probably csv file header
            else:
                raise Usage("Input file in wrong format")
        # The 'first guess' NAC R image coordinates are flipped horizontally
        # To solve this, ideally, the NAC coords would be fixed appropriately.
        # However, as a fudged solution, the user may provide a width for
        # the original NAC image, which will be used to flip the x-coord.
        if flipwidth > 0:
            sample = flipwidth - sample
        # Construct command line
        cmd = 'campt from=%s to=tmp.csv format=flat append=true type=image line=%s sample=%s > /dev/null' % (cub_file, line, sample)
        #print cmd
        status = os.system(cmd) # returns the exit status, check it
        if status > 0:
            raise ISISError("Execution of campt failed.")
        # Run command and output to a temp file
        tmp = file('tmp.csv')
        l = tmp.readline()
        ls = l.split(',')
        #print [ls[x] for x in [7,9,16,17]]
        l = tmp.readline()
        tmp.close()
        os.remove('tmp.csv')
        ls = l.split(',')
        lat, long, latpixscale, longpixscale = [float(ls[x]) for x in [7,9,16,17]]
        diam_metres = diam * longpixscale
        out.write('%f, %f, %f, %f, %f, %f\n'%(line, sample, diam, lat, long, diam_metres))
    f.close()
    out.close()
    if i == 0:
        raise Usage("Input file in wrong format")

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
        if len(args) not in (3, 4):
            raise Usage("Wrong number of arguments")
        if len(args) == 3:
            crater_csv, output_csv, cub_file = args
            flipwidth = 0
        elif len(args) == 4:
            crater_csv, output_csv, cub_file, flipwidth = args
        try:
            flipwidth = int(flipwidth)
        except ValueError:
            raise Usage("Input flipwidth must be an integer: %s"%flipwidth)
        if not os.path.exists(crater_csv):
            raise Usage("Input crater file does not exist: %s"%crater_csv)
        elif os.path.exists(output_csv) and (not clobber):
            raise Usage("Output file already exists: %s\nUse -f to overwrite."%output_csv)
        elif not os.path.exists(cub_file):
            raise Usage("Input cub file does not exist: %s"%cub_file)
        pix2latlong(crater_csv, output_csv, cub_file, flipwidth)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2
    except ISISError, err:
        print >>sys.stderr, "ISIS Error: %s"%err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
