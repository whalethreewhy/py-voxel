import numpy as np
cimport numpy
cimport cython
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef bint collisionpadding(numpy.ndarray[numpy.int_t, ndim=2] checknear,float inx,float iny,float inz):
    
    cdef numpy.ndarray[numpy.float64_t,ndim=2] playerbox
    cdef int lookingblock
    
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,0] < inx-2,checknear[:,0] > inx+2))]
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,1] < iny-2,checknear[:,1] > iny+2))]
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,2] < inz-2,checknear[:,2] > inz+2))]
    cdef int [:,:] converted = checknear
    cdef int arr_shape = checknear.shape[0]
    playerbox = np.array([
        [inx-0.3,inx+0.3],
        [iny-1.5,iny+0.5],
        [inz-0.3,inz+0.3],
    ])
    cdef double [:,:] convertedplayerbox = playerbox
    for lookingblock in range(arr_shape):
        tempx,tempy,tempz = converted[lookingblock]
        if convertedplayerbox[0][0] < tempx+0.4 and convertedplayerbox[0][1] > tempx-0.4:
            if convertedplayerbox[1][0] < tempy+0.4 and convertedplayerbox[1][1] > tempy-0.4:
                if convertedplayerbox[2][0] < tempz+0.4 and convertedplayerbox[2][1] > tempz-0.4:
                    return True
    return False


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef tuple fallcollision(numpy.ndarray[numpy.int_t, ndim=2] checknear,float inx,float iny,float inz):
    
    cdef numpy.ndarray[numpy.float64_t,ndim=2] playerbox
    cdef int lookingblock
    
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,0] < inx-2,checknear[:,0] > inx+2))]
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,1] < iny-2,checknear[:,1] > iny+2))]
    checknear = checknear[np.logical_not(np.logical_or(checknear[:,2] < inz-2,checknear[:,2] > inz+2))]
    cdef int [:,:] converted = checknear
    cdef int arr_shape = checknear.shape[0]
    playerbox = np.array([
        [inx-0.3,inx+0.3],
        [iny-1.5,iny+0.5],
        [inz-0.3,inz+0.3],
    ])
    cdef double [:,:] convertedplayerbox = playerbox
    for lookingblock in range(arr_shape):
        tempx,tempy,tempz = converted[lookingblock]
        if convertedplayerbox[0][0] < tempx+0.4 and convertedplayerbox[0][1] > tempx-0.4:
            if convertedplayerbox[1][0] < tempy+0.4 and convertedplayerbox[1][1] > tempy-0.4:
                if convertedplayerbox[2][0] < tempz+0.4 and convertedplayerbox[2][1] > tempz-0.4:
                    return (True,tempx,tempy,tempz)
    return (False,0,0,0)

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef tuple gravity(bint noCollide,float sincetime,numpy.ndarray[numpy.int_t, ndim=2] notexarray,float inx,float iny,float inz):
    cdef float fall = (-1/4*(0.003)*(sincetime**2))/40
    cdef int n
    for n in range(40):
        if fall < -0.7/40:
            fall = -0.7/40
        iny += fall
        if noCollide or collisionpadding(notexarray,inx,iny,inz):
            iny -= fall
            sincetime = 0
            break
        else:
            sincetime += 0.01
    return (iny,sincetime)