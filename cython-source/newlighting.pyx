import numpy as np
import time
from collections import deque
cimport cython
cimport numpy
from copy import copy,deepcopy
#vec3(0.0, 0.0, 1.0),vec3(1.0, 0.0, 0.0),vec3(0.0, 0.0, -1.0),vec3(-1.0, 0.0, 0.0),vec3(0.0,-1.0, 0.0),vec3(0.0, 1.0, 0.0)
#x,z,y

adjacent = np.array([
	[1,0,0],
	[-1,0,0],
	[0,1,0],
	[0,-1,0],
	[0,0,1],
	[0,0,-1]	
],dtype='int32')


zy_flip_adjacent = np.array([
	[3],
	[1],
	[2],
	[0],
	[4],
	[5]	
],dtype='int32')

dec_adjacent2 = np.concatenate((adjacent,zy_flip_adjacent),axis=1)

np_flood = np.ones((24*24*256,3),dtype='int32')*-127
#vis = np.zeros((24,24,256),dtype='int32')

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef int floodfill(int [:,:] flood,int [:,:] badjacent,int minX,int maxX,int minZ,int maxZ,int [:,:,:] nodeMap,int[:] nodeArray,int nodeSize,int [:,:,:,:] empty,int node0,int node1,int node2):
    cdef int point_light
    cdef int a_v

    cdef int po0,po1,po2
    cdef int v0,v1,v2
    cdef int attenuate
    cdef int QIndex = 0
    #cdef int [:,:,:] vN = np.zeros((24,24,256),dtype='int32')
    #vN[node0][node1][node2] = 1

    flood[QIndex][0] = node0 
    flood[QIndex][1] = node1
    flood[QIndex][2] = node2 
    
    nodeArray[nodeSize] = (24*24*node2)+(24*node1)+node0
    nodeSize += 1
    nodeMap[node0][node1][node2] = 1

    
    while QIndex >= 0:
        po0 = flood[QIndex][0]
        po1 = flood[QIndex][1]
        po2 = flood[QIndex][2]
 
        QIndex -= 1
        #Light Val of current node
        point_light = empty[po0][po1][po2][2]
        
        for a_v in range(6):
           

            v0 = badjacent[a_v][0] + po0
            v1 = badjacent[a_v][1] + po1
            v2 = badjacent[a_v][2] + po2

            if minX <= v0 < maxX and minZ <= v1 < maxZ and 0 <= v2 < 256:
                if empty[v0][v1][v2][0] == -1:
                    if empty[v0][v1][v2][2] < point_light:

                        
                        if nodeMap[v0][v1][v2] == 0:
                            nodeArray[nodeSize] = (24*24*v2)+(24*v1)+v0
                            nodeSize += 1
                            nodeMap[v0][v1][v2] = 1                            
                        

                        attenuate = point_light-(a_v != 5)
             
                        #attenuate = point_light-1
                        empty[v0][v1][v2][2] = attenuate
                        empty[v0][v1][v2][3] = attenuate
                        empty[v0][v1][v2][4] = attenuate
                        empty[v0][v1][v2][5] = attenuate
                        empty[v0][v1][v2][6] = attenuate
                        empty[v0][v1][v2][7] = attenuate

                
                        #if (not vN[v0][v1][v2]) and attenuate > 1:
                        if attenuate > 1:
                            QIndex += 1
                            flood[QIndex][0] = v0   
                            flood[QIndex][1] = v1
                            flood[QIndex][2] = v2
                            #vN[v0][v1][v2] = 1
       
    return nodeSize

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict lighting(list near_lightmaps,int chunkX,int chunkZ):
    cdef int [:,:] adjacent2 =  dec_adjacent2
    cdef numpy.ndarray[numpy.int32_t, ndim=2] emptyLight
    cdef numpy.ndarray[numpy.int32_t, ndim=4] np_empty = np.ones((24,24,256,8),dtype='int32')*-1
    cdef int q 
    cdef int w 
    cdef int n
    cdef int nplus
    cdef dict reconverts = dict()


    
    cdef int gb
    cdef numpy.ndarray[numpy.int32_t, ndim=2] nearchunk
    cdef list ori_map
    ori_map = deepcopy(near_lightmaps)
    cdef int minX = 256
    cdef int maxX = -1

    cdef int minZ = 256
    cdef int maxZ = -1


    for gb in range(len(near_lightmaps)):
        nearchunk = near_lightmaps[gb][0]
        minpointX = (near_lightmaps[gb][1][0]*8 + 8) - chunkX*8
        minpointZ = (near_lightmaps[gb][1][1]*8 + 8) - chunkZ*8

        minX = min(minpointX,minX)
        maxX = max(minpointX+7,maxX)

        minZ = min(minpointZ,minZ)
        maxZ = max(minpointZ+7,maxZ)
        nearchunk[:,0] = nearchunk[:,0] - chunkX*8 + 8 
        nearchunk[:,2] = nearchunk[:,2] - chunkZ*8 + 8 
        
        np_empty[nearchunk[:,0],nearchunk[:,2],nearchunk[:,1]]= nearchunk[:,3:11]
    
  

    cdef int [:,:,:,:] empty = np_empty
    cdef int [:,:] view_flood = np_flood
    cdef int [:,:] badjacent = adjacent

    cdef int [:] lightNodeArray = np.zeros((24*24*256),dtype='int32')
    cdef int [:,:,:] lightNodeMap = np.zeros((24,24,256),dtype='int32')
    cdef int lN_size = 0

    #rt = time.time()
    for q in range(8,16):
        for w in range(8,16):
            for n in range(255, -1,-1):
                if empty[q][w][n][0] != -1:

                    nplus = n+1
                    empty[q][w][nplus][2] = 7
                    empty[q][w][nplus][3] = 7
                    empty[q][w][nplus][4] = 7
                    empty[q][w][nplus][5] = 7
                    empty[q][w][nplus][6] = 7
                    empty[q][w][nplus][7] = 7
                    
                    
                    lN_size = floodfill(view_flood,badjacent,minX,maxX,minZ,maxZ,lightNodeMap,lightNodeArray,lN_size,empty,q,w,n+1)
                    break
    #print(time.time()-rt)

    cdef int c
    cdef int curNode
    cdef int c0,c1,c2
    cdef int b
    cdef int b0,b1,b2,b3
    
    for c in range(lN_size):
        curNode = lightNodeArray[c]
        c2 = curNode // 576
        c1 = (curNode // 24) % 24
        c0 = curNode % 24
        for b in range(6):
            b0 = adjacent2[b][0] + c0
            b1 = adjacent2[b][1] + c1
            b2 = adjacent2[b][2] + c2
            if 0 <= b0 < 24 and 0 <= b1 < 24 and 0 <= b2 < 256:
                if empty[b0][b1][b2][0] != -1:
                    b3 = adjacent2[b][3]+2 
                    empty[b0][b1][b2][b3] = max(empty[c0][c1][c2][2],empty[b0][b1][b2][b3])

    
    cdef tuple cur_chunk
    cdef numpy.ndarray[numpy.int32_t, ndim=2] near_reconvert
    cdef numpy.ndarray[numpy.int32_t, ndim=2] bloc
    for gb in range(len(near_lightmaps)):
        nearchunk = near_lightmaps[gb][0]
        cur_chunk = near_lightmaps[gb][1]
        near_reconvert = np.asarray(empty)[nearchunk[:,0],nearchunk[:,2],nearchunk[:,1]][:,2:8]
        bloc = np.concatenate((ori_map[gb][0][:,:5],near_reconvert),axis=1)
        
        reconverts[cur_chunk] = bloc

    return reconverts
    
#vec3(0.0, 0.0, 1.0),vec3(1.0, 0.0, 0.0),vec3(0.0, 0.0, -1.0),vec3(-1.0, 0.0, 0.0),vec3(0.0,-1.0, 0.0),vec3(0.0, 1.0, 0.0)

