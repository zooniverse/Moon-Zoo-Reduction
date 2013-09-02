#! /usr/bin/env python

"""mz_cluster.py - Perform clustering on MZ data.

    Version 2013-08-29

    Usage:
        mz_cluster.py <output_filename_base> <moonzoo_markings_csv> <expert_markings_csv>
                      <threshold> <mincount> <maxcount> <maxiter> <position_scale> <size_scale>
                      <long_min> <long_max> <lat_min> <lat_max>

    Note that the csv files must contain column headers, including 'long', 'lat' and 'xradius'.
    
    Usage example:
        python mz_cluster.py mz_clusters data/M104311715/craters_RE_latlong.csv data/M104311715/715_xpert.csv 

"""

import os, sys, getopt
from string import strip
from math import sqrt, pi
import numpy
import matplotlib
import matplotlib.pyplot as pyplot
import scipy.cluster
#import fastcluster

# Some debugging tools:
#from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)

matplotlib.rcParams.update({'font.size': 14})

# minimum size is still hardcoded - needs to adapt to NAC pixel scale,
# and preferably use knowledge of zoom level of each marking

#minsizes = 7.4 * numpy.array([1.0, 4.0, 8.34])
minsizes = 14.5 * numpy.array([1.0, 4.0, 8.34])
degrees_per_metre = 360.0 / (2*pi*1737.4*1000)


def mz_cluster(output_filename_base='mz_clusters', moonzoo_markings_csv=None, expert_markings_csv=None,
               threshold=1.0, mincount=2, maxcount=10, maxiter=3,
               position_scale=4.0, size_scale=0.4,
               long_min=30.657, long_max=30.798, lat_min=20.122, lat_max=20.265):
    """Runs clustering routine.

    This reads in all the data, clusters the markings, selects
    reliable craters, calculates their properties, creates and output
    catalogue, and makes a variety of plots.

    If no input filename is supplied, performs a test simulation and outputs
    some performance assessments.
    
    If expert data is provided, calculates some consistency statistics.
     
    Keyword arguments:
    output_filename_base -- basename of all output files
    moonzoo_markings_csv -- name of file containing raw crater markings
    expert_markings_csv -- name of file containing expert craters
    threshold -- general scaling of the clustering linking length
    mincount -- minimum number of markings required for a crater
    maxcount -- expected maximum number of markings for a crater
    maxiter -- maximum number of iterations for splitting too-large clusters
    position_scale -- maximum positional difference for linking two markings,
                      normalised by the square root of the crater size
    size_scale -- maximum fractional size difference for linking two markings
    long_min, long_max, lat_min, lat_max -- limits of region to consider

    This could incorporate user weighting in future, e.g. by assigning
    clusters scores based on the sum of the user weights for each
    clustered marking, and using a minscore rather than mincount.

    """
    print
    print('*** Start of mz_cluster ***\n')
    print('output_filename_base = %s\nmoonzoo_markings_csv = %s\nexpert_markings_csv = %s'%(output_filename_base, moonzoo_markings_csv, expert_markings_csv))
    print('threshold = %f\nmincount = %i\nmaxcount = %i\nmaxiter = %i'%(threshold, mincount, maxcount, maxiter))
    print('position_scale = %f\nsize_scale = %f'%(position_scale, size_scale))
    print
    # set global variables for crater metric
    global pscale, sscale
    pscale = position_scale
    sscale = size_scale
    # read in all data
    test=False
    if moonzoo_markings_csv is None:
        # If no filename specified, generate and use test data
        test = True
        make_test_craters(ncraters=50, nobs=10)
        expert_markings_csv = 'truthcraters.csv'
        moonzoo_markings_csv = 'testcraters.csv'
    truth = None
    if expert_markings_csv is not None:
        # If 'truth' data is supplied, use it in plots
        data = numpy.genfromtxt(expert_markings_csv, delimiter=None, names=True)
        truth = numpy.array([data['x'], data['y'], data['RIM_DIA']])
        datarange = (truth[0].min(), truth[0].max(), truth[1].min(), truth[1].max())
        print('Expert data covers region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
        truth[2] /= 2.0  # fix diameter to radius
        if test:
            long_min, long_max, lat_min, lat_max = datarange
    # Get markings data
    data = numpy.genfromtxt(moonzoo_markings_csv, delimiter=None, names=True)
    #points = numpy.array([data['x'], data['y'], data['size_m']])
    points = numpy.array([data['long'], data['lat'], data['radius'], data['axialratio'],
                          data['angle'], data['boulderyness'], data['minsize'], data['user'])
    datarange = (points[0].min(), points[0].max(), points[1].min(), points[1].max())
    print('Markings cover region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
    # Select region of interest
    print('Considering region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%(long_min, long_max, lat_min, lat_max))
    select = (points[0] >= long_min) & (points[0] <= long_max)
    select &= (points[1] >= lat_min) & (points[1] <= lat_max)
    points = points[:,select]
    if test:
        # If this is a test we know the true clustering,
        # which can be used to evaluate performance
        labels_true = numpy.array(data['truelabel'], dtype=numpy.int)[select]
    if 'minsize' in data.names:
        minsize = numpy.array(data['minsize'], dtype=numpy.bool)[select]
    if 'user' in data.names:
        user = numpy.array(data['user'], dtype=numpy.int)[select]
    if truth is not None:
        select = (truth[0] >= long_min) & (truth[0] <= long_max)
        select &= (truth[1] >= lat_min) & (truth[1] <= lat_max)
        select &= truth[2] > minsizes[0]  # remove small expert craters
        truth = truth[:,select]
    print('\nNumber of markings: %i'%points.shape[1])
    if expert_markings_csv is not None:
        print('Number of expert markings: %i'%truth.shape[1])
    # Perform clustering of markings
    clusters = iterative_fastclusterdata(points, threshold, maxcount, mincount, maxiter)
    # Previous clustering methods:
    ### clusters = fastclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric=crater_metric)
    ### clusters = dbscanclusterdata(points.transpose(), t=threshold, m=mincount, metric=crater_metric)
    ### clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='distance', method='single', metric='euclidean')
    ### clusters = scipy.cluster.hierarchy.fclusterdata(points.transpose(), t=threshold, criterion='inconsistent', method='single', metric='euclidean')
    # Calculate clustered crater properties and useful stats
    # while eliminating clusters with too few markings
    nclusters = clusters.max()
    print('\nFound %i initial clusters'%nclusters)
    crater_mean = numpy.zeros((3, nclusters), numpy.float)
    crater_stdev = numpy.zeros((3, nclusters), numpy.float)
    crater_count = numpy.zeros(nclusters, numpy.int)
    dra = []
    drs = []
    ds = []
    s = []
    notmin = []
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
        if crater_count[i] >= mincount:
            dra.extend(crater_absolute_position_metric(p, crater_mean[:,i]))
            drs.extend(crater_position_metric(p, crater_mean[:,i]))
            ds.extend(crater_size_metric(p, crater_mean[:,i]))
            s.extend([crater_mean[2,i]]*crater_count[i])
            notmin.extend(notminsize)
    dra, drs, ds, s, notmin = map(numpy.array, (dra, drs, ds, s, notmin))
    # select final craters (should we also remove minsize craters?)
    ok = crater_count >= mincount
    crater_count = crater_count[ok]
    crater_mean = crater_mean[:,ok]
    crater_stdev = crater_stdev[:,ok]
    print('Found %i final clusters'%len(crater_count))
    # Write final crater catalogue to a csv file
    fout = open(output_filename_base+'_craters.csv', 'w')
    fout.write('long,long_err,lat,lat_err,radius,radius_err\n')
    for i in range(len(crater_count)):
        x = (crater_mean[0,i], crater_stdev[0,i], crater_mean[1,i], crater_stdev[1,i],
             crater_mean[2,i], crater_stdev[2,i])
        fout.write('%.6f,%.6f,%.6f,%.6f,%.2f,%.2f\n'%x)
    fout.close()
    # Make some plots
    plot_cluster_stats(dra, drs, ds, s, notmin, output_filename_base)
    plot_crater_stats(crater_mean, truth, output_filename_base)
    plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base)
    plot_cluster_diagnostics(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base)
    # If this is a test, calculate some metrics
    if test:
        from sklearn import metrics
        print
        print("Homogeneity: %0.3f" % metrics.homogeneity_score(labels_true, clusters))
        print("Completeness: %0.3f" % metrics.completeness_score(labels_true, clusters))
        print("V-measure: %0.3f" % metrics.v_measure_score(labels_true, clusters))
        print("Adjusted Rand Index: %0.3f"
              % metrics.adjusted_rand_score(labels_true, clusters))
        print("Adjusted Mutual Information: %0.3f"
              % metrics.adjusted_mutual_info_score(labels_true, clusters))
    print
    return crater_count


def is_minsize(r):
    # this is rough, can do better if know zoom level
    out = None
    for m in minsizes:
        if out is None:
            out = numpy.abs(r - m)/m < 0.01
        else:
            out |= numpy.abs(r - m)/m < 0.01
    return out


def crater_metric(uin, vin):
    # get position and size differences
    dr = crater_position_metric(uin, vin) / pscale
    ds = crater_size_metric(uin, vin) / sscale
    # combine position and size differences
    dist = sqrt(dr**2 + ds**2)
    return dist


def crater_absolute_position_metric(uin, vin):
    # get coords
    x1, y1, s1 = uin
    x2, y2, s2 = vin
    # calculate crater position difference
    dr = numpy.sqrt((x2-x1)**2 + (y2-y1)**2) / degrees_per_metre
    return dr


def crater_position_metric(uin, vin):
    # get coords
    x1, y1, s1 = uin
    x2, y2, s2 = vin
    # calculate mean crater size
    sm = (s1 + s2)/2.0
    # calculate crater position difference
    dr = crater_absolute_position_metric(uin, vin) / numpy.sqrt(sm)
    return dr


def crater_size_metric(uin, vin):
    # get coords
    x1, y1, s1 = uin
    x2, y2, s2 = vin
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    ds = numpy.where(is_minsize(s1)|is_minsize(s2), 0.0,  numpy.abs(s1 - s2) / sm)
    return ds


def draw_craters(points, c='r', lw=1, ls='solid'):
    for (x, y, r) in points.transpose():
        circle=pyplot.Circle((x, y), r*degrees_per_metre, color=c, fill=False, lw=lw, ls=ls, alpha=0.5)
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
    truelabel = numpy.zeros(ncraters*nobs, numpy.int)
    flag = numpy.zeros(ncraters*nobs, numpy.int)
    for i in range(nobs):
        x[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cx, numpy.sqrt(cr)/5.0)
        y[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cy, numpy.sqrt(cr)/5.0)
        r[i*ncraters:(i+1)*ncraters] = numpy.maximum(numpy.random.normal(cr, cr/20.0), minsizes[0])
        truelabel[i*ncraters:(i+1)*ncraters] = numpy.arange(ncraters)+1
        for j in range(ncraters):
            # some of the time get the position completely wrong
            if numpy.random.random() < pwrong:
                x[i*ncraters+j], y[i*ncraters+j] = numpy.random.normal(scale, scale/2.0, size=2)
                flag[i*ncraters+j] = 2
                truelabel[i*ncraters+j] = 0
            # some of the time set the crater to a minimum size
            if numpy.random.random() < pmin:
                r[i*ncraters+j] = minsizes[0]
                flag[i*ncraters+j] = 1
    # convert x,y in metres into long,lat
    x, y, cx, cy = numpy.multiply((x, y, cx, cy), degrees_per_metre)
    f = file('truthcraters.csv', 'w')
    f.write('long,lat,radius\n')
    for i in range(len(cx)):
        f.write('%f,%f,%f\n'%(cx[i], cy[i], cr[i]))
    f.close()        
    f = file('testcraters.csv', 'w')
    f.write('long,lat,radius,flag,truelabel\n')
    for i in range(len(x)):
        f.write('%f,%f,%f,%i,%i\n'%(x[i], y[i], r[i], flag[i], truelabel[i]))
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
    #Z = fastcluster.linkage(Y, method=method)
    Z = scipy.cluster.hierarchy.linkage(Y, method=method)
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
    from sklearn.cluster import DBSCAN

    X = numpy.asarray(X, order='c', dtype=numpy.double)

    if type(X) != numpy.ndarray or len(X.shape) != 2:
        raise TypeError('The observation matrix X must be an n by m numpy '
                        'array.')

    db = DBSCAN(eps=t, min_samples=m, metric=metric).fit(X)
    labels = numpy.array(db.labels_, dtype=numpy.int) + 1
    return labels


def iterative_fastclusterdata(points, threshold, maxcount, mincount, maxiter):
    clusters = numpy.ones(points.shape[1], numpy.int)
    nclusters = 1
    largeclustersflag = True
    iteration = 0
    while largeclustersflag and iteration < maxiter:
        threshold *= 0.9**iteration
        iteration += 1
        largeclustersflag = False
        i = 1
        newclusters = 0
        while i <= nclusters - newclusters:
            selectedpoints = clusters == i
            p = points[:,selectedpoints]            
            if p.shape[1] > maxcount:
                if not largeclustersflag:
                    print('\nIteration %i, threshold %.3f'%(iteration, threshold))
                print('%i clusters, cluster number %i with %i members.'%(nclusters, i, p.shape[1]))
                subclusters = fastclusterdata(p.transpose(), t=threshold, criterion='distance',
                                              method='single', metric=crater_metric)
                nsubclusters = subclusters.max()
                newclusters += nsubclusters
                clusters[clusters > i] -= 1
                clusters[selectedpoints] = subclusters + nclusters - 1
                nclusters = clusters.max()
                largeclustersflag = True
                cluster_count = numpy.zeros(nclusters, numpy.int)
                for j in range(nclusters):
                    q = points[:,clusters == j+1]
                    cluster_count[j] = q.shape[1]
                if nsubclusters > 1:
                    print('After subclustering, %i clusters, of which %i have at least %i measurements.'%(nclusters, (cluster_count >= mincount).sum(), mincount))
                    #print('Cluster labels: ' + str(clusters))
                    #print('Cluster counts: ' + str(cluster_count))
                else:
                    print('No change after subclustering')
            else:
                i += 1
    return clusters


def plot_cluster_stats(dra, drs, ds, s, notminsize, output_filename_base):
    x = numpy.arange(0.0, s.max(), 0.1)
    minsize = numpy.logical_not(notminsize)
    #
    pyplot.figure()
    pyplot.plot(s[notminsize], ds[notminsize], '.')
    pyplot.plot(s[minsize], ds[minsize], '.')
    pyplot.plot(x, x*0+0.4, '-')
    pyplot.xlabel('size')
    pyplot.ylabel('ds')
    pyplot.savefig(output_filename_base+'_size_ds.png', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.plot(s, drs, '.')
    pyplot.plot(x, x*0+4.0, '-')
    pyplot.xlabel('size')
    pyplot.ylabel('drs')
    pyplot.savefig(output_filename_base+'_size_drs.png', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.plot(s, dra, '.')
    pyplot.plot(x, 4.0*numpy.sqrt(x), '-')
    pyplot.xlabel('size')
    pyplot.ylabel('dra')
    pyplot.savefig(output_filename_base+'_size_dra.png', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    #pyplot.hist(ds, 100, histtype='stepfilled')
    pyplot.hist(ds[(ds > 1e-5) & notminsize], 100, histtype='stepfilled')
    pyplot.vlines(0.4, 0, pyplot.axis()[3])
    pyplot.axis(ymin=0)
    pyplot.xlabel('ds')
    pyplot.savefig(output_filename_base+'_hist_ds.png', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.hist(drs, 100, histtype='stepfilled')
    pyplot.vlines(4.0, 0, pyplot.axis()[3])
    pyplot.axis(ymin=0)
    pyplot.xlabel('drs')
    pyplot.savefig(output_filename_base+'_hist_drs.png', dpi=300)
    pyplot.close()

    
def plot_crater_stats(crater_mean, truth, output_filename_base):
    pyplot.figure(figsize=(6., 8.))
    sf_bins_clust, sf_clust = plot_sizefreq(crater_mean[2], label='clustered')
    if truth is not None:
        print
        sf_bins_truth, sf_truth = plot_sizefreq(truth[2], sf_bins_clust, label='truth')
        ok = (sf_clust > 0) & (sf_truth > 0)
        delta = sf_clust[ok].astype(numpy.float)/sf_truth[ok] - 1
        text = 'mean_delta = %.3f'%delta.mean()
        print text
        pyplot.text(1.0, 10**1.0, text)
        text = 'rms_delta = %.3f'%numpy.sqrt((delta**2).mean())
        print text    
        pyplot.text(1.0, 10**0.8, text)
        text = 'mad_delta = %.3f'%numpy.median(numpy.abs(delta))
        print text
        pyplot.text(1.0, 10**0.6, text)
    pyplot.axis(xmin=0.8, xmax=2.7, ymin=0.5)
    pyplot.xlabel('log10(radius [m])')
    pyplot.ylabel('cumulative frequency')
    pyplot.legend(loc='lower left')
    pyplot.savefig(output_filename_base+'_sizefreq.png', dpi=300)
    pyplot.close()


def plot_sizefreq(size, bins=10000, label=''):
    h, b = numpy.histogram(numpy.log10(size), bins)
    c = numpy.cumsum(h[::-1])
    c = c[::-1]
    c = numpy.concatenate((c[0:1], c))
    ax = pyplot.plot(b, c, ls='steps-pre', label=label)
    pyplot.gca().set_yscale('log')
    return b, c


def plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base):
    pyplot.figure()
    ax = pyplot.subplot(111)
    radius_min, radius_max = (points[2].min(), points[2].max())
    radius_range = radius_max - radius_min
    radius_min /= 2.0
    radius_max *= 2.0
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    msel = is_minsize(points[2])
    draw_craters(points[:,msel], c='r', lw=0.25)
    draw_craters(points[:,numpy.logical_not(msel)], c='r', lw=0.5)
    if truth is not None:
        draw_craters(truth, c='g', lw=2)
    draw_craters(crater_mean, c='b', lw=1)
    pyplot.savefig(output_filename_base+'_craters.png', dpi=300)

    
def plot_cluster_diagnostics(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base):
    pyplot.figure(figsize=(12.,6.))
    ax = pyplot.subplot(131)
    radius_min, radius_max = (points[2].min(), points[2].max())
    radius_range = radius_max - radius_min
    radius_min /= 2.0
    radius_max *= 2.0
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))

    pyplot.plot(crater_mean[0], crater_mean[1], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points[0], points[1], '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('lat')
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    ax = pyplot.subplot(132)
    pyplot.plot(crater_mean[0], numpy.log10(crater_mean[2]), 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points[0], numpy.log10(points[2]), '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('log10(radius)')
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(log10radius_min, log10radius_max)
    ax = pyplot.subplot(133)
    pyplot.plot(numpy.log10(crater_mean[2]), crater_mean[1], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(numpy.log10(points[2]), points[1], '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('log10(radius)')
    pyplot.ylabel('lat')
    ax.set_xlim(log10radius_min, log10radius_max)
    ax.set_ylim(lat_min, lat_max)
    pyplot.subplots_adjust(wspace=0.3, hspace=0.3, right=0.95, top=0.95)
    pyplot.savefig(output_filename_base+'_clusters.png', dpi=600)
    pyplot.close()

    
def timetest():
    import timeit
    print('Time: %f s'%min(timeit.repeat(stmt='mz_cluster.mz_cluster()', setup='import mz_cluster', repeat=3, number=1)))

    
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
                print('\n'+__doc__)
                print('More detail on mz_cluster: '+ mz_cluster.__doc__)
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
