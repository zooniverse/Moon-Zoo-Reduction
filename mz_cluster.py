#! /usr/bin/env python

"""mz_cluster.py - Try out clustering on MZ data

    Version 2013-07-05

    Usage:
        mz_cluster.py <output_filename_base> <moonzoo_markings_csv> <expert_markings_csv>
                      <threshold> <min_count> <long_min> <long_max> <lat_min> <lat_max>

    Note that the csv files must contain column headers, including 'long', 'lat',
    and 'xradius'.

    This requires the 'fastcluster' module.  Most easily obtained by typing:
        easy_install fastcluster
    into a terminal.  (Although I'm actually not sure this is much faster than the default
    python module for our purposes.)

    Usage example:
        python mz_cluster.py mz_clusters data/M104311715/craters_RE_latlong.csv data/M104311715/715_xpert.csv 

"""

import os, sys, getopt
from string import strip
import numpy
import matplotlib
import matplotlib.pyplot as pyplot
import scipy.cluster
import fastcluster
import timeit
from sklearn.cluster import DBSCAN

matplotlib.rcParams.update({'font.size': 10})

minsizes = 7.4 * numpy.array([1.0, 4.0, 8.34])
rfactor = 360.0 / (2*numpy.pi*1737.4*1000)

def timetest():
    print 'Time: %f s'%min(timeit.repeat(stmt='mz_cluster.mz_cluster()', setup='import mz_cluster', repeat=3, number=1))

def mz_cluster(outname='mz_clusters', fn=None, expertfn=None, threshold=1.0, mincount=3,
               long_min=-360, long_max=360, lat_min=-360, lat_max=360):
    truth = None
    if fn is None:
        test = True
        make_test_craters(ncraters=100, nobs=5)
        expertfn = 'truthcraters.csv'
        fn = 'testcraters.csv'
    if expertfn is not None:
        data = numpy.genfromtxt(expertfn, delimiter=',', names=True)
        truth = numpy.array([data['long'], data['lat'], data['xradius']])
        datarange = (truth[0].min(), truth[0].max(), truth[1].min(), truth[1].max())
        print 'Expert data covers region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange
        #long_centre, lat_centre = (truth[0].mean(), truth[1].mean())
        #print 'Centre: (long, lat) = (%.4f, %.4f)'%(long_centre, lat_centre)
        #truth[2] /= 5.0
        if test:
            long_min, long_max, lat_min, lat_max = datarange
    # Open input file
    data = numpy.genfromtxt(fn, delimiter=',', names=True)
    #points = numpy.array([data['x'], data['y'], data['size_m']])
    points = numpy.array([data['long'], data['lat'], data['xradius']])
    datarange = (points[0].min(), points[0].max(), points[1].min(), points[1].max())
    print 'Markings cover region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange
    # select region
    select = (points[0] > long_min) & (points[0] < long_max)
    select &= (points[1] > lat_min) & (points[1] < lat_max)
    points = points[:,select]
    if truth is not None:
        select = (truth[0] > long_min) & (truth[0] < long_max)
        select &= (truth[1] > lat_min) & (truth[1] < lat_max)
        select &= truth[2] > 7.0
        truth = truth[:,select]
    print 'Number of markings:', points.shape[1]
    if expertfn is not None:
        print 'Number of expert markings:', truth.shape[1]
    clusters = fastclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric=crater_metric)
    #clusters = dbscanclusterdata(points.transpose(), t=threshold, m=mincount, metric=crater_metric)
    #clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric='euclidean')
    #clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='inconsistent', method='single', metric='euclidean')
    nclusters = clusters.max()
    print('Found %i initial clusters'%nclusters)
    crater_mean = numpy.zeros((3, nclusters), numpy.float)
    crater_stdev = numpy.zeros((3, nclusters), numpy.float)
    crater_count = numpy.zeros(nclusters, numpy.int)
    for i in range(nclusters):
        p = points[:,clusters == i+1]
        crater_count[i] = p.shape[1]
        crater_mean[:2,i] = p[:2].mean(-1)
        notminsize = numpy.logical_not(is_minsize(p[2]))
        if notminsize.sum() > 0:
            crater_mean[2,i] = p[2][notminsize].mean(-1)
        else:
            crater_mean[2,i] = p[2].mean(-1)
        crater_stdev[:,i] = p.std(-1)
    ok = crater_count >= mincount
    crater_count = crater_count[ok]
    crater_mean = crater_mean[:,ok]
    crater_stdev = crater_stdev[:,ok]
    print('Found %i final clusters'%len(crater_count))
    fout = open(outname+'.csv', 'w')
    fout.write('long,long_err,lat,lat_err,xradius,xradius_err\n')
    for i in range(len(crater_count)):
        x = (crater_mean[0,i], crater_stdev[0,i], crater_mean[1,i], crater_stdev[1,i],
             crater_mean[2,i], crater_stdev[2,i])
        fout.write('%.6f,%.6f,%.6f,%.6f,%.2f,%.2f\n'%x)
    fout.close()
    # plot craters
    pyplot.clf()
    pyplot.ion()
    radius_min, radius_max = (points[2].min(), points[2].max())
    radius_range = radius_max - radius_min
    radius_min -= 0.05*radius_range
    radius_max += 0.05*radius_range
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))
    ax = pyplot.subplot(221)
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    msel = is_minsize(points[2])
    draw_craters(points[:,msel], c='r', ls='dotted', lw=0.5)
    draw_craters(points[:,numpy.logical_not(msel)], c='r', lw=0.5)
    if truth is not None:
        draw_craters(truth, c='g', lw=2)
    draw_craters(crater_mean, c='b', lw=1)
    ax = pyplot.subplot(224)
    pyplot.plot(crater_mean[0], crater_mean[1], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points[0], points[1], 'o', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('lat')
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    ax = pyplot.subplot(222)
    pyplot.plot(crater_mean[0], numpy.log10(crater_mean[2]), 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points[0], numpy.log10(points[2]), 'o', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('log10(radius)')
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(log10radius_min, log10radius_max)
    ax = pyplot.subplot(223)
    pyplot.plot(numpy.log10(crater_mean[2]), crater_mean[1], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(numpy.log10(points[2]), points[1], 'o', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('log10(radius)')
    pyplot.ylabel('lat')
    ax.set_xlim(log10radius_min, log10radius_max)
    ax.set_ylim(lat_min, lat_max)
    pyplot.subplots_adjust(wspace=0.3, hspace=0.3, right=0.95, top=0.95)
    pyplot.savefig(outname+'.pdf')
    return crater_count

    

def is_minsize(r):
    # this is rough, can do better if know zoom level
    out = None
    for m in minsizes:
        if out is None:
            out = numpy.abs(r - m) < 1.0
        else:
            out |= numpy.abs(r - m) < 1.0
    return out


def crater_metric(uin, vin):
    x1, y1, r1 = uin
    x2, y2, r2 = vin
    is_minsize(r1)
    if is_minsize(r1) | is_minsize(r2):
        # if one or both of the craters are minsize
        # set the radius "distance" to zero
        r1 = 1.0
        r2 = 1.0
    # scale crater size
    r1 = r1
    r2 = r2
    rav = (r1 + r2)/2.0 / 4.0
    r1 /= rav
    r2 /= rav
    # scale position
    x1, x2, y1, y2 = numpy.divide((x1, x2, y1, y2), rfactor*numpy.sqrt(rav)*8)
    # vectors for metric
    u = numpy.array([x1, y1, r1])
    v = numpy.array([x2, y2, r2])        
    # could also try normalising by, e.g. sqrt(r)
    dist = numpy.sqrt(((u-v)*(u-v).T).sum())
    #print uin, vin, u, v, dist
    return dist


def draw_craters(points, c='r', lw=1, ls='solid'):
    for (x, y, r) in points.transpose():
        circle=pyplot.Circle((x, y), r*rfactor, color=c, fill=False, lw=lw, ls=ls, alpha=0.5)
        fig = pyplot.gcf()
        fig.gca().add_artist(circle)
    pyplot.xlabel('long')
    pyplot.ylabel('lat')
    

def make_test_craters(ncraters=10, nobs=10, pmin=0.2, pwrong=0.2):
    scale = numpy.sqrt(ncraters/10.0) * 100
    # true craters
    cx = numpy.random.normal(scale, scale/2.0, size=ncraters)
    cy = numpy.random.normal(scale, scale/2.0, size=ncraters)
    cr = numpy.random.uniform(minsizes[0], scale/5.0, size=ncraters)
    # test craters
    x = numpy.zeros(ncraters*nobs, numpy.float)
    y = numpy.zeros(ncraters*nobs, numpy.float)
    r = numpy.zeros(ncraters*nobs, numpy.float)
    flag = numpy.zeros(ncraters*nobs, numpy.int)
    for i in range(nobs):
        x[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cx, numpy.sqrt(cr)/5.0)
        y[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cy, numpy.sqrt(cr)/5.0)
        r[i*ncraters:(i+1)*ncraters] = numpy.maximum(numpy.random.normal(cr, cr/20.0), minsizes[0])
        for j in range(ncraters):
            # some of the time get the position completely wrong
            if numpy.random.random() < pwrong:
                x[i*ncraters+j], y[i*ncraters+j] = numpy.random.normal(scale, scale/2.0, size=2)
                flag[i*ncraters+j] = 2
            # some of the time set the crater to a minimum size
            if numpy.random.random() < pmin:
                r[i*ncraters+j] = minsizes[0]
                flag[i*ncraters+j] = 1
    # convert x,y in metres into long,lat
    x, y, cx, cy = numpy.multiply((x, y, cx, cy), rfactor)
    f = file('truthcraters.csv', 'w')
    f.write('long,lat,xradius\n')
    for i in range(len(cx)):
        f.write('%f,%f,%f\n'%(cx[i], cy[i], cr[i]))
    f.close()        
    f = file('testcraters.csv', 'w')
    f.write('long,lat,xradius,flag\n')
    for i in range(len(x)):
        f.write('%f,%f,%f,%i\n'%(x[i], y[i], r[i], flag[i]))
    f.close()        
    #numpy.savetxt("testcraters.csv", p.transpose(), delimiter=",")


def fastclusterdata(X, t, criterion='inconsistent', \
                 metric='euclidean', depth=2, method='single', R=None):
    """
    scipy.cluster.hierarchy.fclusterdata modified to use fastcluster
    """
    X = numpy.asarray(X, order='c', dtype=numpy.double)

    if type(X) != numpy.ndarray or len(X.shape) != 2:
        raise TypeError('The observation matrix X must be an n by m numpy '
                        'array.')

    Y = scipy.cluster.hierarchy.distance.pdist(X, metric=metric)
    Z = fastcluster.linkage(Y, method=method)
    #Z = scipy.cluster.hierarchy.linkage(Y, method=method)
    if R is None:
        R = scipy.cluster.hierarchy.inconsistent(Z, d=depth)
    else:
        R = numpy.asarray(R, order='c')
    T = scipy.cluster.hierarchy.fcluster(Z, criterion=criterion, depth=depth, R=R, t=t)
    return T


def dbscanclusterdata(X, t, m, metric='euclidean'):
    """
    Attempt at using sklearn.DBSCAN - but no faster than fastcluster
    """
    X = numpy.asarray(X, order='c', dtype=numpy.double)

    if type(X) != numpy.ndarray or len(X.shape) != 2:
        raise TypeError('The observation matrix X must be an n by m numpy '
                        'array.')

    db = DBSCAN(eps=t, min_samples=m, metric=metric).fit(X)
    labels = numpy.array(db.labels_, dtype=numpy.int) + 1
    return labels


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
        for i in range(len(args)):
            if i > 2:
                args[i] = float(args[i])
        mz_cluster(*args)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
