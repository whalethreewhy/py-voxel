import random
cimport cython
cimport numpy
import noisegen as gen

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict async_terraingen(int seed, int terraintype, int px, int py, numpy.ndarray[numpy.int32_t, ndim=2] adjacent, numpy.ndarray[numpy.int32_t, ndim=2] tree):
	cdef int q,w,blocktype
	cdef int currentheight,ho
	cdef dict world = dict()
	cdef int adjheight
	cdef numpy.ndarray currenttree
	cdef bint treeplaced = False
	random.seed(a=seed*px*py)
	if terraintype == 1:
		world[(px,py)] = dict()
		for q in range((px*8),(px*8)+8,1):
			for w in range((py*8),(py*8)+8,1):
				adjheight = 9999
				for re in adjacent+[q,w]:
					adjheight = min(adjheight,(max((int(gen.getHeight(seed,64000000+re[0], 64000000+re[1],600))),52)))
				currentheight = max((int(gen.getHeight(seed,64000000+q, 64000000+w,600))),52)
				for ho in range(0,currentheight+1):
					blocktype = 3
					if ho > 80:
						blocktype = 2
						if ho >90 and ho == currentheight:
							blocktype = 7
					else:
						if currentheight == 52 and ho > 30:#sea
							blocktype = 6
						else:
							if ho < 50 :#stone below 50
								blocktype = 2
							else:
								if ho == currentheight:# dirt/grass above 50
									blocktype = 0
								else:
									blocktype = 3
							if currentheight == 52 and ho == 30:#seabed
								blocktype = 3
					if blocktype == 0:
						if (not treeplaced) and (px*8) + 2 <= q <= ((px+1)*8)-1-2 and (py*8) + 2 <= w <= ((py+1)*8)-1-2:
							if random.randint(0,18) == 13:
								world[(px,py)] = {**{tuple(currenttree[:3]):tuple(currenttree[3:5]) for currenttree in tree+[q,ho,w,0,0]},**world[(px,py)]}
								treeplaced = True
					if ho != currentheight and adjheight >= ho:
						world[(px,py)][(q,ho,w)] = (blocktype,0)
					else:
						world[(px,py)][(q,ho,w)] = (blocktype,1)
	elif terraintype == 2:
		choices = (0,2,3)
		world[(px,py)] = dict()
		for q in range((px*8),(px*8)+8,1):
			for w in range((py*8),(py*8)+8,1):
				
				blocktype = random.choice(choices)
				"""if q == px*8 or q == ((px+1)*8)-1 or w == ((py+1)*8)-1 or w == (py)*8:
					blocktype = 5
				"""
				"""
				if (not treeplaced) and (px*8) + 2 <= q <= ((px+1)*8)-1-2 and (py*8) + 2 <= w <= ((py+1)*8)-1-2:
					if random.randint(0,13) == 13:
						world[(px,py)] = {**{tuple(t[:3]):tuple(t[3:5]) for t in tree+[q,0,w,0,0]},**world[(px,py)]}
						treeplaced = True
				"""
				world[(px,py)][(q,0,w)] = (blocktype,1)


	return world