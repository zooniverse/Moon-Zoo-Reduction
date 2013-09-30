from libc.math cimport cos, sin, asin, sqrt
import numpy
cimport numpy
from numpy import *
import numexpr

pscale = 1.0
sscale = 1.0
lunar_radius = 1737.4*1000  # metres
lunar_diameter = 2 * lunar_radius
cdef float lunar_diameter = 2 * lunar_radius

# these expect lat and long in radians!

DTYPE = numpy.double
ctypedef numpy.double_t DTYPE_t

def test(n=1000):
    from scipy.scipy.cluster.hierarchy.distance import pdist, cdist
    from timeit import repeat
    x = random.normal(0, 1, (n, 4))
    y = random.normal(0, 1, (n, 4))
    d1 = crater_pdist(x)
    d2 = pdist(x, crater_metric)
    if (d1 == d2).all():
        print 'pdist match'
    t1 = timeit('crater_pdist(x)', 'from __main__ import f', repeat=10, number=1)
    t2 = timeit('pdist(x, crater_metric)', 'from __main__ import f', repeat=10, number=1)
    f = min(t1)/min(t2)
    print 'New pdist runs in a factor of %.2f of the time of the original'%f
    d1 = crater_cdist(x)
    d2 = cdist(x, y, crater_metric)
    if (d1 == d2).all():
        print 'cdist match'
    t1 = timeit('crater_cdist(x, y)', 'from __main__ import f', repeat=10, number=1)
    t2 = timeit('cdist(x, y, crater_metric)', 'from __main__ import f', repeat=10, number=1)
    f = min(t1)/min(t2)
    print 'New cdist runs in a factor of %.2f of the time of the original'%f
    
def crater_pdist(numpy.ndarray[DTYPE_t, ndim=2] X):
    assert X.dtype == DTYPE
    cdef numpy.ndarray[DTYPE_t, ndim=1] dm
    cdef int m, i, k
    m = X.shape[0]
    dm = zeros((m * (m - 1)) // 2, dtype=DTYPE)
    k = 0
    for i in xrange(0, m-1):
        x = crater_metric(X[i], X[i+1:m])
        dm[k:k+m-i-1] = x
        k += 1
    return dm

def crater_cdist(numpy.ndarray[DTYPE_t, ndim=2] X1, numpy.ndarray[DTYPE_t, ndim=2] X2):
    assert X1.dtype == DTYPE
    assert X2.dtype == DTYPE
    cdef numpy.ndarray[DTYPE_t, ndim=1] dm
    cdef int m, n, i, k
    m = X1.shape[0]
    n = X2.shape[0]
    dm = zeros(m * n, dtype=X.dtype)
    k = 0
    for i in xrange(0, m):
        x = crater_metric(X1[i], X2)
        dm[k:k+n] = x
        k += 1
    return dm

cpdef crater_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    assert uin.dtype == DTYPE
    assert vin.dtype == DTYPE
    cdef DTYPE long1, lat1, s1, m1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2, m2
    cdef numpy.ndarray[DTYPE_t, ndim=1] sm, neither_minsize, ds, hdLat, hdlong, x, dr, dist
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
    dr = lunar_diameter * arcsin(sqrt(x)) / sqrt(sm)
    # combine position and size differences
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
    dr = 'lunar_diameter*arcsin(sqrt(sin((lat2 - lat1)/2.0)**2 + sin((long2 - long1)/2.0)**2 * cos(lat1) * cos(lat2))) / sqrt((s1 + s2)/2.0)'
    # combine position and size differences
    dist = numexpr.evaluate('sqrt(('+dr+')**2 + ('+ds+')**2)')
    return dist

def crater_absolute_position_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    assert uin.dtype == DTYPE
    assert vin.dtype == DTYPE
    cdef DTYPE long1, lat1, s1, m1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2, m2
    cdef numpy.ndarray[DTYPE_t, ndim=1] hdLat, hdlong, x, dr, dist
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * arcsin(sqrt(x))
    return dr

def crater_position_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    assert uin.dtype == DTYPE
    assert vin.dtype == DTYPE
    cdef DTYPE long1, lat1, s1, m1
    cdef numpy.ndarray[DTYPE_t, ndim=1] long2, lat2, s2, m2
    cdef numpy.ndarray[DTYPE_t, ndim=1] sm, hdLat, hdlong, x, dr, dist
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * arcsin(sqrt(x)) / sqrt(sm)
    return dr

def crater_size_metric(numpy.ndarray[DTYPE_t, ndim=1] uin, numpy.ndarray[DTYPE_t, ndim=2] vin):
    assert uin.dtype == DTYPE
    assert vin.dtype == DTYPE
    cdef DTYPE long1, lat1, s1, m1
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

