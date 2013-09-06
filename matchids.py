import numpy

def matchids(id1,id2):
    """ Match two sets of ids. 
        Returns: 
          ibest -- array of indices of i1 that match i2; -1 if no match
    """
    indices = numpy.argsort(id1)
    idsorted = id1[indices]
    n = len(id2)
    ibest = numpy.zeros(n, dtype=numpy.int)
    for i in range(n):
        j = matchidsorted(idsorted,id2[i])
        if j >= 0:
            ibest[i] = indices[j]
    return ibest


def matchidsorted(ids, targetid):
    """ Find id matches, return index in i1 that matches targetid; -1 if no match. """
    i1 = numpy.searchsorted(ids,targetid)
    if i1 < len(ids) and targetid == ids[i1]:
        ibest = i1
    else:
        ibest = -1 
    return ibest
