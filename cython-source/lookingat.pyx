from libc.math cimport sin
from libc.math cimport cos
import numpy as np
cimport numpy
cimport cython
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef numpy.ndarray[numpy.int32_t, ndim=1] lookingat(float x,float y,float z,float pitch,float yaw,numpy.ndarray[numpy.int32_t, ndim=2] notex):    
    cdef int breakloop = 0
    cdef int cubecheck
    cdef int distrange
    cdef float tempx
    cdef float tempy
    cdef float tempz
    cdef float cosyaw = cos((yaw))
    cdef float xmult = sin((pitch))*cosyaw
    cdef float zmult = cos((pitch))*cosyaw
    cdef float ymult = -1*sin((yaw))
    
    cdef int [:,:] notexture = notex
    try:
        for cubecheck in range(len(notex)):
            for distrange in range(1,36):
                tempx = x + xmult*distrange/6
                tempz = z - zmult*distrange/6
                tempy = y + ymult*distrange/6
                if tempx >= notexture[cubecheck][0]-0.5 and tempx <= notexture[cubecheck][0]+0.5:
                    if tempy >= notexture[cubecheck][1]-0.5 and tempy <= notexture[cubecheck][1]+0.5:
                        if tempz >= notexture[cubecheck][2]-0.5 and tempz <= notexture[cubecheck][2]+0.5:
                            return np.asarray(notexture[cubecheck])
    except:
        pass