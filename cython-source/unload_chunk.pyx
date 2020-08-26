cimport numpy
cimport cython
from collections import deque
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef unsigned int get_key(int val,dict my_dict): 
	cdef unsigned int key
	cdef int value
	for key,value in my_dict.items():
		if val == value:
			return key

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef tuple unload_chunk(tuple o,dict world,list activearray,dict activearray_indices,dict chunkbuffer,list used_buffers,available_buffers,set VAOs,dict used_VAOs):
	cdef int old_index
	cdef tuple fq
	cdef unsigned int switchvao
	cdef int n
	del world[o]
	if len(activearray) > 0:
		del activearray[activearray_indices[o]]
	old_index = activearray_indices[o]
	del activearray_indices[o]

	for fq in activearray_indices:
		if activearray_indices[fq] > old_index:
			activearray_indices[fq] = activearray_indices[fq]-1

	re = chunkbuffer[o][:4]
	for n in range(len(used_buffers)):
		if used_buffers[n] != 0:
			if [used_buffers[n][0],used_buffers[n][1],used_buffers[n][2],used_buffers[n][3]] == re:
				used_buffers[n] = 0
				available_buffers.append(re+[0])
				del chunkbuffer[o]
				switchvao = get_key(n,used_VAOs)
				VAOs.add(switchvao)
				del used_VAOs[switchvao]
	
	return (world,activearray,activearray_indices,chunkbuffer,used_buffers,available_buffers,VAOs,used_VAOs)