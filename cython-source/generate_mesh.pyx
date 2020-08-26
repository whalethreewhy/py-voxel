cimport numpy
cimport cython
import numpy as np
avecs = np.array((
	(0, 0, 1),
	(1, 0, 0),
	(0, 0, -1),
	(-1, 0, 0),
	(0,-1, 0),
	(0, 1, 0)),dtype='int32')
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef numpy.uint8_t [:,:,:,:] generate_mesh(dict world,numpy.ndarray[numpy.int32_t, ndim=2] taddlist,int Xnormchunk,int Znormchunk):
	cdef numpy.ndarray[numpy.int32_t, ndim=2] vecs = avecs
	cdef numpy.ndarray[numpy.int32_t, ndim=1] k
	cdef int kn
	#cdef numpy.ndarray[numpy.int32_t, ndim=1] adj_block
	cdef tuple which_chunk = (int(Xnormchunk/8),int(Znormchunk/8))
	cdef tuple tupAdjacentBlock
	cdef numpy.ndarray np_empty = np.zeros((8,8,256,7),dtype='bool')
	np_empty[taddlist[:,0],taddlist[:,2],taddlist[:,1]] = True
	cdef numpy.uint8_t [:,:,:,:] empty = np_empty

	for k in taddlist:
		for kn in range(6):
			adj_block = k + vecs[kn]
			tupAdjacentBlock = (adj_block[0]+Xnormchunk,adj_block[1],adj_block[2]+Znormchunk)
			try:
				if tupAdjacentBlock in world[which_chunk]:
					empty[k[0]][k[2]][k[1]][kn+1] = False
			except:pass
	
	return empty