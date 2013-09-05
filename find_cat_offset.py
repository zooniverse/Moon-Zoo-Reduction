import sys, getopt
import numpy
import mz_cluster

from IPython import embed

def find_cat_offset(cat1, cat2, outcat=None, position_scale=4.0, size_scale=0.4):
    # set global variables for crater metric
    mz_cluster.pscale = position_scale
    mz_cluster.sscale = size_scale
    p1 = numpy.genfromtxt(cat1, delimiter=',', names=True)
    p2 = numpy.genfromtxt(cat2, delimiter=',', names=True)
    p2new = mz_cluster.find_offset(p1, p2)
    # Write offset crater catalogue to a csv file
    if outcat is None:
        dot = cat2.rfind('.')
        if dot == -1:
            outcat = cat2+'_offset'
        else:
            outcat = cat2[:dot]+'_offset'+ cat2[dot:]
    fout = open(outcat, 'w')
    fout.write(','.join(p2new.dtype.names)+'\n')
    numpy.savetxt(fout, p2new.T, delimiter=", ", fmt='%.6f')
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
