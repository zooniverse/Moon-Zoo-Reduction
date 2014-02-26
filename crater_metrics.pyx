import numpy
cimport numpy
from numpy import *
import numexpr

pscale = 1.0
sscale = 1.0
lunar_radius = 1737.4*1000  # metres
cdef float lunar_diameter = 2 * lunar_radius

# these expect lat and long in radians!

DTYPE = numpy.double
ctypedef numpy.double_t DTYPE_t

def test(n=100):
    from scipy.spatial.distance import pdist, cdist
    from timethis import timethis
    x = random.normal(10, 1, (n, 4))
    y = random.normal(10, 1, (n, 4))
    x[:,3] = x[:,3] > 11.0
    y[:,3] = y[:,3] > 11.0
    d1 = crater_pdist(x)
    d2 = pdist(x, crater_metric_one)
    if (d1 == d2).all():
        print 'pdist match'
    else:
        print 'pdist do not match'
        return x, y, d1, d2
    t1 = timethis('crater_pdist(x)', globals(), locals())
    t2 = timethis('pdist(x, crater_metric_one)', globals(), locals())
    f = t1/t2
    print 'New pdist runs in a factor of %.3f of the time of the original'%f
    d1 = crater_cdist(x, y)
    d2 = cdist(x, y, crater_metric_one)
    if (d1 == d2).all():
        print 'cdist match'
    else:
        print 'cdist do not match'
        return x, y, d1, d2
    t1 = timethis('crater_cdist(x, y)', globals(), locals())
    t2 = timethis('cdist(x, y, crater_metric_one)', globals(), locals())
    f = t1/t2
    print 'New cdist runs in a factor of %.3f of the time of the original'%f
    
def crater_pdist(numpy.ndarray[DTYPE_t, ndim=2] X):
    cdef numpy.ndarray[DTYPE_t, ndim=1] x, dm
    cdef int m, i, k
    m = X.shape[0]
    dm = zeros((m * (m - 1)) // 2, dtype=DTYPE)
    k = 0
    for i in xrange(0, m-1):
        x = crater_metric(X[i], X[i+1:m])
        dm[k:k+m-i-1] = x
        k += m-i-1
    return dm

def crater_cdist(numpy.ndarray[DTYPE_t, ndim=2] X1, numpy.ndarray[DTYPE_t, ndim=2] X2):
    cdef numpy.ndarray[DTYPE_t, ndim=1] x
    cdef numpy.ndarray[DTYPE_t, ndim=2] dm
    cdef int m, n, i, k
    m = X1.shape[0]
    n = X2.shape[0]
    dm = zeros((m, n), dtype=X1.dtype)
    for i in xrange(0, m):
        x = crater_metric(X1[i], X2)
        dm[i] = x
    return dm

cpdef numpy.ndarray[DTYPE_t, ndim=1] crater_metric_one(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=1] vin):
    cdef numpy.ndarray[DTYPE_t, ndim=2] vin2
    vin2 = numpy.array([vin])
    return crater_metric(uin, vin2)

cpdef numpy.ndarray[DTYPE_t, ndim=1] crater_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    cdef double long1, lat1, s1, m1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2, m2
    cdef numpy.ndarray[DTYPE_t, ndim=1] sm, neither_minsize, ds, hdLat, hdLong, x, dr, dist
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    neither_minsize = (1-m1) * (1-m2)
    ds = neither_minsize * abs(s1 - s2) / sm
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * arcsin(sqrt(x)) / sm
    # combine position and size differences
    dr /= pscale
    ds /= sscale
    dist = sqrt(dr**2 + ds**2)
    return dist

def crater_numexpr_metric(uin, vin):
    # this is not used as does not deliver any speed up over standard numpy
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater size difference
    ds = '(1-m1) * (1-m2) * abs(s1 - s2) / ((s1 + s2)/2.0)'
    # calculate crater position difference
    dr = 'lunar_diameter*arcsin(sqrt(sin((lat2 - lat1)/2.0)**2 + sin((long2 - long1)/2.0)**2 * cos(lat1) * cos(lat2))) / ((s1 + s2)/2.0)'
    # combine position and size differences
    dr /= pscale
    ds /= sscale
    dist = numexpr.evaluate('sqrt(('+dr+')**2 + ('+ds+')**2)')
    return dist

def crater_absolute_position_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    cdef double long1, lat1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2
    cdef numpy.ndarray[DTYPE_t, ndim=1] hdLat, hdLong, x, dr
    # get coords
    long1, lat1 = uin[:2]
    long2, lat2 = vin[:,:2].T
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * arcsin(sqrt(x))
    return dr

def crater_position_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    cdef double long1, lat1, s1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2
    cdef numpy.ndarray[DTYPE_t, ndim=1] sm, hdLat, hdLong, x, dr
    # get coords
    long1, lat1, s1 = uin[:3]
    long2, lat2, s2 = vin[:,:3].T
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * arcsin(sqrt(x)) / sm
    return dr

def crater_size_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    cdef double long1, lat1, s1, m1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2, m2
    cdef numpy.ndarray[DTYPE_t, ndim=1] sm, neither_minsize, ds
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    neither_minsize = (1-m1) * (1-m2)
    ds = neither_minsize * abs(s1 - s2) / sm
    return ds

