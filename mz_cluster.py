#! /usr/bin/env python

"""mz_cluster.py - Perform clustering on MZ data.

    Version 2014-02-26

    Usage:
        mz_cluster.py <output_filename_base> <moonzoo_markings_csv> <nac_names> <expert_markings_csv>
                      <image> <threshold> <mincount> <maxcount> <maxiter> <position_scale> <size_scale>
                      <min_user_weight> <long_min> <long_max> <lat_min> <lat_max>

    Note that the csv files must contain column headers, including 'long', 'lat' and 'xradius'.
    
    Usage example:
        python mz_cluster.py mz_clusters data/M104311715/craters_RE_latlong.csv data/M104311715/715_xpert.csv 

"""

import os, sys, getopt
from string import strip
from math import sqrt, pi
import numpy
import matplotlib
matplotlib.use('PDF')
import matplotlib.pyplot as pyplot
from matplotlib.patches import Ellipse
from scipy.optimize import fmin_powell as fmin
from scipy.stats import scoreatpercentile, ks_2samp
import scipy.cluster
import fastcluster
from collections import Container
from numpy.lib.recfunctions import append_fields
import pymysql

# Some debugging tools:
#from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)

# Cython auto compilation
import pyximport; pyximport.install(setup_args={"include_dirs":numpy.get_include()})
from matchids import matchids
import crater_metrics
from crater_metrics import crater_cdist, crater_pdist, crater_absolute_position_metric, crater_position_metric, crater_size_metric,lunar_radius, crater_metric_one as crater_metric

matplotlib.rcParams.update({'font.size': 14})

degrees_per_metre = 360.0 / (2*pi*lunar_radius)

minsize_factor = 0.5  # downweight minsize markings by this factor

def mz_cluster(output_filename_base='mz_clusters', moonzoo_markings_csv='none',
               nac_names='none', expert_markings_csv='none', image='none',
               threshold=1.0, mincount=2.0, maxcount=10, maxiter=3,
               position_scale=0.2, size_scale=0.2, min_user_weight=0.5,
               long_min=-1.0, long_max=361.0, lat_min=-91.0, lat_max=91.0):
    #long_min=30.655, long_max=30.800, lat_min=20.125, lat_max=20.255):
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
    nac_names -- comma separated list of all NAC names contributing to markings file
    expert_markings_csv -- name of file containing expert craters
    image -- image to put underneath crater plots
    threshold -- general scaling of the clustering linking length
    mincount -- minimum number of markings required for a crater
    maxcount -- expected maximum number of markings for a crater
    maxiter -- maximum number of iterations for splitting too-large clusters
    position_scale -- maximum positional difference for linking two markings,
                      normalised by the crater size
    size_scale -- maximum fractional size difference for linking two markings
    min_user_weight -- minimum user weight to be included at all
                       if this is >= 100, then user weights are ignored
    long_min, long_max, lat_min, lat_max -- limits of region to consider
    
    This could incorporate user weighting in future, e.g. by assigning
    clusters scores based on the sum of the user weights for each
    clustered marking, and using a minscore rather than mincount.

    """
    print
    print('*** Start of mz_cluster ***\n')
    print('output_filename_base = %s\nmoonzoo_markings_csv = %s\nexpert_markings_csv = %s'%(output_filename_base, moonzoo_markings_csv, expert_markings_csv))
    print('threshold = %f\nmincount = %f\nmaxcount = %i\nmaxiter = %i'%(threshold, mincount, maxcount, maxiter))
    print('position_scale = %f\nsize_scale = %f\nmin_user_weight = %f'%(position_scale, size_scale, min_user_weight))
    print
    # set variables for crater metric
    crater_metrics.pscale = position_scale
    crater_metrics.sscale = size_scale
    # read in all data
    nac_names = nac_names.upper().split(',')
    test=False
    if moonzoo_markings_csv.lower() == 'none':
        # If no filename specified, generate and use test data
        test = True
        make_test_craters(ncraters=100, nobs=10)
        expert_markings_csv = 'truthcraters.csv'
        moonzoo_markings_csv = 'testcraters.csv'
    truth = None
    if expert_markings_csv.lower() != 'none':
        # If 'truth' data is supplied, use it in plots
        truth = numpy.genfromtxt(expert_markings_csv, delimiter=',', names=True)
        if truth.dtype.names[:3] != ('long', 'lat', 'radius'):
            # this is a cat from Rob, rather than an internal test cat
            # the format of these files changes every time
            #truth.dtype.names = ('long', 'lat', 'radius') + truth.dtype.names[3:]
            truth.dtype.names = ('radius', 'x', 'y', 'long', 'lat')
            #truth['radius'] /= 2.0  # fix diameter to radius
            n = len(truth)
            truth = numpy.rec.fromarrays([truth['long'], truth['lat'], truth['radius'],
                                          numpy.ones(n, numpy.float), numpy.zeros(n, numpy.float),
                                          numpy.zeros(n, numpy.float)],
                                          names=('long', 'lat', 'radius', 'axialratio', 'angle',
                                                 'boulderyness'))
        datarange = (truth['long'].min(), truth['long'].max(), truth['lat'].min(), truth['lat'].max())
        print('Expert data covers region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
        if test:
            long_min, long_max, lat_min, lat_max = datarange
    # Get markings data
    points = numpy.recfromtxt(moonzoo_markings_csv, delimiter=',', names=True)
    if points.dtype.names[:3] != ('long', 'lat', 'radius'):
        # this is a cat from Rob, rather than one produced from the pipeline
        points.dtype.names = ('long', 'lat', 'radius') + points.dtype.names[3:]
        n = len(points)
        points = numpy.rec.fromarrays([points['long'], points['lat'], points['radius'],
                                       numpy.ones(n, numpy.float), numpy.zeros(n, numpy.float),
                                       numpy.zeros(n, numpy.float), numpy.zeros(n, numpy.bool),
                                       numpy.zeros(n, numpy.int)],
                                       names=('long', 'lat', 'radius', 'axialratio', 'angle',
                                              'boulderyness', 'minsize', 'user'))
    datarange = (points['long'].min(), points['long'].max(), points['lat'].min(), points['lat'].max())
    print('Markings cover region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
    # Select region of interest
    print('Considering region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%(long_min, long_max, lat_min, lat_max))
    select = (points['long'] >= long_min) & (points['long'] <= long_max)
    select &= (points['lat'] >= lat_min) & (points['lat'] <= lat_max)
    # Get user weights
    if min_user_weight >= 100:
        print('\nIgnoring user weights')
        user_weights = numpy.ones(len(points), numpy.float)
    else:
        print('\nGetting user weights')
        user_weights = get_user_weights(points['user'])
        user_weights_select = user_weights > min_user_weight
        user_weights_rejected = select.sum() - user_weights_select[select].sum()
        print('Removing %i of %i markings by users with very low weights'%(user_weights_rejected, select.sum()))
        select &= user_weights_select
    # Filter by user weight
    points = points[select]
    user_weights = user_weights[select]
    smallest_radius = points['radius'].min()
    smallest_expert_radius = truth['radius'].min() if truth is not None else 0.0
    if truth is not None:
        select = (truth['long'] >= long_min) & (truth['long'] <= long_max)
        select &= (truth['lat'] >= lat_min) & (truth['lat'] <= lat_max)
        select &= truth['radius'] > smallest_radius  # remove small expert craters
        truth = truth[select]
    print('\nNumber of markings: %i'%points.shape[0])
    print('Radius of smallest marking: %.3f'%smallest_radius)
    if truth is not None:
        print('Number of expert markings: %i'%truth.shape[0])
        print('Radius of smallest expert marking: %.3f'%smallest_expert_radius)
    # Perform clustering of markings
    p = numpy.array([points[name] for name in ('long', 'lat', 'radius', 'minsize')], numpy.double)
    p[0:2] *= pi/180.0
    clusters = iterative_fastclusterdata(p, threshold, maxcount, mincount, maxiter)
    # Previous clustering methods:
    ### clusters = fastclusterdata(p, t=threshold, criterion='distance', method='single')
    ### clusters = dbscanclusterdata(p, t=threshold, m=mincount)
    ### clusters = scipy.cluster.hierarchy.fclusterdata(p, t=threshold, criterion='distance', method='single', metric='euclidean')
    ### clusters = scipy.cluster.hierarchy.fclusterdata(p, t=threshold, criterion='inconsistent', method='single', metric='euclidean')
    # Calculate clustered crater properties and useful stats
    # while eliminating clusters with too few markings
    nclusters = clusters.max()
    print('\nFound %i initial clusters'%nclusters)
    crater_mean = numpy.zeros(nclusters, [('long', numpy.float), ('lat', numpy.float), ('radius', numpy.float), ('minsize', numpy.float), ('axialratio', numpy.float), ('angle', numpy.float), ('boulderyness', numpy.float)])
    crater_stdev = numpy.zeros(nclusters, [('long', numpy.float), ('lat', numpy.float), ('radius', numpy.float), ('minsize', numpy.float), ('axialratio', numpy.float), ('angle', numpy.float), ('boulderyness', numpy.float)])
    crater_count = numpy.zeros(nclusters, numpy.int)
    crater_score = numpy.zeros(nclusters, numpy.float)
    crater_countnotmin = numpy.zeros(nclusters, numpy.int)
    dra = []
    drs = []
    ds = []
    s = []
    notmin = []
    for i in range(nclusters):
        p = points[clusters == i+1]
        w = user_weights[clusters == i+1]
        v = numpy.array([p[name] for name in ('long', 'lat', 'radius', 'minsize', 'axialratio', 'angle', 'boulderyness')], dtype=numpy.double)
        crater_count[i] = p.shape[0]
        crater_mean[i] = v.mean(-1)
        crater_stdev[i] = v.std(-1)
        minsize = p['minsize'].astype(numpy.bool)
        notminsize = numpy.logical_not(minsize)
        crater_score[i] = w[notminsize].sum() + (minsize_factor * w[minsize]).sum()
        crater_countnotmin[i] = notminsize.sum()
        if crater_countnotmin[i] > 0:
            crater_mean['radius'][i] = p['radius'][notminsize].mean()
            crater_stdev['radius'][i] = p['radius'][notminsize].std()
            crater_mean['axialratio'][i] = p['axialratio'][notminsize].mean()
            crater_stdev['axialratio'][i] = p['axialratio'][notminsize].std()
            crater_mean['angle'][i] = p['angle'][notminsize].mean()
            crater_stdev['angle'][i] = p['angle'][notminsize].std()
        bouldery = p['boulderyness'] > 0
        if bouldery.sum() > 0:
            crater_mean['boulderyness'][i] = p['boulderyness'][bouldery].mean()
            crater_stdev['boulderyness'][i] = p['boulderyness'][bouldery].std()
        if crater_count[i] >= mincount:
            crater_mean['minsize'][i] = 0
            m = numpy.array([crater_mean[name][i] for name in ('long', 'lat', 'radius', 'minsize')], numpy.double)
            v[0:2] *= pi/180.0
            m[0:2] *= pi/180.0
            dra.extend(crater_absolute_position_metric(m, v.T))
            drs.extend(crater_position_metric(m, v.T))
            ds.extend(crater_size_metric(m, v.T))
            s.extend([crater_mean['radius'][i]]*crater_count[i])
            notmin.extend(notminsize)
    dra, drs, ds, s, notmin = map(numpy.array, (dra, drs, ds, s, notmin))
    # select final craters exceeding specified score
    # also reject craters with one or fewer notmin markings
    ok = (crater_score >= mincount) & (crater_countnotmin > 1)
    crater_score = crater_score[ok]
    crater_count = crater_count[ok]
    crater_countnotmin = crater_countnotmin[ok]
    crater_mean = crater_mean[ok]
    crater_stdev = crater_stdev[ok]
    crater_mean = crater_mean[['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
    crater_stdev = crater_stdev[['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
    print('Found %i final clusters'%len(crater_count))

    crater_mean_for_comparison = crater_mean[crater_mean['radius'] > smallest_expert_radius]
    print('Only computing stats for set of %i craters larger than smallest truth crater'%len(crater_mean_for_comparison))

    # Write final crater catalogue to a csv file
    write_crater_cat(output_filename_base, crater_mean, crater_stdev, crater_score, crater_count, crater_countnotmin)
    # Make some plots
    plot_cluster_stats(dra, drs, ds, s, notmin, output_filename_base)
    plot_crater_stats(crater_mean_for_comparison, truth, output_filename_base)
    plot_cluster_diagnostics(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base)
    plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base, user_weights, crater_score, img=image)
    if len(nac_names) > 0 and nac_names != 'NONE':
        plot_coverage(long_min, long_max, lat_min, lat_max, output_filename_base, nac_names=nac_names, img=image)

    if truth is not None:
        matchval = compare(crater_mean_for_comparison, truth)
        print("\nMedian metric distance between nearest neighbours: %.3f"%matchval)

    if truth is not None:
        # And now computing and applying offsets...
        print('\nDetermining position offset between clustered craters and truth')
        offset = find_offset(truth, crater_mean_for_comparison)
        crater_mean_for_comparison = apply_offset(crater_mean_for_comparison, offset)
        crater_mean = apply_offset(crater_mean, offset)
        points = apply_offset(points, offset)
        output_filename_base += '_offset'
        # Write final offset crater catalogue to a csv file
        write_crater_cat(output_filename_base, crater_mean, crater_stdev, crater_score, crater_count, crater_countnotmin)
        # Make some plots
        plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base,
                     user_weights, crater_score, img=image)
        if truth is not None:
            matchval = compare(crater_mean_for_comparison, truth)
            print("\nMedian metric distance between nearest neighbours after offset: %.3f"%matchval)
    
    # If this is a test we know the true clustering, which can be used to evaluate performance
    if test:
        from sklearn import metrics
        labels_true = points['truelabel']
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
    

def write_crater_cat(output_filename_base, crater_mean, crater_stdev, crater_score, crater_count, crater_countnotmin):
    fout = open(output_filename_base+'_craters.csv', 'w')
    fout.write('long,long_std,lat,lat_std,radius,radius_std,axialratio,axialratio_std,angle,angle_std,boulderyness,boulderyness_std,score,count,countnotmin\n')
    outarray = numpy.zeros((15, crater_mean.shape[0]), numpy.float)
    outarray[:-3:2] = [crater_mean[n] for n in crater_mean.dtype.names]
    outarray[1:-3:2] = [crater_stdev[n] for n in crater_stdev.dtype.names]
    outarray[-3] = crater_score
    outarray[-2] = crater_count
    outarray[-1] = crater_countnotmin
    numpy.savetxt(fout, outarray.T, delimiter=", ", fmt='%.6f')
    fout.close()

    
def get_user_weights(userids, db='moonzoo'):
    if (userids == 0).all():
        return numpy.ones(len(userids), numpy.float)
    else:
        db = pymysql.connect(host="localhost", user="root", passwd="", db=db)
        cur = db.cursor() 
        sql = """SELECT zooniverse_user_id, weight
                 FROM user_weights"""
        cur.execute(sql)
        data = numpy.rec.fromrecords(cur.fetchall())
        db.close()
        match = matchids(data['f0'], userids.astype(numpy.int))
        return data['f1'][match].astype(numpy.float)
    

def draw_craters(points, c='r', lw=1, ls='solid', alpha=0.5):
    if not isinstance(lw, Container):
        lw = numpy.zeros(len(points)) + lw
    ax = pyplot.gcf().gca()
    for i, p in enumerate(points):
        x, y, r, q, theta, b = [p[name] for name in ['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
        crater = Ellipse((x, y), width=2*r*degrees_per_metre, height=2*q*r*degrees_per_metre, angle=theta,
                         color=c, fill=False, lw=lw[i], ls=ls, alpha=alpha)
        ax.add_artist(crater)
    pyplot.xlabel('long')
    pyplot.ylabel('lat')
    

def make_test_craters(ncraters=10, nobs=10, pmin=0.1, pwrong=0.15):
    scale = numpy.sqrt(ncraters/10.0) * 100
    # true craters
    cx = numpy.random.normal(scale*4, scale*2, size=ncraters)
    cy = numpy.random.normal(scale*4, scale*2, size=ncraters)
    cr = numpy.random.uniform(7.4, scale/3.0, size=ncraters)
    # test craters
    x = numpy.zeros(ncraters*nobs, numpy.float)
    y = numpy.zeros(ncraters*nobs, numpy.float)
    r = numpy.zeros(ncraters*nobs, numpy.float)
    truelabel = numpy.zeros(ncraters*nobs, numpy.int)
    flag = numpy.zeros(ncraters*nobs, numpy.int)
    for i in range(nobs):
        x[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cx, numpy.sqrt(cr)/1.0)
        y[i*ncraters:(i+1)*ncraters] = numpy.random.normal(cy, numpy.sqrt(cr)/1.0)
        r[i*ncraters:(i+1)*ncraters] = numpy.maximum(numpy.random.normal(cr, cr/5.0), 7.4)
        truelabel[i*ncraters:(i+1)*ncraters] = numpy.arange(ncraters)+1
        for j in range(ncraters):
            # some of the time get the position completely wrong
            if numpy.random.random() < pwrong:
                x[i*ncraters+j], y[i*ncraters+j] = numpy.random.normal(scale*4, scale*2, size=2)
                flag[i*ncraters+j] = 0
                truelabel[i*ncraters+j] = 0
            # some of the time set the crater to a minimum size
            if numpy.random.random() < pmin:
                r[i*ncraters+j] = 7.4
                flag[i*ncraters+j] = 1
    # convert x,y in metres into long,lat
    x, y, cx, cy = numpy.multiply((x, y, cx, cy), degrees_per_metre)
    offset = 0.001
    f = file('truthcraters.csv', 'w')
    f.write('long,lat,radius,axialratio,angle,boulderyness\n')
    for i in range(len(cx)):
        f.write('%f,%f,%f,%f,%f,%i\n'%(cx[i]+offset, cy[i]+offset, cr[i], 1.0, 0.0, 0))
    f.close()        
    f = file('testcraters.csv', 'w')
    f.write('long,lat,radius,axialratio,angle,boulderyness,minsize,user,truelabel\n')
    for i in range(len(x)):
        f.write('%f,%f,%f,%i,%f,%f,%i,%i,%i\n'%(x[i], y[i], r[i], 1.0, 0.0, 0, flag[i], 0, truelabel[i]))
    f.close()        
    #numpy.savetxt("testcraters.csv", p.transpose(), delimiter=",")

    
def find_offset(p1, p2):
    datarange = (p1['long'].min(), p1['long'].min(), p1['long'].max(), p1['lat'].min(), p1['lat'].max())    
    long_min = max(p1['long'].min(), p2['long'].min())
    long_max = min(p1['long'].max(), p2['long'].max())
    lat_min = max(p1['lat'].min(), p2['lat'].min())
    lat_max = min(p1['lat'].max(), p2['lat'].max())
    select = (p1['long'] >= long_min) & (p1['long'] <= long_max) & (p1['lat'] >= lat_min) & (p1['lat'] <= lat_max)
    p1 = p1[select]
    select = (p2['long'] >= long_min) & (p2['long'] <= long_max) & (p2['lat'] >= lat_min) & (p2['lat'] <= lat_max)
    p2 = p2[select]
    if len(p1) < 1 or len(p2) < 1:
        print('Too few craters to find offset')
        return [0.0, 0.0]
    if len(p1) > 100 and len(p2) > 100:
        big = scoreatpercentile(p1['radius'], 75)
        big = min(big, scoreatpercentile(p2['radius'], 75))
        p1 = p1[p1['radius'] > big]
        p2 = p2[p2['radius'] > big]
    minsize1 = numpy.zeros(p1.shape[0], [('minsize', numpy.double)])
    minsize2 = numpy.zeros(p2.shape[0], [('minsize', numpy.double)])
    X1 = numpy.asarray([p1[name] for name in ('long', 'lat', 'radius')]+[minsize1['minsize']], order='c', dtype=numpy.double)
    X2 = numpy.asarray([p2[name] for name in ('long', 'lat', 'radius')]+[minsize2['minsize']], order='c', dtype=numpy.double)
    results = fmin(comparedata, [0.0, 0.0], args=(X1, X2), xtol=0.001, maxiter=1000)
    results *= degrees_per_metre  # convert from rough metres to degrees
    print('Found a shift of dlong = %e deg, dlat = %e deg'%tuple(results))
    return results


def apply_offset(p, offset):
    pnew = p.copy()
    pnew['long'] += offset[0]
    pnew['lat'] += offset[1]
    return pnew

    
def compare(p1, p2):
    minsize1 = numpy.zeros(p1.shape[0], [('minsize', numpy.double)])
    minsize2 = numpy.zeros(p2.shape[0], [('minsize', numpy.double)])
    X1 = numpy.asarray([p1[name] for name in ('long', 'lat', 'radius')]+[minsize1['minsize']], order='c', dtype=numpy.double)
    X2 = numpy.asarray([p2[name] for name in ('long', 'lat', 'radius')]+[minsize2['minsize']], order='c', dtype=numpy.double)
    return comparedata(numpy.array([0.0, 0.0]), X1, X2)


def comparedata(shift, X1, X2):
    dX = numpy.zeros((X2.shape[0],1), numpy.double)
    # shift input in rough metres as seems to increase speed
    dX[:2,0] = shift * degrees_per_metre
    X2 = X2+dX
    #Y = scipy.cluster.hierarchy.distance.cdist(X1.T, X2.T, metric=crater_metric)
    Y = crater_cdist(X1.T, X2.T)
    # mean is probably best for determining offsets, as varies smoothly
    M = numpy.mean(Y.min(numpy.argmax(Y.shape)))
    # median is probably a better measure of overall quality of a clustering
    #M = numpy.median(Y.min(numpy.argmax(Y.shape)))
    return M


def fastclusterdata(X, t, criterion='distance', method='single'):
    """
    scipy.cluster.hierarchy.fclusterdata modified to use fastcluster
    """
    X = numpy.asarray(X, order='c', dtype=numpy.double)

    if type(X) != numpy.ndarray or len(X.shape) != 2:
        raise TypeError('The observation matrix X must be an n by m numpy '
                        'array.')

    #Y = scipy.cluster.hierarchy.distance.pdist(X, metric=crater_metric)
    Y = crater_pdist(X)
    Z = fastcluster.linkage(Y, method=method)
    #Z = scipy.cluster.hierarchy.linkage(Y, method=method)
    T = scipy.cluster.hierarchy.fcluster(Z, criterion=criterion, t=t)
    return T


def dbscanclusterdata(X, t, m):
    """
    Attempt at using sklearn.DBSCAN - but no faster than fastcluster
    """
    from sklearn.cluster import DBSCAN

    X = numpy.asarray(X, order='c', dtype=numpy.double)

    if type(X) != numpy.ndarray or len(X.shape) != 2:
        raise TypeError('The observation matrix X must be an n by m numpy '
                        'array.')

    db = DBSCAN(eps=t, min_samples=m, metric=crater_metric).fit(X)
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
                                              method='single')
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
    pyplot.savefig(output_filename_base+'_size_ds.pdf', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.plot(s, drs, '.')
    pyplot.plot(x, x*0+4.0, '-')
    pyplot.xlabel('size')
    pyplot.ylabel('drs')
    pyplot.savefig(output_filename_base+'_size_drs.pdf', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.plot(s, dra, '.')
    pyplot.plot(x, 4.0*numpy.sqrt(x), '-')
    pyplot.xlabel('size')
    pyplot.ylabel('dra')
    pyplot.savefig(output_filename_base+'_size_dra.pdf', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    #pyplot.hist(ds, 100, histtype='stepfilled')
    pyplot.hist(ds[(ds > 1e-5) & notminsize], 100, histtype='stepfilled')
    pyplot.vlines(0.4, 0, pyplot.axis()[3])
    pyplot.axis(ymin=0)
    pyplot.xlabel('ds')
    pyplot.savefig(output_filename_base+'_hist_ds.pdf', dpi=300)
    pyplot.close()
    #
    pyplot.figure()
    pyplot.hist(drs, 100, histtype='stepfilled')
    pyplot.vlines(4.0, 0, pyplot.axis()[3])
    pyplot.axis(ymin=0)
    pyplot.xlabel('drs')
    pyplot.savefig(output_filename_base+'_hist_drs.pdf', dpi=300)
    pyplot.close()

    
def plot_crater_stats(crater_mean, truth, output_filename_base):
    plot_crater_sizefreq(crater_mean, truth, output_filename_base)
    plot_crater_cumsizefreq(crater_mean, truth, output_filename_base)


def plot_crater_sizefreq(crater_mean, truth, output_filename_base):
    pyplot.figure(figsize=(6., 8.))
    sf_bins_clust, sf_clust = plot_sizefreq(2*crater_mean['radius'], label='clustered')
    if truth is not None:
        print
        sf_bins_truth, sf_truth = plot_sizefreq(2*truth['radius'], sf_bins_clust, label='truth')
        ok = (sf_clust > 0) & (sf_truth > 0)
        D, p = ks_2samp(crater_mean['radius'], truth['radius'])
        text = 'KS D, p = %.3f, %.3f'%(D, p)
        pyplot.text(1.75, 100.0, text)
        print text
        #delta = (sf_clust[ok].astype(numpy.float) - sf_truth[ok])/sf_truth[ok]
        delta = (sf_clust[ok].astype(numpy.float) - sf_truth[ok])/numpy.sqrt(sf_truth[ok])
        text = 'mean_delta = %.3f'%delta.mean()
        print text
        pyplot.text(1.75, 95, text)
        text = 'med_delta = %.3f'%numpy.median(delta)
        print text
        pyplot.text(1.75, 90, text)
        text = 'rms_delta = %.3f'%numpy.sqrt((delta**2).mean())
        print text    
        pyplot.text(1.75, 85, text)
        text = 'mad_delta = %.3f'%numpy.median(numpy.abs(delta))
        print text
        pyplot.text(1.75, 80, text)
    pyplot.axis(xmin=0.8, xmax=3.0, ymin=0.0)
    pyplot.xlabel('log10(diameter [m])')
    pyplot.ylabel('frequency')
    pyplot.legend(loc='lower left')
    pyplot.savefig(output_filename_base+'_sizefreq.pdf', dpi=300)
    pyplot.close()


def plot_sizefreq(size, bins=10, label=''):
    h, b = numpy.histogram(numpy.log10(size), bins, range=(0.8, 3.0))
    c = 0.5*(b[:-1]+b[1:])
    err = numpy.sqrt(h)
    ax = pyplot.errorbar(c, h, yerr=err, ls='steps-mid', label=label)
    return b, h


def plot_crater_cumsizefreq(crater_mean, truth, output_filename_base):
    pyplot.figure(figsize=(6., 8.))
    pyplot.plot([0.8, 3.0], [10**3.5, 0.5], ':k')
    sf_bins_clust, sf_clust = plot_cumsizefreq(2*crater_mean['radius'], label='clustered')
    if truth is not None:
        print
        sf_bins_truth, sf_truth = plot_cumsizefreq(2*truth['radius'], sf_bins_clust, label='truth')
        ok = (sf_clust > 0) & (sf_truth > 0)
        delta = sf_clust[ok].astype(numpy.float)/sf_truth[ok] - 1
        text = 'cum_mean_delta = %.3f'%delta.mean()
        print text
        pyplot.text(1.0, 10**1.0, text)
        text = 'cum_med_delta = %.3f'%numpy.median(delta)
        print text
        pyplot.text(1.0, 10**0.8, text)
        text = 'cum_rms_delta = %.3f'%numpy.sqrt((delta**2).mean())
        print text    
        pyplot.text(1.0, 10**0.6, text)
        text = 'cum_mad_delta = %.3f'%numpy.median(numpy.abs(delta))
        print text
        pyplot.text(1.0, 10**0.4, text)
    pyplot.axis(xmin=0.8, xmax=3.0, ymin=0.5, ymax=10**3.5)
    pyplot.xlabel('log10(diameter [m])')
    pyplot.ylabel('cumulative frequency')
    pyplot.legend(loc='lower left')
    pyplot.savefig(output_filename_base+'_cumsizefreq.pdf', dpi=300)
    pyplot.close()


def plot_cumsizefreq(size, bins=10000, label=''):
    h, b = numpy.histogram(numpy.log10(size), bins)
    c = numpy.cumsum(h[::-1])
    c = c[::-1]
    c = numpy.concatenate((c[0:1], c))
    ax = pyplot.plot(b, c, ls='steps-pre', label=label)
    pyplot.gca().set_yscale('log')
    return b, c


def get_coverage(nac_names, point=None, db='moonzoo'):
    db = pymysql.connect(host="localhost", user="root", passwd="", db=db)
    cur = db.cursor() 
    nac_names = '("'+'","'.join(nac_names)+'")'
    if point is not None:
        point = 'and %f between long_min and long_max and %f between lat_min and lat_max'%point
    else:
        point = ''
    data = []
    for zoom in ("> 6", "between 2 and 6", "< 2"):
        sql = "SELECT nviews, zoom, long_min, long_max, lat_min, lat_max FROM slice_counts WHERE nac_name in %s and zoom %s %s;"%(nac_names, zoom, point)
        cur.execute(sql)
        names = [d[0] for d in cur.description]
        data.append(numpy.rec.fromrecords(cur.fetchall(), names=names))
    db.close()
    return data


def plot_image(img, ax, extent):
    if img is not None and img.lower() != 'none':
        import Image
        img = Image.open(img)
        a = numpy.asarray(img)
        ax.imshow(a, cmap='gray', extent=extent)


def plot_coverage(long_min, long_max, lat_min, lat_max, output_filename_base, 
                  nac_names=['M104311715RE'], img='../New_CC/ROI_715.png'):
    alpha = 0.1
    data = get_coverage(nac_names)
    fig, ax = pyplot.subplots(3, sharex=True, sharey=True)
    for i, datazoom in enumerate(data):
        plot_image(img, ax[i], (long_min, long_max, lat_min, lat_max))
        for nviews, zoom, long1, long2, lat1, lat2 in datazoom:
            if not (long2 < long_min or long1 > long_max or lat2 < lat_min or lat1 > lat_max):
                if nviews <= 2:
                    c = 'r'
                elif nviews >= 5:
                    c = 'g'
                else:
                    c = 'b'
                a = min(alpha*nviews, 1.0)
                ax[i].add_patch(pyplot.Rectangle((long1, lat1), long2-long1, lat2-lat1, facecolor=c, edgecolor='none', linewidth=0, alpha=a))
    y_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
    fig.subplots_adjust(hspace=0.05)
    for a in ax:
        a.set_autoscale_on(False)
        a.set_aspect('equal', adjustable='box-forced')
    for a in ax:
        a.yaxis.set_major_formatter(y_formatter)
        a.set_xbound(long_min, long_max)
        a.set_ybound(lat_min, lat_max)
        a.tick_params(labelsize=8)
    ax[-1].set_xlabel('longitude', fontsize=10)
    ax[1].set_ylabel('latitude', fontsize=10)
    pyplot.setp([a.get_xticklabels() for a in ax[:-1]], visible=False)
    pyplot.savefig(output_filename_base+'_coverage.pdf', dpi=300)
    pyplot.close()


def plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base,
                 user_weights=None, crater_score=None, img=None):
    pyplot.figure()
    ax = pyplot.subplot(111)
    radius_min, radius_max = (points['radius'].min(), points['radius'].max())
    radius_range = radius_max - radius_min
    radius_min /= 2.0
    radius_max *= 2.0
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))
    ax.set_xbound(long_min, long_max)
    ax.set_ybound(lat_min, lat_max)
    msel = points['minsize'].astype(numpy.bool)
    plot_image(img, ax, (long_min, long_max, lat_min, lat_max))
    draw_craters(points[msel], c='r', lw=0.25)
    draw_craters(points[numpy.logical_not(msel)], c='r', lw=0.5)
    if truth is not None:
        draw_craters(truth, c='g', lw=2)
    draw_craters(crater_mean, c='b', lw=1)
    pyplot.axis((long_min, long_max, lat_min, lat_max))
    ax.set_aspect('equal', adjustable='box')
    y_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.tick_params(labelsize=8)
    ax.set_xlabel('longitude', fontsize=10)
    ax.set_ylabel('latitude', fontsize=10)
    pyplot.savefig(output_filename_base+'_craters.pdf', dpi=300)
    pyplot.close()
    if (user_weights is not None) or (crater_score is not None):
        pyplot.figure()
        ax = pyplot.subplot(111)
        ax.set_xbound(long_min, long_max)
        ax.set_ybound(lat_min, lat_max)
        ax.yaxis.set_major_formatter(y_formatter)
        ax.set_xlabel('longitude', fontsize=10)
        ax.set_ylabel('latitude', fontsize=10)
        if user_weights is not None:
            draw_craters(points, c='r', lw=user_weights)
        if crater_score is not None:
            draw_craters(crater_mean, c='b', lw=crater_score/3.0, alpha=0.25)
        ax.set_aspect('equal')
        pyplot.savefig(output_filename_base+'_crater_weights.pdf', dpi=300)

    
def plot_cluster_diagnostics(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base):
    pyplot.figure(figsize=(12.,6.))
    ax = pyplot.subplot(131)
    radius_min, radius_max = (points['radius'].min(), points['radius'].max())
    radius_range = radius_max - radius_min
    radius_min /= 2.0
    radius_max *= 2.0
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))

    pyplot.plot(crater_mean['long'], crater_mean['lat'], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points['long'], points['lat'], '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('lat')
    ax.set_xbound(long_min, long_max)
    ax.set_ybound(lat_min, lat_max)
    ax = pyplot.subplot(132)
    pyplot.plot(crater_mean['long'], numpy.log10(crater_mean['radius']), 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points['long'], numpy.log10(points['radius']), '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('log10(radius)')
    ax.set_xbound(long_min, long_max)
    ax.set_ybound(log10radius_min, log10radius_max)
    ax = pyplot.subplot(133)
    pyplot.plot(numpy.log10(crater_mean['radius']), crater_mean['lat'], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(numpy.log10(points['radius']), points['lat'], '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('log10(radius)')
    pyplot.ylabel('lat')
    ax.set_xbound(log10radius_min, log10radius_max)
    ax.set_ybound(lat_min, lat_max)
    pyplot.subplots_adjust(wspace=0.3, hspace=0.3, right=0.95, top=0.95)
    pyplot.savefig(output_filename_base+'_clusters.pdf', dpi=600)
    pyplot.close()

    
def timetest():
    from timethis import timethis
    t = timethis('mz_cluster()', globals(), repeat=3, number=1)
    print('Time: %f s'%t)

    
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
            if i > 4:
                args[i] = float(args[i])
        if len(args) > 0:
            output = args[0]+'_craters.csv'
            if os.path.exists(output) and (not clobber):
                raise Usage("Output file already exists: %s\nUse -f to overwrite."%output)
            mz_cluster(*args)
        else:
            timetest()
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2

    
if __name__ == "__main__":
    sys.exit(main())
