import sys, getopt
import numpy
import mz_cluster
from scipy.optimize import fmin_powell as fmin
from scipy.stats import scoreatpercentile

from IPython import embed

def find_cat_offset(cat1, cat2, outcat=None, position_scale=4.0, size_scale=0.4):
    # set global variables for crater metric
    mz_cluster.pscale = position_scale
    mz_cluster.sscale = size_scale
    p1 = numpy.genfromtxt(cat1, delimiter=',', names=True)
    p2 = numpy.genfromtxt(cat2, delimiter=',', names=True)
    big = scoreatpercentile(p1['radius'], 75)
    big = min(big, scoreatpercentile(p2['radius'], 75))
    p1s = p1[p1['radius'] > big]
    p2s = p2[p2['radius'] > big]
    minsize1 = numpy.zeros(p1s.shape[0], [('minsize', numpy.double)])
    minsize2 = numpy.zeros(p2s.shape[0], [('minsize', numpy.double)])
    X1 = numpy.asarray([p1s[name] for name in ('long', 'lat', 'radius')]+[minsize1['minsize']], order='c', dtype=numpy.double)
    X2 = numpy.asarray([p2s[name] for name in ('long', 'lat', 'radius')]+[minsize2['minsize']], order='c', dtype=numpy.double)
    results = fmin(mz_cluster.comparedata, [0.0, 0.0], args=(X1, X2), xtol=0.001, maxiter=1000)
    results *= mz_cluster.degrees_per_metre  # convert from rough metres to degrees
    print('Found a shift of dlong = %e deg, dlat = %e deg'%tuple(results))
    p2['long'] += results[0]
    p2['lat'] += results[1]
    # Write offset crater catalogue to a csv file
    if outcat is None:
        dot = cat2.rfind('.')
        if dot == -1:
            outcat = cat2+'_offset'
        else:
            outcat = cat2[:dot]+'_offset'+ cat2[dot:]
    fout = open(outcat, 'w')
    fout.write(','.join(p2.dtype.names)+'\n')
    numpy.savetxt(fout, p2.T, delimiter=", ", fmt='%.6f')
    fout.close()


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

        
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], '')
        except getopt.error, msg:
            raise Usage(msg)
        if len(args) not in (2, 3):
            raise Usage("Requires two csv catalogue filenames and an optional output catalogue name.")
        else:
            find_cat_offset(*args)
    except Usage, err:
        print >>sys.stderr, err.msg
        return 2

    
if __name__ == "__main__":
    sys.exit(main())
