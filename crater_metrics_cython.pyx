from libc.math cimport cos, sin, asin, sqrt
#from cython.parallel cimport prange
#cimport cython
import numpy
cimport numpy
from time import sleep

pscale = 1.0
sscale = 1.0
lunar_radius = 1737.4*1000  # metres
cdef float lunar_diameter = 2 * lunar_radius

# these expect lat and long in radians!

DTYPE = numpy.double
ctypedef numpy.double_t DTYPE_t


def test():
    x = numpy.random.normal(0, 1, (1000, 4))
    crater_pdist(x)

def crater_pdist(numpy.ndarray[DTYPE_t, ndim=2] X):
    assert X.dtype == DTYPE
    cdef numpy.ndarray[DTYPE_t, ndim=1] dm
    cdef int m, n, i, j, k

    m = X.shape[0]
    n = X.shape[1]
    dm = numpy.zeros((m * (m - 1)) // 2, dtype=DTYPE)
    dm2 = numpy.zeros((m * (m - 1)) // 2, dtype=DTYPE)

    #for i in xrange(0, m-1):
    #    for j in xrange(i + 1, m):
    #        k = (m-1)*i - (i-1)*i/2 + j - i - 1
    #        dm[k] = crater_metric(X[i], X[j])

    for i in xrange(0, m-1):
        # try doing in numpy way here
        k = (m-1)*i - (i-1)*i/2
        x = crater_numpy_metric(X[i], X[i+1:m])
        #print x.shape
        #print dm2[k:k+m-i-1].shape
        dm2[k:k+m-i-1] = x

    print (dm == dm2).all()

    return dm

def crater_numpy_metric(uin, vin):
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
    x = numpy.sin(hdLat)**2 + numpy.sin(hdLong)**2 * numpy.cos(lat1) * numpy.cos(lat2)
    dr = lunar_diameter * numpy.arcsin(numpy.sqrt(x))
    # combine position and size differences
    dist = numpy.sqrt(dr**2 + ds**2)
    return dist


cpdef crater_metric(object uin, object vin):
    cdef double long1, lat1, s1, m1
    cdef double long2, lat2, s2, m2
    cdef double sm, ds, neither_minsize, x, dr, dist
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:4]
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    neither_minsize = (1-m1) * (1-m2)
    ds = neither_minsize * abs(s1 - s2) / sm
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * asin(sqrt(x))
    # combine position and size differences
    dist = sqrt(dr**2 + ds**2)
    return dist


cpdef slow_crater_metric(object uin, object vin):
    cdef double dr, ds, dist
    # get position and size differences
    dr = crater_position_metric(uin, vin) / pscale
    ds = crater_size_metric(uin, vin) / sscale
    # combine position and size differences
    dist = sqrt(dr**2 + ds**2)
    return dist


cpdef double crater_absolute_position_metric(object uin, object vin):
    cdef double long1, lat1, s1
    cdef double long2, lat2, s2
    cdef double hdLat, hdLong, x, dr
    # get coords
    long1, lat1, s1 = uin[:3]
    long2, lat2, s2 = vin[:3]
    # calculate crater position difference
    hdLat = (lat2 - lat1)/2.0
    hdLong = (long2 - long1)/2.0
    x = sin(hdLat)**2 + sin(hdLong)**2 * cos(lat1) * cos(lat2)
    dr = lunar_diameter * asin(sqrt(x))
    return dr


cpdef double crater_position_metric(object uin, object vin):
    cdef double long1, lat1, s1
    cdef double long2, lat2, s2
    cdef double sm, dr
    # get coords
    long1, lat1, s1 = uin[:3]
    long2, lat2, s2 = vin[:3]
    # calculate mean crater size
    sm = (s1 + s2)/2.0
    # calculate crater position difference
    dr = crater_absolute_position_metric(uin, vin) / sqrt(sm)
    return dr


cpdef double crater_size_metric(object uin, object vin):
    cdef double long1, lat1, s1, m1
    cdef double long2, lat2, s2, m2
    cdef double sm, ds, neither_minsize
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:4]
    # calculate crater size difference
    sm = (s1 + s2)/2.0
    neither_minsize = (1-m1) * (1-m2)
    ds = neither_minsize * abs(s1 - s2) / sm
    return ds
