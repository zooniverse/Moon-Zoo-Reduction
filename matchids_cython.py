import numpy
cimport numpy

DTYPE = numpy.int
ctypedef numpy.int_t DTYPE_t

def matchids(numpy.ndarray[DTYPE_t, ndim=1] id1, numpy.ndarray[DTYPE_t, ndim=1] id2):
    """ Match two sets of ids. 
        Returns: 
          ibest -- array of indices of i1 that match i2; -1 if no match
    """
    assert id1.dtype == DTYPE and id2.dtype == DTYPE
    cdef numpy.ndarray[DTYPE_t, ndim=1] indices, idsorted, ibest
    cdef i, n, j
    indices = numpy.argsort(id1)
    idsorted = id1[indices]
    n = len(id2)
    ibest = numpy.zeros(n, dtype=DTYPE)
    for i in range(n):
        j = matchidsorted(idsorted,id2[i])
        if j >= 0:
            ibest[i] = indices[j]
    return ibest


cpdef int matchidsorted(numpy.ndarray[DTYPE_t, ndim=1] ids, int targetid):
    """ Find id matches, return index in i1 that matches targetid; -1 if no match. """
    assert ids.dtype == DTYPE
    cdef int i1, ibest
    i1 = numpy.searchsorted(ids,targetid)
    if i1 < len(ids) and targetid == ids[i1]:
        ibest = i1
    else:
        ibest = -1 
    return ibest
