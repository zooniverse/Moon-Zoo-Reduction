#! /usr/bin/env python

"""pix2latlong.py - Convert NAC image pixel coords to lat, long

    Version 2013-09-02

    Usage:
        pix2latlong.py <crater_csv> <output_csv> <cub_file>

    Usage examples:
        Using csv input:
            python pix2latlong.py craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub
        Using database input (database name 'moonzoo'), also need to specify nac_name:
            python db:moonzoo craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub, M101963963LE
        
    This program uses the ISIS routine 'campt' to convert the input
    pixel coordinates and sizes into latitude, longitude and size in metres.
    
    The crater_csv file is expected to contain specific columns.
    This file may be created using the following SQL code:
        SELECT xnac, ynac, x_diameter_nac, y_diameter_nac,
               angle_nac, boulderyness, zoom, zooniverse_user_id
        INTO OUTFILE 'craters.csv'
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\n'
        FROM craters;
    The file will be output wherever your database files live.

    The product is another csv file, containing the longitude, latitude,
    size, axial_ratio, angle, boulderyness, minsize flag and user id for each entry.

    
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

def read_db(nac_name, db='moonzoo'):
    import pymysql
    db = pymysql.connect(host="localhost", user="root", passwd="", db=db)
    cur = db.cursor() 
    sql = """SELECT xnac, ynac, x_diameter_nac, y_diameter_nac, 
                    angle, boulderyness, zoom, zooniverse_user_id
             FROM craters as C, classification_stats as S
             WHERE C.classification_id = S.classification_id
             AND S.count < 25"""
    if nac_name is not None:
        sql += "\nAND nac_name='%s';"%nac_name
    cur.execute(sql)
    data = numpy.rec.fromrecords(cur.fetchall())
    db.close()
    return data


def pix2latlong(crater_csv=None, output_csv=None, cub_file=None, nac_name=""):
    # Open output file for writing
    out = file(output_csv, 'w')
    #out.write('x_pix, y_pix, size_pix, lat, long, size_metres\n')
    out.write('long, lat, radius, axialratio, angle, boulderyness, minsize, user\n')
    # Open input file
    if crater_csv.startswith('db:'):
        db = crater_csv[3:]
        data = read_db(nac_name.upper(), db)
    else:
        data = numpy.recfromtxt(crater_csv, delimiter=',')
    sample, line, xdiam, ydiam, angle, boulderyness, zoom, user = (data.field(n) for n in data.dtype.names)
    # Use multiprocessing to speed things up
    p = Pool(8)
    result = p.map(run_campt, ((cub_file, line[i], sample[i]) for i in range(len(line))))
    lat, long, latpixscale, longpixscale = numpy.array(result).T
    # The following won't work if the lat and long pixel scales are different,
    # and it is not clear exactly what the "diameters" refer to.
    # Actually need to use angle, and know whether xdiam, ydiam are major are minor axis lengths,
    # or projected sizes in long and lat.
    xradius = xdiam / 2.0
    xradius_long = numpy.abs(xradius * numpy.cos(angle*pi/180.0) * longpixscale)
    xradius_lat = numpy.abs(xradius * numpy.sin(angle*pi/180.0) * latpixscale)
    xradius_metres = numpy.sqrt(xradius_long**2 + xradius_lat**2)
    yradius = ydiam / 2.0
    yradius_long = numpy.abs(yradius * numpy.sin(angle*pi/180.0) * longpixscale)
    yradius_lat = numpy.abs(yradius * numpy.cos(angle*pi/180.0) * latpixscale)
    yradius_metres = numpy.sqrt(yradius_long**2 + yradius_lat**2)
    # Flag minimum size craters
    minsize = ((numpy.abs(xdiam - 20.0) + numpy.abs(ydiam - 20.0)) < 1.0e-5).astype(numpy.byte)
    possize = (xradius_metres > 0) | (yradius_metres > 0)
    axialratio = numpy.ones(xradius.shape, numpy.float)
    axialratio[possize] = yradius_metres[possize]/xradius_metres[possize]
    flip = axialratio > 1.0001
    axialratio[flip] = 1.0/axialratio[flip]
    angle[flip] = angle[flip] + 90.0
    outarray = numpy.rec.fromarrays((long, lat, xradius_metres, axialratio, angle, boulderyness, minsize, user))
    numpy.savetxt(out, outarray, delimiter=", ", fmt=('%.6f','%.6f','%.3f','%.3f','%.3f','%i','%i','%i'))
    out.close()

    
def run_campt((cub_file, line, sample)):
    # Construct command line
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmpname = tmp.name
    tmp.close()
    cmd = 'campt from=%s to=%s format=flat append=true type=image line=%s sample=%s > /dev/null' % (cub_file, tmpname, line, sample)
    print cmd
    status = os.system(cmd) # returns the exit status, check it
    if status > 0:
        raise ISISError("Execution of campt failed.")
    # Run command and output to a temp file
    tmp = file(tmpname)
    #l = tmp.readline()
    #print l
    #ls = l.split(',')
    #print ls
    #print [ls[x] for x in [7,9,16,17]]
    l = tmp.readline()
    tmp.close()
    os.remove(tmpname)
    ls = l.split(',')
    lat, long, latpixscale, longpixscale = [float(ls[x]) for x in [7,9,16,17]]
    return lat, long, latpixscale, longpixscale


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
        if len(args) not in (3, 4, 5):
            raise Usage("Wrong number of arguments")
        if len(args) == 3:
            crater_csv, output_csv, cub_file = args
            nac_name = ""
        elif len(args) == 4:
            crater_csv, output_csv, cub_file, nac_name = args
        if (not crater_csv.startswith("db:")) and (not os.path.exists(crater_csv)):
            raise Usage("Input crater file does not exist: %s"%crater_csv)
        elif os.path.exists(output_csv) and (not clobber):
            raise Usage("Output file already exists: %s\nUse -f to overwrite."%output_csv)
        elif not os.path.exists(cub_file):
            raise Usage("Input cub file does not exist: %s"%cub_file)
        pix2latlong(crater_csv, output_csv, cub_file, nac_name)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2
    except ISISError, err:
        print >>sys.stderr, "ISIS Error: %s"%err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
