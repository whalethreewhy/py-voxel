cimport numpy
cimport cython
import numpy as np
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef numpy.ndarray[numpy.int_t, ndim=2] dict_to_numpy(dictitems,bint force_all = False):
    cdef numpy.ndarray[numpy.int_t, ndim=2] py_convertarray
    cdef int count
    cdef tuple r

    py_convertarray = np.empty((len(dictitems),5),dtype='int32')
    cdef int [:,:] convertarray = py_convertarray
    count = 0
    for r in dictitems:
        if r[1][1] == 1 or force_all:
            convertarray[count][0] = r[0][0]
            convertarray[count][1] = r[0][1]
            convertarray[count][2] = r[0][2]
            convertarray[count][3] = r[1][0]
            convertarray[count][4] = r[1][1]
            count+=1
    return np.asarray(convertarray[:count])