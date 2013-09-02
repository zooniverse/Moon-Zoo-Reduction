#! /usr/bin/env python

"""latlong2pix.py - Convert lat, long to NAC image pixel coords to

    Version 2013-09-02

    Usage:
        latlong2pix.py <crater_csv> <output_csv> <cub_file>

    Usage examples:
        Using csv input:
            python latlong2pix.py craters_latlong.csv craters_pix.csv CUB/M101963963LE.cal.cub
        
    This program uses the ISIS routine 'campt' to convert the input
    latitude, longitude and size in metres into pixel coordinates and sizes.
    
    The crater_csv file is expected to contain the output of mz_cluster.py.
    
    The product is another csv file, containing the line, sample and
    radius in pixels for each entry.

    
"""

import os, sys, getopt
from math import sin, cos, sqrt, pi
from string import strip
import numpy
import tempfile
from multiprocessing import Pool

# This could be made substantially faster by creating some c++ code based on
# campt.cpp to read a list of line,sample and output a list of long,lat.
# The ISIS3 source code is all available at "rsync isisdist.astrogeology.usgs.gov::"

def latlong2pix(crater_csv=None, output_csv=None, cub_file=None):
    # Open output file for writing
    out = file(output_csv, 'w')
    out.write('x_pix, y_pix, radius_pix, axialratio, angle, boulderyness\n')
    # Open input file
    data = numpy.recfromtxt(crater_csv, delimiter=',', names=True)
    long,long_err,lat,lat_err,radius,radius_err,axialratio,axialratio_err,angle,angle_err,boulderyness,boulderyness_err = (data.field(n) for n in data.dtype.names)
    # Use multiprocessing to speed things up
    p = Pool(8)
    result = p.map(run_campt_backwards, ((cub_file, long[i], lat[i]) for i in range(len(long))))
    sample, line, latpixscale, longpixscale = numpy.array(result).T
    # The following won't work if the lat and long pixel scales are different,
    # and it is not clear exactly what the "diameters" refer to.
    # Actually need to use angle, and know whether xdiam, ydiam are major are minor axis lengths,
    # or projected sizes in long and lat.
    # Currently not handling elliptical craters
    xradius = yradius = radius
    radius_pix = xradius / ((longpixscale + latpixscale) / 2.0)
    outarray = numpy.rec.fromarrays((line, sample, radius_pix, axialratio, angle, boulderyness))
    numpy.savetxt(out, outarray, delimiter=", ", fmt='%.3f')
    out.close()

    
def run_campt_backwards((cub_file, long, lat)):
    # Construct command line
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmpname = tmp.name
    tmp.close()
    cmd = 'campt from=%s to=%s format=flat append=true type=ground longitude=%s latitude=%s > /dev/null' % (cub_file, tmpname, long, lat)
    status = os.system(cmd) # returns the exit status, check it
    if status > 0:
        raise ISISError("Execution of campt failed.")
    # Run command and output to a temp file
    tmp = file(tmpname)
    l = tmp.readline()
    ls = l.split(',')
    l = tmp.readline()
    tmp.close()
    os.remove(tmpname)
    ls = l.split(',')
    sample, line, latpixscale, longpixscale = [float(ls[x]) for x in [2,3,16,17]]
    return sample, line, latpixscale, longpixscale


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
        if len(args) not in (3,):
            raise Usage("Wrong number of arguments")
        if len(args) == 3:
            crater_csv, output_csv, cub_file = args
            nac_name = ""
        if not os.path.exists(crater_csv):
            raise Usage("Input crater file does not exist: %s"%crater_csv)
        elif os.path.exists(output_csv) and (not clobber):
            raise Usage("Output file already exists: %s\nUse -f to overwrite."%output_csv)
        elif not os.path.exists(cub_file):
            raise Usage("Input cub file does not exist: %s"%cub_file)
        latlong2pix(crater_csv, output_csv, cub_file)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2
    except ISISError, err:
        print >>sys.stderr, "ISIS Error: %s"%err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
