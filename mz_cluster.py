#! /usr/bin/env python

"""mz_cluster.py - Perform clustering on MZ data.

    Version 2013-08-29

    Usage:
        mz_cluster.py <output_filename_base> <moonzoo_markings_csv> <expert_markings_csv>
                      <threshold> <mincount> <maxcount> <maxiter> <position_scale> <size_scale>
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
import scipy.cluster
#import fastcluster

# Some debugging tools:
from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)

matplotlib.rcParams.update({'font.size': 14})

# minimum size is still hardcoded - needs to adapt to NAC pixel scale,
# and preferably use knowledge of zoom level of each marking

lunar_radius = 1737.4*1000  # metres
degrees_per_metre = 360.0 / (2*pi*lunar_radius)

minsize_factor = 0.5  # downweight minsize markings by this factor

def mz_cluster(output_filename_base='mz_clusters', moonzoo_markings_csv='none', expert_markings_csv='none',
               threshold=1.0, mincount=2, maxcount=10, maxiter=3,
               position_scale=4.0, size_scale=0.4, min_user_weight=0.5,
               long_min=-720.0, long_max=720.0, lat_min=-360.0, lat_max=360.0):
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
    expert_markings_csv -- name of file containing expert craters
    threshold -- general scaling of the clustering linking length
    mincount -- minimum number of markings required for a crater
    maxcount -- expected maximum number of markings for a crater
    maxiter -- maximum number of iterations for splitting too-large clusters
    position_scale -- maximum positional difference for linking two markings,
                      normalised by the square root of the crater size
    size_scale -- maximum fractional size difference for linking two markings
    min_user_weight -- minimum user weight to be included at all
    long_min, long_max, lat_min, lat_max -- limits of region to consider

    This could incorporate user weighting in future, e.g. by assigning
    clusters scores based on the sum of the user weights for each
    clustered marking, and using a minscore rather than mincount.

    """
    print
    print('*** Start of mz_cluster ***\n')
    print('output_filename_base = %s\nmoonzoo_markings_csv = %s\nexpert_markings_csv = %s'%(output_filename_base, moonzoo_markings_csv, expert_markings_csv))
    print('threshold = %f\nmincount = %i\nmaxcount = %i\nmaxiter = %i'%(threshold, mincount, maxcount, maxiter))
    print('position_scale = %f\nsize_scale = %f\nmin_user_weight = %f'%(position_scale, size_scale, min_user_weight))
    print
    # set global variables for crater metric
    global pscale, sscale
    pscale = position_scale
    sscale = size_scale
    # read in all data
    test=False
    if moonzoo_markings_csv.lower() == 'none':
        # If no filename specified, generate and use test data
        test = True
        make_test_craters(ncraters=50, nobs=10)
        expert_markings_csv = 'truthcraters.csv'
        moonzoo_markings_csv = 'testcraters.csv'
    truth = None
    if expert_markings_csv.lower() != 'none':
        # If 'truth' data is supplied, use it in plots
        # robstest
        #data = numpy.genfromtxt(expert_markings_csv, delimiter=None, names=True)
        #truth = numpy.array([data['x'], data['y'], data['RIM_DIA']])
        #truth['radius'] /= 2.0  # fix diameter to radius
        # internal test
        truth = numpy.genfromtxt(expert_markings_csv, delimiter=',', names=True)
        datarange = (truth['long'].min(), truth['long'].max(), truth['lat'].min(), truth['lat'].max())
        print('Expert data covers region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
        if test:
            long_min, long_max, lat_min, lat_max = datarange
    # Get markings data
    points = numpy.recfromtxt(moonzoo_markings_csv, delimiter=',', names=True)
    points = points.view(numpy.ndarray)
    datarange = (points['long'].min(), points['long'].max(), points['lat'].min(), points['lat'].max())
    print('Markings cover region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%datarange)
    # Select region of interest
    print('Considering region: long=(%.3f, %.3f), lat=(%.3f, %.3f)'%(long_min, long_max, lat_min, lat_max))
    select = (points['long'] >= long_min) & (points['long'] <= long_max)
    select &= (points['lat'] >= lat_min) & (points['lat'] <= lat_max)
    # Get user weights
    print('\nGetting user weights')
    user_weights = get_user_weights(points['user'])
    user_weights_select = user_weights > min_user_weight
    user_weights_rejected = select.sum() - user_weights_select[select].sum()
    print('Removing %i of %i markings by users with very low weights'%(user_weights_rejected, select.sum()))
    select &= user_weights_select
    # Filter by user weight
    points = points[select]
    user_weights = user_weights[select]
    if truth is not None:
        select = (truth['long'] >= long_min) & (truth['long'] <= long_max)
        select &= (truth['lat'] >= lat_min) & (truth['lat'] <= lat_max)
        select &= truth['radius'] > points['radius'].min()  # remove small expert craters
        truth = truth[select]
    print('\nNumber of markings: %i'%points.shape[0])
    if expert_markings_csv is not None:
        print('Number of expert markings: %i'%truth.shape[0])
    # Perform clustering of markings
    p = numpy.array([points[name] for name in ('long', 'lat', 'radius', 'minsize')], numpy.double)
    clusters = iterative_fastclusterdata(p, threshold, maxcount, mincount, maxiter)
    # Previous clustering methods:
    ### clusters = fastclusterdata(p, t=threshold, criterion='distance', method='single', metric=crater_metric)
    ### clusters = dbscanclusterdata(p, t=threshold, m=mincount, metric=crater_metric)
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
            dra.extend(crater_absolute_position_metric(v, m))
            drs.extend(crater_position_metric(v, m))
            ds.extend(crater_size_metric(v, m))
            s.extend([crater_mean['radius'][i]]*crater_count[i])
            notmin.extend(notminsize)
    dra, drs, ds, s, notmin = map(numpy.array, (dra, drs, ds, s, notmin))
    # select final craters (should we also remove minsize craters?)
    ok = crater_score >= mincount
    crater_score = crater_score[ok]
    crater_count = crater_count[ok]
    crater_countnotmin = crater_countnotmin[ok]
    crater_mean = crater_mean[ok]
    crater_stdev = crater_stdev[ok]
    crater_mean = crater_mean[['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
    crater_stdev = crater_stdev[['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
    print('Found %i final clusters'%len(crater_count))
    # Write final crater catalogue to a csv file
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
    if truth is not None:
        matchval = compare(crater_mean, truth)
        print("\nMean metric distance between nearest neighbours: %.3f"%matchval)
    # Make some plots
    plot_cluster_stats(dra, drs, ds, s, notmin, output_filename_base)
    plot_crater_stats(crater_mean, truth, output_filename_base)
    plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base,
                 user_weights, crater_score)
    plot_cluster_diagnostics(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base)
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
    

def get_user_weights(userids, db='moonzoo'):
    import pymysql
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


def matchids(id1,id2):
    """ Match two sets of ids. 
        Returns: 
          ibest -- array of indices of i1 that match i2; -1 if no match
    """
    indices = numpy.argsort(id1)
    idsorted = id1[indices]
    ibest = []
    for i in range(len(id2)):
        j = matchidsorted(idsorted,id2[i])
        if j < 0:
            ibest += [j]
        else:
            ibest += [indices[j]]
    return numpy.array(ibest)


def matchidsorted(ids,targetid):
    """ Find id matches, return index in i1 that matches targetid; -1 if no match. """
    i1 = numpy.searchsorted(ids,targetid)
    if targetid == ids[i1]:
        ibest = i1
    else:
        ibest = -1 
    return ibest


def crater_metric(uin, vin):
    # get position and size differences
    dr = crater_position_metric(uin, vin) / pscale
    ds = crater_size_metric(uin, vin) / sscale
    # combine position and size differences
    dist = sqrt(dr**2 + ds**2)
    return dist


def crater_absolute_position_metric(uin, vin):
    # get coords
    long1, lat1, s1 = uin[:3]
    long2, lat2, s2 = vin[:3]
    # calculate crater position difference
    long1, long2, lat1, lat2 = [i*pi/180.0 for i in (long1, long2, lat1, lat2)]
    dr = lunar_radius * numpy.arccos(numpy.cos(lat1)*numpy.cos(lat2)*numpy.cos(long1-long2) + numpy.sin(lat1)*numpy.sin(lat2))
    return dr


def crater_position_metric(uin, vin):
    # get coords
    x1, y1, s1 = uin[:3]
    x2, y2, s2 = vin[:3]
    # calculate mean crater size
    sm = (s1 + s2)/2.0
    # calculate crater position difference
    dr = crater_absolute_position_metric(uin, vin) / numpy.sqrt(sm)
    return dr


def crater_size_metric(uin, vin):
    # get coords
    x1, y1, s1, m1 = uin[:4]
    x2, y2, s2, m2 = vin[:4]
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    neither_minsize = (1-m1) * (1-m2)
    ds = neither_minsize * numpy.abs(s1 - s2) / sm
    return ds


def draw_craters(points, c='r', lw=1, ls='solid'):
    for i, p in enumerate(points):
        x, y, r, q, theta, b = [p[name] for name in ['long', 'lat', 'radius', 'axialratio', 'angle', 'boulderyness']]
        crater = Ellipse((x, y), width=2*r*degrees_per_metre, height=2*q*r*degrees_per_metre, angle=theta,
                         color=c, fill=False, lw=lw, ls=ls, alpha=0.5)
        fig = pyplot.gcf()
        fig.gca().add_artist(crater)
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
    f = file('truthcraters.csv', 'w')
    f.write('long,lat,radius,axialratio,angle,boulderyness\n')
    for i in range(len(cx)):
        f.write('%f,%f,%f,%f,%f,%i\n'%(cx[i], cy[i], cr[i], 1.0, 0.0, 0))
    f.close()        
    f = file('testcraters.csv', 'w')
    f.write('long,lat,radius,axialratio,angle,boulderyness,minsize,user,truelabel\n')
    for i in range(len(x)):
        f.write('%f,%f,%f,%i,%f,%f,%i,%i,%i\n'%(x[i], y[i], r[i], 1.0, 0.0, 0, flag[i], 0, truelabel[i]))
    f.close()        
    #numpy.savetxt("testcraters.csv", p.transpose(), delimiter=",")


def compare(p1, p2):
    minsize1 = numpy.zeros(p1.shape[0], [('minsize', numpy.double)])
    minsize2 = numpy.zeros(p2.shape[0], [('minsize', numpy.double)])
    X1 = numpy.asarray([p1[name] for name in ('long', 'lat', 'radius')]+[minsize1['minsize']], order='c', dtype=numpy.double)
    X2 = numpy.asarray([p2[name] for name in ('long', 'lat', 'radius')]+[minsize2['minsize']], order='c', dtype=numpy.double)
    return comparedata(numpy.array([0.0, 0.0]), X1, X2)


def comparedata(shift, X1, X2, metric=crater_metric):
    dX = numpy.zeros((X2.shape[0],1), numpy.double)
    # shift input in rough metres as seems to increase speed
    dX[:2,0] = shift * degrees_per_metre
    X2 = X2+dX
    Y = scipy.cluster.hierarchy.distance.cdist(X1.T, X2.T, metric=metric)
    M = Y.min(numpy.argmax(Y.shape)).mean()
    return M


def fastclusterdata(X, t, criterion='distance', metric=crater_metric, method='single'):
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
    T = scipy.cluster.hierarchy.fcluster(Z, criterion=criterion, t=t)
    return T


def dbscanclusterdata(X, t, m, metric=crater_metric):
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
    pyplot.figure(figsize=(6., 8.))
    pyplot.plot([0.5, 2.7], [3.5, 0.5], ':k')
    sf_bins_clust, sf_clust = plot_sizefreq(2*crater_mean['radius'], label='clustered')
    if truth is not None:
        print
        sf_bins_truth, sf_truth = plot_sizefreq(2*truth['radius'], sf_bins_clust, label='truth')
        ok = (sf_clust > 0) & (sf_truth > 0)
        delta = sf_clust[ok].astype(numpy.float)/sf_truth[ok] - 1
        text = 'mean_delta = %.3f'%delta.mean()
        print text
        pyplot.text(1.0, 10**1.0, text)
        text = 'med_delta = %.3f'%numpy.median(delta)
        print text
        pyplot.text(1.0, 10**0.8, text)
        text = 'rms_delta = %.3f'%numpy.sqrt((delta**2).mean())
        print text    
        pyplot.text(1.0, 10**0.6, text)
        text = 'mad_delta = %.3f'%numpy.median(numpy.abs(delta))
        print text
        pyplot.text(1.0, 10**0.4, text)
    pyplot.axis(xmin=0.5, xmax=2.7, ymin=0.5, ymax=3.5)
    pyplot.xlabel('log10(diameter [m])')
    pyplot.ylabel('cumulative frequency')
    pyplot.legend(loc='lower left')
    pyplot.savefig(output_filename_base+'_sizefreq.pdf', dpi=300)
    pyplot.close()


def plot_sizefreq(size, bins=10000, label=''):
    h, b = numpy.histogram(numpy.log10(size), bins)
    c = numpy.cumsum(h[::-1])
    c = c[::-1]
    c = numpy.concatenate((c[0:1], c))
    ax = pyplot.plot(b, c, ls='steps-pre', label=label)
    pyplot.gca().set_yscale('log')
    return b, c


def plot_craters(points, crater_mean, truth, long_min, long_max, lat_min, lat_max, output_filename_base,
                 user_weights=None, crater_score=None):
    pyplot.figure()
    ax = pyplot.subplot(111)
    radius_min, radius_max = (points['radius'].min(), points['radius'].max())
    radius_range = radius_max - radius_min
    radius_min /= 2.0
    radius_max *= 2.0
    log10radius_min, log10radius_max = numpy.log10((radius_min, radius_max))
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    msel = points['minsize'].astype(numpy.bool)
    draw_craters(points[msel], c='r', lw=0.25)
    draw_craters(points[numpy.logical_not(msel)], c='r', lw=0.5)
    if truth is not None:
        draw_craters(truth, c='g', lw=2)
    draw_craters(crater_mean, c='b', lw=1)
    pyplot.savefig(output_filename_base+'_craters.pdf', dpi=300)
    # pyplot.clf()
    # if (user_weights is not None) or (crater_score is not None):
    #     if user_weights is not None:
    #         draw_craters(points, c='r', lw=user_weights)
    #     if crater_score is not None:
    #         draw_craters(crater_mean, c='b', lw=crater_score, alpha=0.5)
    #     pyplot.savefig(output_filename_base+'_crater_weights.pdf', dpi=300)

    
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
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(lat_min, lat_max)
    ax = pyplot.subplot(132)
    pyplot.plot(crater_mean['long'], numpy.log10(crater_mean['radius']), 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(points['long'], numpy.log10(points['radius']), '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('long')
    pyplot.ylabel('log10(radius)')
    ax.set_xlim(long_min, long_max)
    ax.set_ylim(log10radius_min, log10radius_max)
    ax = pyplot.subplot(133)
    pyplot.plot(numpy.log10(crater_mean['radius']), crater_mean['lat'], 'o', markersize=4,
                mfc='white', mec='blue')
    pyplot.plot(numpy.log10(points['radius']), points['lat'], '.', mfc='red', mec='red', alpha=0.25, markersize=2)
    pyplot.xlabel('log10(radius)')
    pyplot.ylabel('lat')
    ax.set_xlim(log10radius_min, log10radius_max)
    ax.set_ylim(lat_min, lat_max)
    pyplot.subplots_adjust(wspace=0.3, hspace=0.3, right=0.95, top=0.95)
    pyplot.savefig(output_filename_base+'_clusters.pdf', dpi=600)
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
        output = args[0]+'_craters.csv'
        if os.path.exists(output) and (not clobber):
            raise Usage("Output file already exists: %s\nUse -f to overwrite."%output)
        mz_cluster(*args)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "For help use --help"
        return 2

    
if __name__ == "__main__":
    sys.exit(main())
