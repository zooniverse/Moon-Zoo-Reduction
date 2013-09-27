from numpy import *
import numexpr

pscale = 1.0
sscale = 1.0
lunar_radius = 1737.4*1000  # metres
lunar_diameter = 2 * lunar_radius

# these expect lat and long in radians!

def test():
    x = random.normal(0, 1, (5000, 4))
    crater_pdist(x)

def crater_pdist(X):
    m = X.shape[0]
    dm = zeros((m * (m - 1)) // 2, dtype=X.dtype)
    k = 0
    for i in xrange(0, m-1):
        x = crater_metric(X[i], X[i+1:m])
        dm[k:k+m-i-1] = x
        k += 1
    return dm

def crater_metric(uin, vin):
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
    dr = lunar_diameter * arcsin(sqrt(x))
    # combine position and size differences
    dist = sqrt(dr**2 + ds**2)
    return dist

def crater_numexpr_metric(uin, vin):
    # get coords
    long1, lat1, s1, m1 = uin[:4]
    long2, lat2, s2, m2 = vin[:,:4].T
    # calculate crater size difference
    ds = '(1-m1) * (1-m2) * abs(s1 - s2) / ((s1 + s2)/2.0)'
    # calculate crater position difference
    dr = 'lunar_diameter*arcsin(sqrt(sin((lat2 - lat1)/2.0)**2 + sin((long2 - long1)/2.0)**2 * cos(lat1) * cos(lat2)))'
    # combine position and size differences
    dist = numexpr.evaluate('sqrt(('+dr+')**2 + ('+ds+')**2)')
    return dist

