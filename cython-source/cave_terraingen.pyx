import glm
cimport numpy
cimport cython
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict cave_terraingen(int seed,tuple v,numpy.ndarray[numpy.int32_t, ndim=2] adjacent,numpy.ndarray[numpy.int32_t, ndim=2] side_adjacent):
	cdef dict outChunk
	cdef int noiseScale
	cdef int px,py
	cdef int amp
	#PROBLEMATIC
	cdef int j
	cdef float cavenoise,newnoise
	cdef int adjheight
	cdef int water
	outChunk = dict()
	noiseScale = 95
	px,py = v 
	amp= 50
	for q in range((px*8),(px*8)+8,1):
		for w in range((py*8),(py*8)+8,1):
			outChunk[(q,0,w)] = (2,1)
			for b in range(1,40):
				cavenoise = glm.perlin(glm.vec3((q+seed)/20, (b+seed)/20, (w+seed)/20)) * 20
				if cavenoise < 5.5:
					counter = 0
					for re in adjacent + [q,b,w]:
						if b<39 and glm.perlin(glm.vec3((re[0]+seed)/20, (re[1]+seed)/20, (re[2]+seed)/20)) * 20 < 5.5:
							counter += 1
						else:break
					if counter == 6:
						outChunk[(q,b,w)] = (2,0)
					else:
						outChunk[(q,b,w)] = (2,1)
			
			newnoise = glm.perlin(glm.vec3((q+seed)/noiseScale, seed, (w+seed)/noiseScale)) * amp
			adjheight = 999
			for se in side_adjacent + [q,w]:
				adjheight = min(adjheight,amp+(glm.perlin(glm.vec3((se[0]+seed)/noiseScale, seed, (se[1]+seed)/noiseScale)) * amp))
			if amp+int(newnoise)<=25:
				for water in range(amp+int(newnoise),25+1):
					if water != 25:
						outChunk[(q,water+40,w)] = (6,0)
					else:
						outChunk[(q,water+40,w)] = (6,1)
			for j in range(0,amp+int(newnoise)+1):
				if j == amp+int(newnoise):
					if amp+int(newnoise)<25:
						blocktype = 3
					else:
						blocktype = 0
				else:
					if j > 20:
						blocktype = 3
					else:
						blocktype = 2
				if j == 0 and (q,j+39,w) not in outChunk:
					outChunk[(q,j+40,w)] = (blocktype,1)
				elif (j != amp+int(newnoise) and adjheight >= j):
					outChunk[(q,j+40,w)] = (blocktype,0)
				else:
					outChunk[(q,j+40,w)] = (blocktype,1)
	return outChunk