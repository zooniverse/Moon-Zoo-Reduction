#! /usr/bin/env python

"""pix2latlong.py - Convert NAC image pixel coords to lat, long

    Version 2014-01-15

    Usage:
        pix2latlong.py <crater_csv> <output_csv> <cub_file>

    Usage examples:
        Using csv input:
            python pix2latlong.py craters.csv craters_latlong.csv CUB/M101963963LE.cal.cub
        Using database input (database name 'moonzoo'), also need to specify nac_name:
            python pix2latlong.py db:moonzoo craters_latlong.csv CUB/M101963963LE.cal.cub, M101963963LE
        
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
from math import sin, cos, sqrt, pi, atan
from string import strip
import numpy
import tempfile
from multiprocessing import Pool

# Some debugging tools:
#from IPython import embed

degrees_per_metre = 360.0 / (2*pi*1737.4*1000)

max_markings_per_slice = 25

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
             AND S.count < %i"""%max_markings_per_slice
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
    p = Pool(16)
    result = p.map(getlatlonginfo, ((cub_file, line[i], sample[i]) for i in range(len(line))))
    lat, long, pixelscale_l, pixelscale_s, phi = numpy.array(result).T

    xradius = xdiam / 2.0
    yradius = ydiam / 2.0
    
    # Assuming angle is that between xdiam and positive line axis measured CCW
    theta = angle * pi / 180.0  # radians
    xradius_metres = xradius * numpy.sqrt((numpy.cos(theta) * pixelscale_s)**2 + (numpy.sin(theta) * pixelscale_l)**2)    
    yradius_metres = yradius * numpy.sqrt((numpy.sin(theta) * pixelscale_s)**2 + (numpy.cos(theta) * pixelscale_l)**2)

    # Flag minimum size craters
    minsize = ((numpy.abs(xdiam - 20.0) + numpy.abs(ydiam - 20.0)) < 1.0e-5).astype(numpy.byte)

    # Ensure axial ratio is between 0 and 1
    possize = (xradius_metres > 0) | (yradius_metres > 0)
    axialratio = numpy.ones(xradius.shape, numpy.float)
    axialratio[possize] = yradius_metres[possize]/xradius_metres[possize]
    flip = axialratio > 1.0001
    axialratio[flip] = 1.0/axialratio[flip]

    # Determine angle
    angle[flip] = angle[flip] + 90.0
    angle -= phi  # or should it be plus?
    angle %= 180.0
    
    outarray = numpy.rec.fromarrays((long, lat, xradius_metres, axialratio, angle, boulderyness, minsize, user))
    numpy.savetxt(out, outarray, delimiter=", ", fmt=('%.6f','%.6f','%.3f','%.3f','%.3f','%i','%i','%i'))
    out.close()


def getlatlonginfo((cub_file, line, sample)):
    # campt does not appear to give useful pixelscale info for images taken at an oblique angle
    # to work around this, I run another campt offset by 1 pixel in line and sample,
    # and use the offset in long and lat to get the relevant pixel scales
    lat, long = run_campt((cub_file, line, sample))
    lat_l, long_l = run_campt((cub_file, line+1, sample))
    lat_s, long_s = run_campt((cub_file, line, sample+1))
    dlat_l = (lat_l - lat) / degrees_per_metre
    dlong_l = (long_l - long) * cos(lat*pi/180.) / degrees_per_metre
    dlat_s = (lat_s - lat) / degrees_per_metre
    dlong_s = (long_s - long) * cos(lat*pi/180.) / degrees_per_metre
    if abs(dlong_s) > 1e-5:
        phi = atan(dlat_s / dlong_s)
    else:
        phi = pi/2.0
    pixelscale_s = sqrt(dlong_s**2 + dlat_s**2)
    pixelscale_l = sqrt(dlong_l**2 + dlat_l**2)
    phi = (phi*180/pi)%180
    return lat, long, pixelscale_l, pixelscale_s, phi

    
def run_campt((cub_file, line, sample)):
    # Construct command line
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmpname = tmp.name
    tmp.close()
    cmd = 'campt from=%s to=%s format=flat append=true type=image line=%s sample=%s > /dev/null' % (cub_file, tmpname, line, sample)
    status = os.system(cmd) # returns the exit status, check it
    if status > 0:
        raise ISISError("Execution of campt failed.")
    # Run command and output to a temp file
    tmp = file(tmpname)
    l = tmp.readline()
    tmp.close()
    os.remove(tmpname)
    ls = l.split(',')
    lat, long, latpixscale, longpixscale = [float(ls[x]) for x in [7,9,16,17]]    
    return lat, long


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
