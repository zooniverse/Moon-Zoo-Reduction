#! /usr/bin/env python

"""slice2latlong.py - Convert NAC image pixel coords to lat, long

    Version 2014-01-15

    Usage:
        slice2latlong.py <db_name> <cub_file> <nac_name>

    Usage examples:
        python slice2latlong.py moonzoo CUB/M101963963LE.cal.cub M101963963LE
        
    This program uses the ISIS routine 'campt' to convert the input
    pixel coordinates and sizes into latitude, longitude and size in metres.
    
    This program directly accesses the database for required information,
    and writes a new table to the database.
    
"""

from pix2latlong import getlatlonginfo, run_campt, Usage, ISISError
import os, sys, getopt
from math import pi
import numpy
from multiprocessing import Pool

# Some debugging tools:
from IPython import embed

degrees_per_metre = 360.0 / (2*pi*1737.4*1000)

def read_db(nac_name, db='moonzoo'):
    import pymysql
    db = pymysql.connect(host="localhost", user="root", passwd="", db=db)
    cur = db.cursor() 
    sql = "SELECT * FROM slice_counts WHERE nac_name='%s';"%nac_name
    cur.execute(sql)
    names = [d[0] for d in cur.description]
    data = numpy.rec.fromrecords(cur.fetchall(), names=names)
    db.close()
    return data


def write_db(data, db='moonzoo'):
    import pymysql
    db = pymysql.connect(host="localhost", user="root", passwd="", db=db)
    cur = db.cursor() 
    sql = "UPDATE slice_counts SET long_min=%f, long_max=%f, lat_min=%f, lat_max=%f where asset_id=%i;"
    for d in data:
        cur.execute(sql%d)
    db.commit()
    db.close()


def slice2latlong(db=None, cub_file=None, nac_name=""):
    print nac_name
    data = read_db(nac_name.upper(), db)
    id = data.field("asset_id")
    # Use multiprocessing to speed things up
    p = Pool(16)
    result = p.map(run_campt, ((cub_file, data.field("x_min")[i], data.field("y_min")[i]) for i in range(len(data))))
    lat_1, long_1  = numpy.array(result).T
    result = p.map(run_campt, ((cub_file, data.field("x_min")[i], data.field("y_max")[i]) for i in range(len(data))))
    lat_2, long_2  = numpy.array(result).T
    result = p.map(run_campt, ((cub_file, data.field("x_max")[i], data.field("y_max")[i]) for i in range(len(data))))
    lat_3, long_3  = numpy.array(result).T
    result = p.map(run_campt, ((cub_file, data.field("x_max")[i], data.field("y_min")[i]) for i in range(len(data))))
    lat_4, long_4  = numpy.array(result).T
    long_min = numpy.min((long_1, long_2, long_3, long_4), axis=0)
    long_max = numpy.max((long_1, long_2, long_3, long_4), axis=0)
    lat_min = numpy.min((lat_1, lat_2, lat_3, lat_4), axis=0)
    lat_max = numpy.max((lat_1, lat_2, lat_3, lat_4), axis=0)
    out = numpy.vstack((long_min, long_max, lat_min, lat_max, id)).T
    write_db(out, db)


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
        if len(args) != 3:
            raise Usage("Wrong number of arguments")
        else:
            db, cub_file, nac_name = args
        if not os.path.exists(cub_file):
            raise Usage("Input cub file does not exist: %s"%cub_file)
        slice2latlong(db, cub_file, nac_name)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2
    except ISISError, err:
        print >>sys.stderr, "ISIS Error: %s"%err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
