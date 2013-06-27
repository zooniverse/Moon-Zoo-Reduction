#! /usr/bin/env python

"""mz_cluster.py - Try out clustering on MZ data    
"""

import os, sys, getopt
from string import strip
import numpy
from matplotlib import pyplot
import scipy.cluster

minsize = 2.000001

def mz_cluster(fn='testcraters.csv', rfactor=1.0, threshold=2.5, mincount=3, test=True):
    if test:
        make_test_craters(ncraters=25, nobs=10)
        data = numpy.genfromtxt('truthcraters.csv', delimiter=',', names=True)
        truth = numpy.array([data['x'], data['y'], data['r']])
        fn = 'testcraters.csv'
    # Open input file
    data = numpy.genfromtxt(fn, delimiter=',', names=True)
    points = numpy.array([data['x'], data['y'], data['r']*rfactor])
    clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric=crater_metric)
    #clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric='euclidean')
    #clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='inconsistent', method='single', metric='euclidean')
    points[2] /= rfactor
    nclusters = clusters.max()
    print('Found %i initial clusters'%nclusters)
    crater_mean = numpy.zeros((3, nclusters), numpy.float)
    crater_stdev = numpy.zeros((3, nclusters), numpy.float)
    crater_count = numpy.zeros(nclusters, numpy.int)
    for i in range(nclusters):
        p = points[:,clusters == i+1]
        crater_count[i] = p.shape[1]
        crater_mean[:2,i] = p[:2].mean(-1)
        notminsize = p[2]>minsize
        if notminsize.sum() > 0:
            crater_mean[2,i] = p[2][notminsize].mean(-1)
        else:
            crater_mean[2,i] = minsize
        crater_stdev[:,i] = p.std(-1)
    ok = crater_count >= mincount
    crater_count = crater_count[ok]
    crater_mean = crater_mean[:,ok]
    crater_stdeve = crater_stdev[:,ok]
    print('Found %i final clusters'%len(crater_count))
    print crater_count
    pyplot.clf()
    pyplot.ion()
    ax = pyplot.subplot(221)
    xmin = points[0].min()
    xmax = points[0].max()
    dx = xmax-xmin
    ax.set_xlim(xmin - 0.1*dx, xmax + 0.1*dx)
    ymin = points[1].min()
    ymax = points[1].max()
    dy = ymax-ymin
    ax.set_ylim(ymin - 0.1*dy, ymax + 0.1*dy)
    draw_craters(points, c='r')
    draw_craters(truth, c='g', lw=5)
    draw_craters(crater_mean, c='b', lw=2)
    ax = pyplot.subplot(224)
    pyplot.plot(points[0], points[1], 'o', alpha=0.25)
    pyplot.plot(crater_mean[0], crater_mean[1], '*')
    pyplot.xlabel('x')
    pyplot.ylabel('y')
    ax.set_xlim(xmin - 0.1*dx, xmax + 0.1*dx)
    ax.set_ylim(ymin - 0.1*dy, ymax + 0.1*dy)
    ax = pyplot.subplot(222)
    pyplot.plot(points[0], points[2], 'o', alpha=0.25)
    pyplot.plot(crater_mean[0], crater_mean[2], '*')
    pyplot.xlabel('x')
    pyplot.ylabel('r')
    ax.set_xlim(xmin - 0.1*dx, xmax + 0.1*dx)
    ax = pyplot.subplot(223)
    pyplot.plot(points[2], points[1], 'o', alpha=0.25)
    pyplot.plot(crater_mean[2], crater_mean[1], '*')
    pyplot.xlabel('r')
    pyplot.ylabel('y')
    ax.set_ylim(ymin - 0.1*dy, ymax + 0.1*dy)
    pyplot.subplots_adjust(wspace=0.3, hspace=0.3, right=0.95, top=0.95)
    pyplot.show()


def crater_metric(u, v):
    x1, y1, r1 = u
    x2, y2, r2 = v
    if ((r1 <= minsize) | (r2 <= minsize)):
        # if one or both of the craters are minsize
        # set the radius "distance" to minsize
        u = numpy.array([x1, y1, 0.0])
        v = numpy.array([x2, y2, minsize])
        dist = numpy.sqrt(((u-v)*(u-v).T).sum())
    else:
        # could also try normalising by, e.g. sqrt(r)
        dist = numpy.sqrt(((u-v)*(u-v).T).sum())
    return dist


def draw_craters(points, c='r', lw=1, ls='solid'):
    for (x, y, r) in points.transpose():
        circle=pyplot.Circle((x, y), r, color=c, fill=False, lw=lw, ls=ls, alpha=0.5)
        fig = pyplot.gcf()
        fig.gca().add_artist(circle)
    pyplot.xlabel('x')
    pyplot.ylabel('y')
    

def make_test_craters(ncraters=10, nobs=10, pmin=0.2, pwrong=0.2):
    scale = numpy.sqrt(ncraters/10.0) * 50
    # true craters
    cx = numpy.random.normal(scale, scale/2.0, size=ncraters)
    cy = numpy.random.normal(scale, scale/2.0, size=ncraters)
    cr = numpy.random.uniform(round(minsize), scale/10.0, size=ncraters)
    # test craters
    x = numpy.zeros(ncraters*nobs, numpy.float)
    y = numpy.zeros(ncraters*nobs, numpy.float)
    r = numpy.zeros(ncraters*nobs, numpy.float)
    flag = numpy.zeros(ncraters*nobs, numpy.int)
    for i in range(nobs):
        x[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cx, numpy.sqrt(cr)/5.0)
        y[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cy, numpy.sqrt(cr)/5.0)
        r[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cr, cr/10.0)
        for j in range(ncraters):
            # some of the time get the position completely wrong
            if numpy.random.random() < pwrong:
                x[i*ncraters+j], y[i*ncraters+j] = numpy.random.normal(scale, scale/2.0, size=2)
                flag[i*ncraters+j] = 2
            # some of the time set the crater to a minimum size
            if numpy.random.random() < pmin:
                r[i*ncraters+j] = 2.0
                flag[i*ncraters+j] = 1
    f = file('truthcraters.csv', 'w')
    f.write('x,y,r\n')
    for i in range(len(cx)):
        f.write('%f,%f,%f\n'%(cx[i], cy[i], cr[i]))
    f.close()        
    f = file('testcraters.csv', 'w')
    f.write('x,y,r,flag\n')
    for i in range(len(x)):
        f.write('%f,%f,%f,%i\n'%(x[i], y[i], r[i], flag[i]))
    f.close()        
    #numpy.savetxt("testcraters.csv", p.transpose(), delimiter=",")

class Usage(Exception):
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
        if len(args) not in (1,):
            raise Usage("Wrong number of arguments")
        if len(args) == 1:
            nac = args[0]
        mz_cluster(nac)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
