from libc.math cimport cos, sin, asin, sqrt

pscale = 1.0
sscale = 1.0
lunar_radius = 1737.4*1000  # metres

# these expect lat and long in radians!

def crater_metric(uin, vin):
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
    dr = lunar_radius * 2.0 * asin(sqrt(x))
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
