#! /usr/bin/env python

"""pix2latlong.py - Convert NAC image pixel coords to lat, long

    Version 2013-08-30

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
    kilometres.
    
    The crater_csv file is expected to contain x, y and radius as the
    first three columns, but it may contain further columns, which are
    ignored.  This file may be created using the following SQL code:
        SELECT xnac, ynac, x_diameter_nac, y_diameter_nac,
               angle_nac, boulderyness, zoom, zooniverse_id
        INTO OUTFILE 'craters.csv'
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\n'
        FROM craters

    The product is another csv file, containing the longitude, latitude,
    two sizes, angle and boulderyness for each entry.

    It is currently not clear exactly what the sizes refer to (major/minor axis lengths,
    or sizes projected on the long and lat axes), and the conversion to metres is probably
    incorrect if the long and lat pixel scales are different.
    
"""

import os, sys, getopt
from string import strip

# This could be made substantially faster by creating some c++ code based on
# campt.cpp to read a list of line,sample and output a list of long,lat.
# The ISIS3 source code is all available at "rsync isisdist.astrogeology.usgs.gov::"

# IN PROGRESS ADAPTING THIS TO READ FROM (AND WRITE TO?) SQL DB DIRECTLY
# IF OUTPUTING CSV, NEED TO RETAIN ZOOM LEVEL AND USER ID

def read_db(nac_name='M104311715RE'):
    # not yet tested...
    db = pymysql.connect(host="localhost", user="root", passwd="", db="moonzoo")
    cur = db.cursor() 
    sql = """SELECT xnac, ynac, x_diameter_nac, y_diameter_nac, 
                    angle_nac, boulderyness, zoom, zooniverse_user_id
             FROM craters
             WHERE nac_name=`%s`;"""%nac_name
    cur.execute(sql)
    data = numpy.recarray(cur.fetchall())
    db.close()


def pix2latlong(crater_csv=None, output_csv=None, cub_file=None, flipwidth=0, nac_name='M104311715RE'):
    # Open output file for writing
    out = file(output_csv, 'w')
    #out.write('x_pix, y_pix, size_pix, lat, long, size_metres\n')
    out.write('long, lat, xdiam_km, ydiam_km, angle, boulderyness, zoom, user\n')
    # Open input file
    if crater_csv is None:
        f = read_db(nac_name)
    else:
        f = file(crater_csv) 
    # Loop over each line, send line,sample to campt
    i = 0
    for i, inLine in enumerate(f):
        # Output progress
        if i%100 == 0 and i > 0: print 'On crater %i'%i
        # Following line is for testing on small sample
        # if i > 10: break
        # Get data for one object from input file
        if crater_csv is None:
            try:
                fields = inLine.split(',')
                sample, line, xdiam, ydiam, angle = [float(x) for x in fields[:5]]
                boulderyness, zoom, user = [int(x) for x in fields[5:8]]
            except ValueError:
                if i == 0:
                    continue  # probably csv file header
                else:
                    raise Usage("Input file in wrong format")
        else:
            sample, line, xdiam, ydiam, angle, boulderyness, zoom, user = inLine
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
        # The following won't work if the lat and long pixel scales are different,
        # and it is not clear exactly what the "diameters" refer to.
        # Actually need to use angle, and know whether xdiam, ydiam are major are minor axis lengths,
        # or projected sizes in long and lat.
        pixscale = (latpixscale + longpixscale)/2.0
        xdiam_metres = xdiam * pixscale
        ydiam_metres = ydiam * pixscale
        xdiam_km = xdiam_metres / 1000.0
        ydiam_km = ydiam_metres / 1000.0
        #out.write('%f, %f, %f, %f, %f, %f\n'%(line, sample, diam, lat, long, diam_metres))
        out.write('%f, %f, %f\n'%(long, lat, xdiam_km, ydiam_km, angle, boulderyness))
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
