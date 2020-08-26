import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
if __name__ == 'test' or __name__ == "__main__":
	import pygame
	from pygame.locals import *
	import OpenGL.GL.shaders
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from itertools import zip_longest
	import math
	import glm
	import copy
	import noisegen
	from lookingat import lookingat
	from collisionpadding import collisionpadding
	from collisionpadding import fallcollision
	from generate_mesh import generate_mesh
	from unload_chunk import unload_chunk,get_key
	from dict_to_numpy import dict_to_numpy
	import random
	import newlighting


import numpy
import time
import sys

from async_terraingen import async_terraingen
from cave_terraingen import cave_terraingen

from multiprocessing import Manager,Pool,freeze_support,cpu_count
import bz2
import _pickle as cPickle
import threading
from collections import deque

#import traceback


import PIL.Image as pil


Running = True

class Player():
	def __init__(self):
		self.inventory=numpy.ones((4,9),dtype='int16')*-1
		self.inventory[3]=numpy.array([0,1,2,3,4,5,7,8,9],dtype='int16')
		self.hotbarselect = 0
		self.hotbarupdate = True
		self.inv_visible=False
		self.x=0
		self.y=0
		self.z=0
		self.pitch=0
		self.yaw=0
		self.blockselection=self.inventory[3][self.hotbarselect]
		self.flytoggle=False
		self.jumping=False
		self.timesince=0
		self.timesincejump=-1
	
	def update_selection(self,newselect):
		if self.hotbarselect != newselect-1:
			self.hotbarupdate = True
			self.hotbarselect = newselect-1
			self.blockselection=self.inventory[3][self.hotbarselect]


"""User Defined Variables"""
if True:
	properties = open("world_saves\\properties.txt","r")
	properties = properties.readlines()
	slot = str(properties[1]).split('\n')[0]
	width = int(properties[3])
	height = int(properties[5])
	fullscreen = int(properties[7])
	highres = int(properties[9])
	if highres == 1: highres = True
	elif highres == 0: highres = False

	worldattr = open("world_saves\\"+slot+"\\world_attributes.txt","r")
	worldattr = worldattr.readlines()
	worldtype = int(worldattr[0])
	seed = int(worldattr[1])
	renderdist = 5
	fog = False
	start_fov = 70
	fov = 70
	vsync = 70	
	farclip = 320
	
"""Starting Variables"""
if __name__ == 'test' or __name__ == "__main__":
	loadQueue = deque()
	loadOut = deque()
	maxblocks = int(16384/2)
	highestworldbuffer = ((((renderdist*2)-1)**2)*4)+3
	sunx = 0
	reversepath = -1
	points = numpy.array((
		(-0.5, -0.5, 0.5),
		(0.5, -0.5, 0.5),
		(-0.5, 0.5, 0.5),
		(0.5, 0.5, 0.5),
		(-0.5, -0.5, -0.5),
		(0.5, -0.5, -0.5),
		(-0.5, 0.5, -0.5),
		(0.5, 0.5, -0.5)
		),dtype='float32')

	surfaces = numpy.array([
		[0,1,3], #front
		[0,3,2],
		[1,5,7], #right
		[1,7,3],
		[5,4,6], #back
		[5,6,7],
		[4,0,2], #left
		[4,2,6],
		[4,5,1], #bottom
		[4,1,0],
		[2,3,7], #top
		[2,7,6]
		],dtype='int32')
		
	quadsurfaces = numpy.array([
		0,1,3,2,
		1,5,7,3,
		5,4,6,7,
		4,0,2,6,
		4,5,1,0,
		2,3,7,6
	])
	
	boundingpoints = numpy.array((
		(-0.505, -0.505, 0.505),
		(0.505, -0.505, 0.505),
		(-0.505, 0.505, 0.505),
		(0.505, 0.505, 0.505),
		(-0.505, -0.505, -0.505),
		(0.505, -0.505, -0.505),
		(-0.505, 0.505, -0.505),
		(0.505, 0.505, -0.505)
	))

	#sides,bottom,top
	texcoordslist = [
		#Grass
		[[0.0,0.25,0.0,0.0,0.25,0.0,0.0,0.25,0.25,0.0,0.25,0.25],
		[0.0,0.5,0.0,0.25,0.25,0.25,0.0,0.5,0.25,0.25,0.25,0.5],
		[0.25,0.25,0.25,0.0,0.5,0.0,0.25,0.25,0.5,0.0,0.5,0.25]],
		
		#Cobblestone
		[[0.25,0.5,0.25,0.25,0.5,0.25,0.25,0.5,0.5,0.25,0.5,0.5]],
		
		#Stone
		[[0.0,0.75, 0.0,0.5, 0.25,0.5, 0.0,0.75, 0.25,0.5, 0.25,0.75]],

		#Dirt
		[[0.0,0.5,0.0,0.25,0.25,0.25,0.0,0.5,0.25,0.25,0.25,0.5]],

		#Wooden Planks
		[[0.25,0.75, 0.25,0.5, 0.5,0.5, 0.25,0.75, 0.5,0.5, 0.5,0.75]],

		#Diamond Block
		[[0.5,0.75, 0.5,0.5, 0.75,0.5, 0.5,0.75, 0.75,0.5, 0.75,0.75]],

		#Water
		[[0.75,0.75, 0.75,0.5, 1.0,0.5, 0.75,0.75, 1.0,0.5, 1.0,0.75]],
		
		#Snow
		[[0.0,1.0, 0.0,0.75, 0.25,0.75, 0.0,1.0, 0.25,0.75, 0.25,1.0]],

		#Oak Log
		[[0.5,0.5, 0.5,0.25, 0.75,0.25, 0.5,0.5, 0.75,0.25, 0.75,0.5],
		[0.75,0.5, 0.75,0.25, 1.0,0.25, 0.75,0.5, 1.0,0.25, 1.0,0.5],
		[0.75,0.5, 0.75,0.25, 1.0,0.25, 0.75,0.5, 1.0,0.25, 1.0,0.5]],

		#Leaves
		[0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25],
	]

	fulltexcoords = numpy.array([
		#grass
		[0.0, 0.25, 0.0, 0.0, 0.25, 0.0, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.25, 0.0, 0.0, 0.25, 0.0, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.25, 0.0, 0.0, 0.25, 0.0, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.25, 0.0, 0.0, 0.25, 0.0, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.25, 0.25, 0.25, 0.0, 0.5, 0.0, 0.25, 0.25, 0.5, 0.0, 0.5, 0.25],
		#cobblestone
		[0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.5, 0.5],
		#stone
		[0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75, 0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75, 0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75, 0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75, 0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75, 0.0, 0.75, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.25, 0.5, 0.25, 0.75],
		#dirt
		[0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5, 0.0, 0.5, 0.0, 0.25, 0.25, 0.25, 0.0, 0.5, 0.25, 0.25, 0.25, 0.5],
		#wood
		[0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75, 0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75, 0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75, 0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75, 0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75, 0.25, 0.75, 0.25, 0.5, 0.5, 0.5, 0.25, 0.75, 0.5, 0.5, 0.5, 0.75],
		#diamond block
		[0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.75, 0.5, 0.75, 0.75],
		#glass
		[0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75, 0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75, 0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75, 0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75, 0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75, 0.75, 0.75, 0.75, 0.5, 1.0, 0.5, 0.75, 0.75, 1.0, 0.5, 1.0, 0.75],
		#Snow
		[0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0, 0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0, 0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0, 0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0, 0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0, 0.0, 1.0, 0.0, 0.75, 0.25, 0.75, 0.0, 1.0, 0.25, 0.75, 0.25, 1.0],
		#Oak Log
		[0.5,0.5, 0.5,0.25, 0.75,0.25, 0.5,0.5, 0.75,0.25, 0.75,0.5,0.5,0.5, 0.5,0.25, 0.75,0.25, 0.5,0.5, 0.75,0.25, 0.75,0.5,0.5,0.5, 0.5,0.25, 0.75,0.25, 0.5,0.5, 0.75,0.25, 0.75,0.5,0.5,0.5, 0.5,0.25, 0.75,0.25, 0.5,0.5, 0.75,0.25, 0.75,0.5,0.75,0.5, 0.75,0.25, 1.0,0.25, 0.75,0.5, 1.0,0.25, 1.0,0.5,0.75,0.5, 0.75,0.25, 1.0,0.25, 0.75,0.5, 1.0,0.25, 1.0,0.5],
		#Leaves
		[0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25,0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25,0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25,0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25,0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25,0.75,0.25, 0.75,0.0, 1.0,0.0, 0.75,0.25, 1.0,0.0, 1.0,0.25]
	],dtype='float32')

	buttontexcoords = [

		#[0.0,1.0,1.0,1.0,1.0,0.0,0.0,0.0],
		
		#[0.0,0.75,1.0,0.75,1.0,0.5,0.0,0.5],
		#[0.0,0.5,1.0,0.5,1.0,0.25,0.0,0.25],
		#save
		[0.0,0.875,1.0,0.875,1.0,0.75,0.0,0.75],
		[0.0,0.75,1.0,0.75,1.0,0.625,0.0,0.625],#on hover
		#quit
		[0.0,0.5,1.0,0.5,1.0,0.375,0.0,0.375],
		[0.0,0.375,1.0,0.375,1.0,0.25,0.0,0.25],#on hover 
	]

	hotbartexcoords = numpy.array([
		[0.0,0.9140625, 0.7109375,0.9140625, 0.7109375,1.0, 0.0,1.0],
		[0.0,0.8203125, 0.09375,0.8203125, 0.09375,0.9140625, 0.0,0.9140625]
	],dtype='float32')

	adjacent_chunks = numpy.array([
		[0,0],
		[1,0],
		[-1,0],
		[0,1],
		[0,-1],
		[1,1],
		[1,-1],
		[-1,1],
		[-1,-1]
	])

	noclip = False
	if noclip:
		def collisionpadding(uu,ii,oo,pp):
			return False

		def fallcollision(uu,ii,oo,pp):
			return (False,0,0,0)
	
	random.seed(a=seed)
	projection = glm.perspective(numpy.deg2rad(fov),width/height,0.1,farclip)
	projection = numpy.array(projection)
	is_looking = False
	vertindices_select = numpy.reshape(numpy.array([range(0,360)],dtype='uint32'),(10,36))

#vec3(0.0, 0.0, 1.0),vec3(1.0, 0.0, 0.0),vec3(0.0, 0.0, -1.0),vec3(-1.0, 0.0, 0.0),vec3(0.0,-1.0, 0.0),vec3(0.0, 1.0, 0.0)
"""Shared Variables"""
if True:
	adjacent = numpy.array([
		[1,0,0],
		[-1,0,0],
		[0,1,0],
		[0,-1,0],
		[0,0,1],
		[0,0,-1]	
	])
	"""
	tree = numpy.array([
		[0, 1, 0, 8, 1], [0, 2, 0, 8, 1], [0, 3, 0, 8, 1], [0, 4, 0, 8, 1], [0, 4, 1, 9, 1], [0, 3, 1, 9, 1], [1, 3, 1, 9, 1], [1, 4, 1, 9, 1], [-1, 3, 1, 9, 1], [-1, 4, 1, 9, 1], [2, 3, 1, 9, 1], [2, 4, 1, 9, 1], [-2, 3, 1, 9, 1], 
		[-2, 4, 1, 9, 1], [1, 3, 2, 9, 1], [0, 3, 2, 9, 1], [-1, 3, 2, 9, 1], [-2, 3, 2, 9, 1], [1, 4, 2, 9, 1], [0, 4, 2, 9, 1], [-1, 4, 2, 9, 1], [-2, 4, 2, 9, 1], [2, 3, 2, 9, 1], [2, 4, 2, 9, 1], [1, 3, 0, 9, 1], 
		[2, 3, 0, 9, 1], [1, 4, 0, 9, 1], [2, 4, 0, 9, 1], [0, 3, -1, 9, 1], [0, 4, -1, 9, 1], [1, 3, -1, 9, 1], [2, 3, -1, 9, 1], [2, 4, -1, 9, 1], [1, 4, -1, 9, 1], [-1, 3, 0, 9, 1], [-1, 3, -1, 9, 1], [-1, 4, 0, 9, 1], [-1, 4, -1, 9, 1], [-2, 3, 0, 9, 1], [-2, 3, -1, 9, 1], [-2, 4, 0, 9, 1], [-2, 4, -1, 9, 1], [-1, 5, 1, 9, 1], [-1, 5, 0, 9, 1], [-1, 5, -1, 9, 1], [0, 5, -1, 9, 1], [1, 5, -1, 9, 1], [0, 5, 1, 9, 1], [1, 5, 1, 9, 1], [1, 5, 0, 9, 1], [0, 5, 0, 8, 1], [1, 6, 0, 9, 1], [0, 6, 0, 9, 1], [-1, 6, 0, 9, 1], [0, 6, 1, 9, 1], [0, 6, -1, 9, 1], [2, 4, -2, 9, 1], [2, 3, -2, 9, 1], [1, 3, -2, 9, 1], [1, 4, -2, 9, 1], [0, 3, -2, 9, 1], [0, 4, -2, 9, 1], [-1, 3, -2, 9, 1], [-1, 4, -2, 9, 1], [-2, 3, -2, 9, 1], [-2, 4, -2, 9, 1]
	],dtype='int32')
	"""
	
	tree = numpy.array([
		[0, 1, 0, 8, 1], [0, 2, 0, 8, 1], [0, 3, 0, 8, 0], [0, 4, 0, 8, 0], [0, 4, 1, 9, 0], [0, 3, 1, 9, 1], [1, 3, 1, 9, 1], [1, 4, 1, 9, 0], [-1, 3, 1, 9, 1], [-1, 4, 1, 9, 0], [2, 3, 1, 9, 1], [2, 4, 1, 9, 1], [-2, 3, 1, 9, 1], [-2, 4, 1, 9, 1], [1, 3, 2, 9, 1], [0, 3, 2, 9, 1], [-1, 3, 2, 9, 1], [-2, 3, 2, 9, 1], [1, 4, 2, 9, 1], [0, 4, 2, 9, 1], [-1, 4, 2, 9, 1], [-2, 4, 2, 9, 1], [2, 3, 2, 9, 1], [2, 4, 2, 9, 1], [1, 3, 0, 9, 1], [2, 3, 0, 9, 1], [1, 4, 0, 9, 0], [2, 4, 0, 9, 1], [0, 3, -1, 9, 1], [0, 4, -1, 9, 0], [1, 3, -1, 9, 1], [2, 3, -1, 9, 1], [2, 4, -1, 9, 1], [1, 4, -1, 9, 0], [-1, 3, 0, 9, 1], [-1, 3, -1, 9, 1], [-1, 4, 0, 9, 0], [-1, 4, -1, 9, 0], 
		[-2, 3, 0, 9, 1], [-2, 3, -1, 9, 1], [-2, 4, 0, 9, 1], [-2, 4, -1, 9, 1], [-1, 5, 1, 9, 1], [-1, 5, 0, 9, 1], [-1, 5, -1, 9, 1], [0, 5, -1, 9, 1], [1, 5, -1, 9, 1], [0, 5, 1, 9, 1], [1, 5, 1, 9, 1], [1, 5, 0, 9, 1], [0, 5, 0, 8, 0], [1, 6, 0, 9, 1], [0, 6, 0, 9, 1], [-1, 6, 0, 9, 1], [0, 6, 1, 9, 1], [0, 6, -1, 9, 1], [2, 4, -2, 9, 1], [2, 3, -2, 9, 1], [1, 3, -2, 9, 1], [1, 4, -2, 9, 1], [0, 3, -2, 9, 1], [0, 4, -2, 9, 1], [-1, 3, -2, 9, 1], [-1, 4, -2, 9, 1], [-2, 3, -2, 9, 1], [-2, 4, -2, 9, 1]
	],dtype='int32')
	adja = numpy.array([
		[0,0],
		[1,0],
		[-1,0],
		[0,1],
		[0,-1],
		[1,1],
		[1,-1],
		[-1,1],
		[-1,-1]
	],dtype='int32')
	non_diag = numpy.array([
		[1,0],
		[-1,0],
		[0,1],
		[0,-1],	
	])

"""Shader Code"""
if __name__ == 'test' or __name__ == "__main__":
	VERTEX_SHADER = """
		#version 330 core
		layout (location = 0) in vec3 position;
		layout (location = 1) in uint sidepointer;
		layout (location = 2) in float color;
		
		uniform vec2 texarray[360] = vec2[360](    
			//grass
			vec2(0.0,0.25),vec2(0.0,0.0),vec2(0.25,0.0),vec2(0.0,0.25),vec2(0.25,0.0),vec2(0.25,0.25),vec2(0.0,0.25),vec2(0.0,0.0),vec2(0.25,0.0),vec2(0.0,0.25),vec2(0.25,0.0),vec2(0.25,0.25),vec2(0.0,0.25),vec2(0.0,0.0),vec2(0.25,0.0),vec2(0.0,0.25),vec2(0.25,0.0),vec2(0.25,0.25),vec2(0.0,0.25),vec2(0.0,0.0),vec2(0.25,0.0),vec2(0.0,0.25),vec2(0.25,0.0),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.25,0.0),vec2(0.5,0.0),vec2(0.25,0.25),vec2(0.5,0.0),vec2(0.5,0.25),
			//cobblestone
			vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),vec2(0.25,0.5),vec2(0.25,0.25),vec2(0.5,0.25),vec2(0.25,0.5),vec2(0.5,0.25),vec2(0.5,0.5),
			//stone
			vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),vec2(0.0,0.75),vec2(0.0,0.5),vec2(0.25,0.5),vec2(0.0,0.75),vec2(0.25,0.5),vec2(0.25,0.75),
			//dirt
			vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),vec2(0.0,0.5),vec2(0.0,0.25),vec2(0.25,0.25),vec2(0.0,0.5),vec2(0.25,0.25),vec2(0.25,0.5),
			//wood
			vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),vec2(0.25,0.75),vec2(0.25,0.5),vec2(0.5,0.5),vec2(0.25,0.75),vec2(0.5,0.5),vec2(0.5,0.75),
			//diamond block
			vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),vec2(0.5,0.75),vec2(0.5,0.5),vec2(0.75,0.5),vec2(0.5,0.75),vec2(0.75,0.5),vec2(0.75,0.75),
			//glass
			vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),vec2(0.75,0.75),vec2(0.75,0.5),vec2(1.0,0.5),vec2(0.75,0.75),vec2(1.0,0.5),vec2(1.0,0.75),
			//Snow
			vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),vec2(0.0,1.0),vec2(0.0,0.75),vec2(0.25,0.75),vec2(0.0,1.0),vec2(0.25,0.75),vec2(0.25,1.0),
			//Oak Log
			vec2(0.5,0.5), vec2(0.5,0.25), vec2(0.75,0.25), vec2(0.5,0.5), vec2(0.75,0.25), vec2(0.75,0.5),vec2(0.5,0.5), vec2(0.5,0.25), vec2(0.75,0.25), vec2(0.5,0.5), vec2(0.75,0.25), vec2(0.75,0.5),vec2(0.5,0.5), vec2(0.5,0.25), vec2(0.75,0.25), vec2(0.5,0.5), vec2(0.75,0.25), vec2(0.75,0.5),vec2(0.5,0.5), vec2(0.5,0.25), vec2(0.75,0.25), vec2(0.5,0.5), vec2(0.75,0.25), vec2(0.75,0.5),vec2(0.75,0.5), vec2(0.75,0.25), vec2(1.0,0.25), vec2(0.75,0.5), vec2(1.0,0.25), vec2(1.0,0.5),vec2(0.75,0.5), vec2(0.75,0.25), vec2(1.0,0.25), vec2(0.75,0.5), vec2(1.0,0.25), vec2(1.0,0.5),
			//Leaves
			vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25),vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25),vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25),vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25),vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25),vec2(0.75,0.25), vec2(0.75,0.0), vec2(1.0,0.0), vec2(0.75,0.25), vec2(1.0,0.0), vec2(1.0,0.25)
		);
		
		uniform vec3 normarray[6] = vec3[6](
			vec3(0.0, 0.0, 1.0),vec3(1.0, 0.0, 0.0),vec3(0.0, 0.0, -1.0),vec3(-1.0, 0.0, 0.0),vec3(0.0,-1.0, 0.0),vec3(0.0, 1.0, 0.0)
		);
		uniform float contrast;
		uniform mat4 projection;
		uniform mat4 view;
		uniform mat4 model;
		uniform vec3 pos;
		
		
		vec2 textureCoords = texarray[sidepointer];

		float fsidepointer = float(int(sidepointer)/36);
		int trinormpointer = int(sidepointer)-int(floor(36*floor(fsidepointer)));
		int normpointer = int(floor(float(trinormpointer)/6));
		vec3 vertNormal = normarray[normpointer];

		float dist;
		uniform float density = 0.02;
		uniform float gradient = 2;

		out float vertColor;
		out vec2 newTexture;
		out vec3 fragPosition;
		out float visibility;

		out float isBottom;
		out vec3 ambientLightIntensity;
		out vec3 sunLightIntensity;

		void main()
		{   
			if (normpointer == 4){
				isBottom = 0f;
			}
			else if (int(sidepointer) >= 216 && int(sidepointer) < 252 ){
				isBottom = 0f;
			}
			else{
				isBottom = 1.0f;
			}


			fragPosition = (model*vec4(vertNormal, 0.0f)).xyz;
			gl_Position = projection * view * model * vec4(position, 1.0f);

			dist = distance(pos,position);
			visibility = exp(-pow((dist*density),gradient));
			visibility = clamp(visibility,0.0,1.0);
			//visibility = 1.0f;

			
			ambientLightIntensity = max(max(contrast,0.7f)*vec3(0.7f, 0.7f, 0.7f),0.2f);
			sunLightIntensity = 1f-ambientLightIntensity.r*vec3(1f, 1f, 1f);
			newTexture = textureCoords;
			vertColor = color;
		}
	"""
	FRAGMENT_SHADER = """
		#version 330 core

		in float vertColor;
		in vec2 newTexture;
		in vec3 fragPosition;
		in float visibility;
		in vec3 ambientLightIntensity;
		in vec3 sunLightIntensity;
		in float isBottom;

		uniform float lightMult;
		uniform vec3 sun;
		uniform vec4 fogColor;

		uniform sampler2D samplerTexture;
		out vec4 outColor;
		void main()
		{   
			
			
			vec3 sunLightDirection = vec3(normalize(sun - fragPosition));
			vec4 texel = texture(samplerTexture, newTexture);

			
			vec3 lightIntensity =  ambientLightIntensity + isBottom*sunLightIntensity * max(dot(fragPosition, sunLightDirection), 0.0f);
			
			outColor = vec4((texel.rgb * max(vertColor*lightIntensity*lightMult,0.2f)), texel.a);
			outColor = mix(fogColor,outColor,visibility);
		}
	"""
	LINE_VERTEX_SHADER = """
		#version 330 core
		uniform mat4 projection;
		uniform mat4 view;
		uniform mat4 model;
		in vec3 position;
		uniform vec4 inColor;
		out vec4 newColor;
		void main() {
			gl_Position = projection * view * model * vec4(position, 1.0f);
			newColor = inColor;
		}
	"""
	LINE_FRAGMENT_SHADER = """
		#version 330 core
		in vec4 newColor;
		out vec4 outColor;
		void main() {
			outColor = newColor;
		}
	"""
	UI_VERTEX_SHADER = """
		#version 330 core

		uniform mat4 m1;
		uniform mat4 m2;
		uniform mat4 m3;
		uniform mat4 m4;
		uniform mat4 m5;
		uniform mat4 m6;
		uniform mat4 m7;
		uniform mat4 m8;
		uniform mat4 m9;


		layout (location = 0) in vec4 vertexdata;
		layout (location = 1) in vec2 inTexCoords;
		layout (location = 2) in int modelIndex;

		
		uniform mat4 orth;

		vec3 position = vertexdata.xyz;
		float inSidecolor = vertexdata.w;
		out vec2 textureCoords;
		out float outSidecolor;
		void main() {
			gl_Position = orth*mat4[9](m1,m2,m3,m4,m5,m6,m7,m8,m9)[modelIndex]*vec4(position,1.0f);
			textureCoords = inTexCoords;
			outSidecolor = inSidecolor;
		}
	"""
	UI_FRAGMENT_SHADER = """
		#version 330 core
		in vec2 textureCoords;
		in float outSidecolor;
		uniform sampler2D samplerTexture;
		out vec4 outColor;

		void main() {
			vec4 texel = texture(samplerTexture, textureCoords);
			outColor = vec4(texel.rgb*outSidecolor,texel.a);
		}
	"""
	if not fog:
		VERTEX_SHADER = VERTEX_SHADER.replace("//visibility = 1.0f;", "visibility = 1.0f;")

				
def newlight(starting=False):
	global lightmaps,lightQ
	"""
	for _ in range(len(lightQ)):
		for n in lightQ:break
		if n in activearray_indices:
			near_lightmaps = [(numpy.concatenate((activearray[activearray_indices[n]],numpy.zeros((len(activearray[activearray_indices[n]]),6),dtype='int32')),axis=1),n)]
			updateLight = newlighting.lighting(copy.deepcopy(near_lightmaps),copy.deepcopy(n[0]),copy.deepcopy(n[1]))[n]
			lightmaps[n] = updateLight
			selectedbuffers = chunkbuffer[n]
			lightBufferData = lightmaps[n][:,5:11].flatten()[masks[n]]
			lightBufferData = numpy.repeat(lightBufferData/7,6).astype('float32')
			glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[2])
			glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
			glBufferSubData(GL_ARRAY_BUFFER,0, (len(lightBufferData))*4, lightBufferData)
		lightQ.remove(n)
		if not starting:break
	"""
	if not is_Loading:
		uploadLights = set()
		
		for _ in range(len(lightQ)):
			for n in lightQ:break
			if n in activearray_indices:
				lightmaps[n] = numpy.concatenate((activearray[activearray_indices[n]],numpy.zeros((len(activearray[activearray_indices[n]]),6),dtype='int32')),axis=1)

				ajs = adja+n
				near_lightmaps = [(lightmaps[k],k) for k in map(tuple,ajs) if k in lightmaps]

				
				updateLight = newlighting.lighting(copy.deepcopy(near_lightmaps),copy.deepcopy(n[0]),copy.deepcopy(n[1]))

				lightmaps = {**lightmaps,**updateLight}	
				
				for f in updateLight:
					
					if f != n:
						ajs = adja+f
						near_lightmaps = [(lightmaps[f],f),(lightmaps[n],n)]
						updateLight2 = newlighting.lighting(copy.deepcopy(near_lightmaps),copy.deepcopy(f[0]),copy.deepcopy(f[1]))
						lightmaps = {**lightmaps,**updateLight2}
					uploadLights.add(f)
			lightQ.remove(n)
			if not starting:break
		
		for f in uploadLights:
			selectedbuffers = chunkbuffer[f]
			lightBufferData = lightmaps[f][:,5:11].flatten()[masks[f]]
			lightBufferData = numpy.repeat(lightBufferData/7,6).astype('float32')
			glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[2])
			glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
			glBufferSubData(GL_ARRAY_BUFFER,0, (len(lightBufferData))*4, lightBufferData)
		glBindBuffer(GL_ARRAY_BUFFER, 0)			
	
def ree(fg):
	global lightmaps
	del lightmaps[fg]
	return fg

def light_update(kn):
	global lightmaps
	uploadLights = set()

	Sajs = adja+kn
	resetlight = {ree(k) for k in map(tuple,Sajs) if k in activearray_indices}


	for _ in range(len(resetlight)):
		for n in resetlight:break
		if n in activearray_indices:
			lightmaps[n] = numpy.concatenate((activearray[activearray_indices[n]],numpy.zeros((len(activearray[activearray_indices[n]]),6),dtype='int32')),axis=1)

			ajs = adja+n
			near_lightmaps = [(lightmaps[k],k) for k in map(tuple,ajs) if k in lightmaps]

			
			updateLight = newlighting.lighting(copy.deepcopy(near_lightmaps),copy.deepcopy(n[0]),copy.deepcopy(n[1]))

			lightmaps = {**lightmaps,**updateLight}	
			
			for f in updateLight:
				
				if f != n:
					ajs = adja+f
					near_lightmaps = [(lightmaps[f],f),(lightmaps[n],n)]
					updateLight2 = newlighting.lighting(copy.deepcopy(near_lightmaps),copy.deepcopy(f[0]),copy.deepcopy(f[1]))
					lightmaps = {**lightmaps,**updateLight2}
				uploadLights.add(f)
		resetlight.remove(n)

	for f in uploadLights:
		selectedbuffers = chunkbuffer[f]
		lightBufferData = lightmaps[f][:,5:11].flatten()[masks[f]]
		lightBufferData = numpy.repeat(lightBufferData/7,6).astype('float32')
		glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[2])
		glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
		glBufferSubData(GL_ARRAY_BUFFER,0, (len(lightBufferData))*4, lightBufferData)
	glBindBuffer(GL_ARRAY_BUFFER, 0)	

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def newverts(temppoints,tempsurfaces,addlist):
	lencubeslist = len(addlist)
	normchunk = (addlist[0][0]//8,addlist[0][2]//8)
	taddlist = addlist.copy()
	taddlist[:,0] = addlist[:,0] - normchunk[0]*8
	taddlist[:,2] = addlist[:,2] - normchunk[1]*8

	boolMask = numpy.asarray(generate_mesh(world,taddlist,normchunk[0]*8,normchunk[1]*8),dtype='bool')

	hiddensides = boolMask[taddlist[:,0],taddlist[:,2],taddlist[:,1]]
	hiddensides = hiddensides[:,1:7]

	
	addlist = addlist.astype('float32')
	addlist = numpy.repeat(addlist,8,axis = 0)
	addlist = numpy.reshape(addlist,(lencubeslist,8,3))
	tempverticies = addlist+temppoints

	tempsurfaces = numpy.array([tempsurfaces])[numpy.zeros((lencubeslist,),dtype='uint')]
	
	surfaceoffset = numpy.arange(0,lencubeslist*8,8)
	
	surfaceoffset = numpy.repeat(surfaceoffset,36,axis = 0)
	surfaceoffset = numpy.reshape(surfaceoffset,(lencubeslist,12,3))
	tempsurfaces = numpy.add(tempsurfaces,surfaceoffset)
	tempsurfaces = numpy.reshape(tempsurfaces,(12*(lencubeslist),3))
	
	oldshape = tempverticies.shape

	tempverticies = numpy.ravel(tempverticies)
	tempverticies = numpy.reshape(tempverticies,(int(len(tempverticies)/12),12))

	tempverticies = numpy.reshape(tempverticies,(oldshape[0]*oldshape[1],3))

	se = numpy.ravel(tempverticies[tempsurfaces])
	se = numpy.reshape(se,(int(len(se)/18),18))
	
	
	#return(se)
	return(se,hiddensides.flatten())

def bufferindices(renderdist):
	global available_buffers,used_buffers
	renderdist = (((renderdist*2)-1)**2)
	available_buffers = deque([[n,n+1,n+2,n+3,0]for n in range(1,(renderdist*4)+1,4)])

	used_buffers = [0for n in range(1,(renderdist*4)+1,4)]

def rebuild_buffer(which_chunk,used_buffers_index):
	global used_buffers,chunkbuffer,masks,lightmaps
	selectedbuffers = chunkbuffer[which_chunk]
	f,newmask = newverts(points,surfaces,activearray[activearray_indices[which_chunk]][:,:3])
	masks[which_chunk] = newmask
	f = f[newmask].ravel()

	v = numpy.ravel(vertindices_select[activearray[activearray_indices[which_chunk]][:,3]])
	v = numpy.reshape(v,(int(len(v)/6),6))[newmask].ravel()

	d = numpy.ones((len(v)),dtype='float32')

	glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[0])
	glBufferData(GL_ARRAY_BUFFER, (maxblocks*108)*4, None, GL_DYNAMIC_DRAW)
	glBufferSubData(GL_ARRAY_BUFFER,0, (len(f))*4, f)

	
	glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[1])
	glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
	glBufferSubData(GL_ARRAY_BUFFER,0, (len(v))*4, v)	

	glBindBuffer(GL_ARRAY_BUFFER, selectedbuffers[2])
	glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
	glBufferSubData(GL_ARRAY_BUFFER,0, (len(d))*4, d)

	glBindBuffer(GL_ARRAY_BUFFER, 0)

	used_buffers[used_buffers_index][4] = len(v)
	chunkbuffer[which_chunk] = copy.copy(used_buffers[used_buffers_index])
	#lightmaps[which_chunk] = numpy.concatenate((activearray[activearray_indices[which_chunk]],numpy.zeros((len(activearray[activearray_indices[which_chunk]]),6),dtype='int32')),axis=1)

def remove_block(removedcube,real,in_wk):
	#0 is real remove, 1 is real place, 2 is fake remove, 3 is fake place
	global world,activearray_indices,activearray,chunkbuffer,buffers_to_rebuild
	which_chunk = (int(removedcube[0]//8),int(removedcube[2]//8))
	removedcube = [int(removedcube[0]),int(removedcube[1]),int(removedcube[2])]

	currentplayerdata = (player,sunx,reversepath)
	
	if real:
		#print(removedcube)
		saveQueue.put((0,removedcube,currentplayerdata))
		wk = (numpy.where((activearray[activearray_indices[which_chunk]][:,:3]==removedcube).all(axis=1))[0])[0]
		activearray[activearray_indices[which_chunk]] = numpy.delete(activearray[activearray_indices[which_chunk]],wk,0)
		del world[which_chunk][tuple(removedcube)]
		
		adjacent1 = adjacent + removedcube
		for e in adjacent1:
			if world.get((int(e[0]//8),int(e[2]//8))).get(tuple(e)) != None and world.get((int(e[0]//8),int(e[2]//8))).get(tuple(e))[1] != 1:
				showblock = e.tolist()
				showblock.append(world.get((int(e[0]//8),int(e[2]//8))).get(tuple(e))[0])

				rebuildchunk = numpy.vstack([activearray[activearray_indices[(int(e[0]//8),int(e[2]//8))]],numpy.concatenate((numpy.array(showblock),[1]))])
				activearray[activearray_indices[(int(e[0]//8),int(e[2]//8))]] = rebuildchunk
				world[(int(e[0]//8),int(e[2]//8))][tuple(e)] = (world[(int(e[0]//8),int(e[2]//8))][tuple(e)][0],1)
				place_block(showblock,False)

	else:
		saveQueue.put((2,removedcube,currentplayerdata))
		wk = in_wk
	selectedbuffers = chunkbuffer[which_chunk]


	#wk is index to remove
	used_buffers_index = used_buffers.index(selectedbuffers)

	#OpenGL stuff
	if real:
		rebuild_buffer(which_chunk,used_buffers_index)
	else:
		buffers_to_rebuild.add((which_chunk,used_buffers_index))

	
	#used_buffers[used_buffers_index][4] -= 36
	#chunkbuffer[which_chunk] = copy.copy(used_buffers[used_buffers_index])

def place_block(addedcube,real):
	#0 is real remove, 1 is real place, 2 is fake remove, 3 is fake place
	global world,activearray_indices,activearray,chunkbuffer,used_buffers,buffers_to_rebuild
	addedcube = [int(addedcube[0]),int(addedcube[1]),int(addedcube[2]),int(addedcube[3])]
	which_chunk = (addedcube[0]//8,(addedcube[2]//8))

	currentplayerdata = (player,sunx,reversepath)

	if real:
		#print(addedcube)
		saveQueue.put((1,addedcube+[1],currentplayerdata))
		rebuildchunk = numpy.vstack([activearray[activearray_indices[which_chunk]],numpy.concatenate((numpy.array(addedcube),[1]))])
		activearray[activearray_indices[which_chunk]] = rebuildchunk
		if not which_chunk in world.keys():
			world[which_chunk] = dict()
		world[which_chunk][tuple(addedcube[:3])] = (addedcube[3],1)
		
		adjacent1 = adjacent + addedcube[0:3] 
		for e in adjacent1:
			if world.get((int(e[0]//8),int(e[2]//8))).get(tuple(e)) != None:
				adjacent2 = adjacent + e
				counter = 0
				for b in adjacent2:
					if world.get((int(b[0]//8),int(b[2]//8))).get(tuple(b)) != None:
						counter += 1
					else:break
				if counter == 6:

					world[(int(e[0]//8),int(e[2]//8))][tuple(e)] = (world[(int(e[0]//8),int(e[2]//8))][tuple(e)][0],0)
					wk = (numpy.where((activearray[activearray_indices[(int(e[0]//8),int(e[2]//8))]][:,:3]==e).all(axis=1))[0])[0]
					activearray[activearray_indices[(int(e[0]//8),int(e[2]//8))]] = numpy.delete(activearray[activearray_indices[(int(e[0]//8),int(e[2]//8))]],wk,0)
					remove_block(e,False,wk)
				
		if len(buffers_to_rebuild) > 0:
			for h in buffers_to_rebuild:
				rebuild_buffer(h[0],h[1])
			buffers_to_rebuild = set()
	else:
		saveQueue.put((3,addedcube+[1],currentplayerdata))

	selectedbuffers = chunkbuffer[which_chunk]
	#1 cube is 108 verts ((x,y,z)x36) 
	used_buffers_index = used_buffers.index(selectedbuffers)

	rebuild_buffer(which_chunk,used_buffers_index)

	#used_buffers[used_buffers_index][4] += lenv
	#chunkbuffer[which_chunk] = copy.copy(used_buffers[used_buffers_index])

def genbuffers(triangleverts,triangleindices):
	global used_buffers,available_buffers,VAOs,used_VAOs
	
	f = numpy.ravel(triangleverts)
	v = triangleindices
	#d = trianglelights

	lenf = len(f)
	lenv = len(v)
	#lend = len(d)

	#1 cube is 108 verts ((x,y,z)x36) and texcoords are 72
	for n in range(len(used_buffers)):
		if used_buffers[n] == 0:
			used_buffers[n] = available_buffers.popleft()
			used_buffers[n][4] = lenv
			break
	

	if True:
		currentvao = VAOs.pop()
		used_VAOs[currentvao] = n
		glBindVertexArray(currentvao)
		glBindBuffer(GL_ARRAY_BUFFER, used_buffers[n][0])
		glBufferData(GL_ARRAY_BUFFER, (maxblocks*108)*4, None, GL_DYNAMIC_DRAW)
		glBufferSubData(GL_ARRAY_BUFFER,0, (lenf)*4, f)
		glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

		
		glBindBuffer(GL_ARRAY_BUFFER, used_buffers[n][1])
		glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
		glBufferSubData(GL_ARRAY_BUFFER,0, (lenv)*4, v)
		glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 0, None)

		glBindBuffer(GL_ARRAY_BUFFER, used_buffers[n][2])
		glBufferData(GL_ARRAY_BUFFER, (maxblocks*36)*4, None, GL_DYNAMIC_DRAW)
		glBufferSubData(GL_ARRAY_BUFFER,0, (lenv)*4, numpy.ones((lenv),dtype='float32'))
		glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 0, None)
		
		glBindVertexArray(0)
	
	return(used_buffers[n])

def set3d(clear=True,cull=True):
	if clear:
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(fov, (width/height), 0.1, farclip)
	glMatrixMode(GL_MODELVIEW)
	glClearDepth(1.0)
	glFrontFace(GL_CCW)
	glDepthMask(GL_TRUE)
	glDepthFunc(GL_LESS)
	if cull:
		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)
	else:
		glClear(GL_DEPTH_BUFFER_BIT)
	glEnable(GL_DEPTH_TEST)
	glDepthRange(0.0,1.0)
	glBindTexture(GL_TEXTURE_2D, Texture)

def set2d():
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluOrtho2D(0, width, height, 0)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	glDisable(GL_CULL_FACE)
	glDisable(GL_DEPTH_TEST)
	glBindTexture(GL_TEXTURE_2D, 0)

def drawmenu(display,tex,buttonattributes):
	global buttontexcoords,renderdist
	width, height = display[0], display[1]
	#Draw dark overlay
	if True:
		menuverts = numpy.array([
			0,0,
			width,0,
			width,height,
			0,height,
		],dtype='float32')
		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+1)
		glBufferData(GL_ARRAY_BUFFER,len(menuverts)*4,menuverts,GL_STATIC_DRAW)
		
		glColor4f(0,0,0,0.5)
		glVertexPointer(2,GL_FLOAT,0,None)
		glEnableClientState(GL_VERTEX_ARRAY)
		glDrawArrays(GL_QUADS,0,4)
		glDisableClientState(GL_VERTEX_ARRAY)
		glBindBuffer(GL_ARRAY_BUFFER,0)
		glColor4f(1,1,1,1)
	glBindTexture(GL_TEXTURE_2D, tex)
	numbuttons,buttonsize,selected = buttonattributes
	buttonspacing = ((height/2+(10*buttonsize))-(height/2-(10*buttonsize)))/5
	buttonspacing += ((height/2+(10*buttonsize))-(height/2-(10*buttonsize)))
	buttonverts = numpy.array([
		[width/2-(100*buttonsize),height/2-(10*buttonsize)-(buttonspacing/2)],
		[width/2+(100*buttonsize),height/2-(10*buttonsize)-(buttonspacing/2)],
		[width/2+(100*buttonsize),height/2+(10*buttonsize)-(buttonspacing/2)],
		[width/2-(100*buttonsize),height/2+(10*buttonsize)-(buttonspacing/2)],
	],dtype='float32')

	buttonverts = numpy.concatenate((buttonverts,buttonverts + numpy.array([0,buttonspacing],dtype='float32')),axis=0)
	buttonverts = numpy.ravel(buttonverts)
	buttontex = numpy.ravel(numpy.array(buttontexcoords,dtype='float32')[selected])
	
	glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+2)
	glBufferData(GL_ARRAY_BUFFER,len(buttonverts)*4,buttonverts,GL_STATIC_DRAW)
	glEnableClientState(GL_VERTEX_ARRAY)
	glVertexPointer(2,GL_FLOAT,0,None)


	glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+3)
	glBufferData(GL_ARRAY_BUFFER,len(buttontex)*4,buttontex,GL_STATIC_DRAW)
	glTexCoordPointer(2,GL_FLOAT,0,None)
	glEnableClientState(GL_TEXTURE_COORD_ARRAY)
	
	
	glDrawArrays(GL_QUADS,0,8)
	glDisableClientState(GL_VERTEX_ARRAY)
	glDisableClientState(GL_TEXTURE_COORD_ARRAY)
	glBindBuffer(GL_ARRAY_BUFFER,0)
	glBindTexture(GL_TEXTURE_2D, 0)

def drawbuffers(model,view,used_buffers):
	global currentnear,is_looking,VAOs
	set3d()
	
	glUseProgram(shader)
	"""SHADER SETUP"""

	if True:
		projection_loc = glGetUniformLocation(shader, "projection")
		view_loc = glGetUniformLocation(shader, "view")
		model_loc = glGetUniformLocation(shader, "model")
		sun_loc = glGetUniformLocation(shader, "sun")
		pos_loc = glGetUniformLocation(shader, "pos")
		fog_loc = glGetUniformLocation(shader, "fogColor")
		lightmult_loc = glGetUniformLocation(shader, "lightMult")
		contrast_loc = glGetUniformLocation(shader, "contrast")
		glUniformMatrix4fv(projection_loc, 1, GL_FALSE, projection)
		glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
		glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)
	
		colormult = (suny+255)/(255*2)
		basecolor = [0.5, 0.69, 1.0]
		ambientcolor = 1.0

		if colormult <= 0.25:
			ambientcolor = colormult/0.25


		clearcolor = (ambientcolor*basecolor[0], ambientcolor*basecolor[1], ambientcolor*basecolor[2], 1)
		glClearColor(clearcolor[0],clearcolor[1],clearcolor[2],clearcolor[3])
		glUniform3f(sun_loc, sunx,suny,0)
		glUniform3f(pos_loc, player.x,player.y,player.z)
		glUniform4f(fog_loc,clearcolor[0],clearcolor[1],clearcolor[2],clearcolor[3])
		glUniform1f(contrast_loc,colormult)
		glUniform1f(lightmult_loc,max(ambientcolor,0.35))

	
	
	for n in used_VAOs:
		glBindVertexArray(n)
		glEnableVertexAttribArray(0)
		glEnableVertexAttribArray(1)
		glEnableVertexAttribArray(2)
		glDrawArrays( GL_TRIANGLES, 0,used_buffers[used_VAOs[n]][4])
	
	glBindVertexArray(0)
	glDisableVertexAttribArray(0)
	glDisableVertexAttribArray(1)
	glDisableVertexAttribArray(2)
	
	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glUseProgram(0)


	if is_looking:
		drawbounding(currentnear,model,view)
	
def draw2d(menuvisible,display,menuTex,hotbarTex,buttonattributes):
	set2d()
	drawhotbar(hotbarTex)

	if menuvisible:
		drawmenu(display,menuTex,buttonattributes)
	else:
		reticleH = int(round(height/135))
		if reticleH % 2 == 0: reticleH += 1

		glBegin(GL_LINES)
		glVertex2i(int(width/2)-reticleH,int(height/2))
		glVertex2i(int(width/2)+reticleH,int(height/2))
		glVertex2i(int(width/2),int(height/2)-reticleH)
		glVertex2i(int(width/2),int(height/2)+reticleH)
		glEnd()

def hotbarSetup():
	global hotbarVAO
	hotbarVAO = glGenVertexArrays(1)
	glBindVertexArray(hotbarVAO)
	glBindBuffer(GL_ARRAY_BUFFER, highestworldbuffer+7)
	glBufferData(GL_ARRAY_BUFFER, 4*4, None, GL_DYNAMIC_DRAW)
	glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)

	glBindBuffer(GL_ARRAY_BUFFER, highestworldbuffer+8)
	glBufferData(GL_ARRAY_BUFFER, 4*4, None, GL_DYNAMIC_DRAW)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, None)


	glBindBuffer(GL_ARRAY_BUFFER, highestworldbuffer+9)
	glBufferData(GL_ARRAY_BUFFER, 4*4, None, GL_DYNAMIC_DRAW)
	glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 0, None)
	glBindVertexArray(0)

def drawhotbar(hotbarTex):
	getupdate = player.hotbarupdate
	if getupdate: player.hotbarupdate = False
	
	"""Draw Hotbar Frame"""
	if getupdate:
		box_noborder = 20/270*height
		borderpadding = 1/270*height
		boxpadding = 5/270*height

		hotbardims = (182/270*height,22/270*height)
		hotbar_verts = numpy.array([
			[(width-hotbardims[0])/2,height],
			[(width-hotbardims[0])/2+hotbardims[0],height],
			[(width-hotbardims[0])/2+hotbardims[0],height-hotbardims[1]],
			[(width-hotbardims[0])/2,height-hotbardims[1]]
		],dtype='float32').flatten()
		
		
		selectboxdims = (24/270*height,24/270*height)
		selectbox_verts = numpy.array([
			[(width-selectboxdims[0])/2-box_noborder*4,height+(1/270*height)],
			[(width-selectboxdims[0])/2-box_noborder*4+selectboxdims[0],height+(1/270*height)],
			[(width-selectboxdims[0])/2-box_noborder*4+selectboxdims[0],height-selectboxdims[1]+(1/270*height)],
			[(width-selectboxdims[0])/2-box_noborder*4,height-selectboxdims[1]+(1/270*height)]
		],dtype='float32')

		selectbox_verts[:,:1] = selectbox_verts[:,:1]+box_noborder*(player.hotbarselect)
		selectbox_verts = selectbox_verts.flatten()
		hotbar_verts = numpy.concatenate((hotbar_verts,selectbox_verts))
		hotbar_tex = hotbartexcoords.ravel()

	"""OpenGL Stuff"""
	if True:
		glBindTexture(GL_TEXTURE_2D, hotbarTex)
		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+5)
		if getupdate: glBufferData(GL_ARRAY_BUFFER,len(hotbar_verts)*4,hotbar_verts,GL_STATIC_DRAW)
		glEnableClientState(GL_VERTEX_ARRAY)
		glVertexPointer(2,GL_FLOAT,0,None)
		
		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+6)
		if getupdate: glBufferData(GL_ARRAY_BUFFER,len(hotbar_tex)*4,hotbar_tex,GL_STATIC_DRAW)
		glTexCoordPointer(2,GL_FLOAT,0,None)
		glEnableClientState(GL_TEXTURE_COORD_ARRAY)

		glDrawArrays(GL_QUADS,0,8)
		glDisableClientState(GL_VERTEX_ARRAY)
		glDisableClientState(GL_TEXTURE_COORD_ARRAY)
		glBindBuffer(GL_ARRAY_BUFFER,0)
		glBindTexture(GL_TEXTURE_2D, 0)
	
	
	"""Draw Hotbar Icons"""
	global hotbaritems
	set3d(clear=False,cull=False)
	glUseProgram(uishader)
	if getupdate:
		hotbarstart = (width-(180/270*height))/2

		iconsize = (-boxpadding+hotbarstart+box_noborder)-(boxpadding+hotbarstart)
		
		vv = numpy.array([
			[boxpadding+hotbarstart, -boxpadding+height-borderpadding,0],
			[-boxpadding+hotbarstart+box_noborder, -boxpadding+height-borderpadding,0],
			[-boxpadding+hotbarstart+box_noborder,  boxpadding+height-hotbardims[1]+borderpadding,0],
			[boxpadding+hotbarstart,boxpadding+height-hotbardims[1]+borderpadding,0],

			[boxpadding+hotbarstart, -boxpadding+height-borderpadding,-iconsize], #4
			[-boxpadding+hotbarstart+box_noborder, -boxpadding+height-borderpadding,-iconsize], #5
			[-boxpadding+hotbarstart+box_noborder,  boxpadding+height-hotbardims[1]+borderpadding,-iconsize], #6
			[boxpadding+hotbarstart,boxpadding+height-hotbardims[1]+borderpadding,-iconsize], #7
		])

		middleoficon=(numpy.sum(vv[:,0])/8,numpy.sum(vv[:,1])/8,numpy.sum(vv[:,2])/8)

		icon_verts_colors = numpy.array([
			vv[0],vv[1],vv[2],
			vv[0],vv[2],vv[3],

			vv[1],vv[5],vv[6],
			vv[1],vv[6],vv[2],

			vv[4],vv[5],vv[6],
			vv[4],vv[6],vv[7],

			vv[4],vv[0],vv[3],
			vv[4],vv[3],vv[7],
			
			vv[4],vv[5],vv[1],
			vv[4],vv[1],vv[0],

			vv[3],vv[2],vv[6],
			vv[3],vv[6],vv[7]
		],dtype='float32')

		#numpy.set_printoptions(suppress=True)
		iconcolors = numpy.ones((30,1),dtype='float32')*0.6
		iconcolors = numpy.concatenate((iconcolors,numpy.ones((6,1),dtype='float32')))
		icon_verts_colors = numpy.hstack((icon_verts_colors,iconcolors))
		icon_verts_colors = icon_verts_colors.flatten()
		icon_verts_colors = numpy.array([icon_verts_colors]*9,dtype='float32').flatten()
		hotbaritems = player.inventory[3][player.inventory[3]>=0]
		icon_tex = fulltexcoords[hotbaritems].flatten()

		iconrot = (135,-30)
		for n in range(9):
			icon_model = glm.mat4()
			icon_model = glm.translate(icon_model,glm.vec3(n*box_noborder,0,0))
			icon_model = glm.translate(icon_model,glm.vec3(middleoficon))
			icon_model = glm.rotate(icon_model,glm.radians(iconrot[0]),glm.vec3(0,1,0))
			icon_model = glm.rotate(icon_model,glm.radians(iconrot[1]),glm.vec3(math.cos(math.radians(iconrot[0])), 0, math.sin(math.radians(iconrot[0]))))
			icon_model = glm.translate(icon_model,glm.vec3(-middleoficon[0],-middleoficon[1],-middleoficon[2]))
			icon_model = numpy.array(icon_model)

			icon_model_loc = glGetUniformLocation(uishader, "m"+str(n+1))
			glUniformMatrix4fv(icon_model_loc, 1, GL_FALSE, icon_model)

	
	orth_loc = glGetUniformLocation(uishader, "orth")
	glUniformMatrix4fv(orth_loc, 1, GL_FALSE, numpy.array(glm.ortho(0.0, width, height, 0.0, -1000.0, 1000.0)))
	
	if getupdate:
		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+7)
		glBufferData(GL_ARRAY_BUFFER,len(icon_verts_colors)*4,icon_verts_colors,GL_STATIC_DRAW)

		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+8)
		glBufferData(GL_ARRAY_BUFFER,len(icon_tex)*4,icon_tex,GL_STATIC_DRAW)

		glBindBuffer(GL_ARRAY_BUFFER,highestworldbuffer+9)
		glBufferData(GL_ARRAY_BUFFER,len(hotbaritems)*36*4,numpy.repeat(numpy.arange(0,len(hotbaritems),1,dtype='int32'),36),GL_STATIC_DRAW)
		glBindBuffer(GL_ARRAY_BUFFER,0)

	glBindVertexArray(hotbarVAO)
	glEnableVertexAttribArray(0)
	glEnableVertexAttribArray(1)
	glEnableVertexAttribArray(2)


	glDrawArrays( GL_TRIANGLES, 0,36*len(hotbaritems))

	
	glDisableVertexAttribArray(0)
	glDisableVertexAttribArray(1)
	glDisableVertexAttribArray(2)
	glUseProgram(0)
	set2d()

def drawbounding(lookingblock,model,view):
	glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
	glLineWidth(1.5)
	glEnable(GL_LINE_SMOOTH)
	verticies = boundingpoints+lookingblock
	tempverts = verticies[quadsurfaces]


	boundingverts = numpy.array(tempverts,dtype='float32')
	boundingverts = boundingverts.flatten()
	glBindBuffer(GL_ARRAY_BUFFER, highestworldbuffer+4)
	glBufferData(GL_ARRAY_BUFFER, len(boundingverts)*4, boundingverts, GL_STATIC_DRAW)
	glBindBuffer(GL_ARRAY_BUFFER, 0)

	glUseProgram(lineshader)
	lineprojection_loc = glGetUniformLocation(lineshader, "projection")
	lineview_loc = glGetUniformLocation(lineshader, "view")
	linemodel_loc = glGetUniformLocation(lineshader, "model")
	incolor_loc = glGetUniformLocation(lineshader, "inColor")
	glUniformMatrix4fv(lineprojection_loc, 1, GL_FALSE, projection)
	glUniformMatrix4fv(lineview_loc, 1, GL_FALSE, view)
	glUniformMatrix4fv(linemodel_loc, 1, GL_FALSE, model)
	glUniform4f(incolor_loc, 0,0,0,1)
	glBindBuffer(GL_ARRAY_BUFFER, highestworldbuffer+4)
	lineposition = glGetAttribLocation(lineshader, 'position')
	glVertexAttribPointer(lineposition, 3, GL_FLOAT, GL_FALSE, 0, None)
	glEnableVertexAttribArray(lineposition)
	
	glBindBuffer(GL_ARRAY_BUFFER, 0)

	glDrawArrays( GL_QUADS, 0,24)
	glDisableVertexAttribArray(lineposition)
	glUseProgram(0)
	glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
	glLineWidth(1.0)
	glDisable(GL_LINE_SMOOTH)

def movement(x,y,z,pitch,yaw):

	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	glRotatef(pitch,0,1,0)
	glRotatef(yaw, math.cos(math.radians(pitch)), 0, math.sin(math.radians(pitch)))
	glTranslatef(-x,-y,-z)

	model = glm.mat4()
	view = glm.mat4()
	#view = glm.rotate(model,glm.radians(45),glm.vec3(0,1,0))
	view = glm.rotate(view,glm.radians(pitch),glm.vec3(0,1,0))
	view = glm.rotate(view,glm.radians(yaw),glm.vec3(math.cos(math.radians(pitch)), 0, math.sin(math.radians(pitch))))
	
	view = glm.translate(view,glm.vec3(-x,-y,-z))
	
	
	return numpy.array(model),numpy.array(view)

def loadimg(img_data,sizew,sizeh):
	"""WHITE LINES ARE CAUSED BY ADJACENT TEXTURE ON TEXTURE ATLAS"""
	Texture = glGenTextures(1)
	glEnable(GL_TEXTURE_2D)
	glBindTexture(GL_TEXTURE_2D, Texture)
	
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT )
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT )
	
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, sizew, sizeh, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
	#glGenerateMipmap(GL_TEXTURE_2D)
	glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
	glEnable(GL_BLEND)
	
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	return Texture
				 
def compressed_pickle(title, data):
	
	keys = numpy.fromiter(data.keys(),dtype=[('x', '<i4'), ('y', '<i4'),('z', '<i4')])
	vals = numpy.fromiter(data.values(),dtype=[('t', '<i4'), ('v', '<i4')])
	data = numpy.column_stack((keys['x'], keys['y'],keys['z'],vals['t'],vals['v']))
	
	title = "world_saves\\"+slot+"\\"+title

	with bz2.BZ2File(title + '.pbz2', 'wb') as f: 
		cPickle.dump(data, f)

"""Process"""	
def async_compressed_pickle(saveQueue):
	while True:
		retr = saveQueue.get()
		blocktoedit = [retr[1][0],retr[1][1],retr[1][2]]
		which_chunk = (int(blocktoedit[0]//8),int(blocktoedit[2]//8))
		data = decompress_nonnp(str(which_chunk))
		if retr[0] == 1:
			data = numpy.concatenate((data,[retr[1]]))
		else:
			wk = (numpy.where((data[:,:3]==blocktoedit).all(axis=1))[0])[0]
			if retr[0] == 0:
				data = numpy.delete(data,wk,0)
			elif retr[0] == 2:
				data[wk][4] = 0
			elif retr[0] == 3:
				data[wk][4] = 1
		
		title = "world_saves\\"+slot+"\\"+str(which_chunk)
		with bz2.BZ2File(title + '.pbz2', 'wb') as f: 
			cPickle.dump(data, f)

		title = "world_saves\\"+slot+"\\"+'player_data'
		with bz2.BZ2File(title + '.pbz2', 'wb') as f: 
			cPickle.dump(retr[2], f)

"""Thread"""
def decompress_pickle(loadTicket):
	global loadQueue,loadOut
	internalQueue = deque()
	while Running:
		loadTicket.get()
		while len(loadQueue) > 0:
			chunk_file = loadQueue.popleft()
			file = "world_saves\\"+slot+"\\"+str(chunk_file)+".pbz2"
			data = bz2.BZ2File(file, 'rb')
			data = cPickle.load(data)
			
			data = {tuple(gh[:3]):(gh[3],gh[4]) for gh in data}
			
			internalQueue.append(data)
			time.sleep(0.01)
		loadOut.extend(internalQueue)
		internalQueue = deque()

def compressed_nonnp(title, data):
	title = "world_saves\\"+slot+"\\"+title
	with bz2.BZ2File(title + '.pbz2', 'w') as f: 
		cPickle.dump(data, f)

def decompress_nonnp(file):
	file = "world_saves\\"+slot+"\\"+file+".pbz2"
	data = bz2.BZ2File(file, 'rb')
	data = cPickle.load(data)
	return data

def gravity(sincetime,notexarray,inx,iny,inz):
	fall = (-1/5*(12)*(sincetime**2))
	fall = max(fall,-2)
	iny += fall
	outfall = fallcollision(notexarray,inx,iny,inz)
	if outfall[0]:
		iny = outfall[2]+1.909
		sincetime = 0
	else:
		sincetime += 0.01
	return (iny,sincetime)

def sortnearest(bq,bd):
	bd.sort(key=lambda pq:sum((aq-bq)**2for aq,bq in zip(bq,pq)))
	return bd

"""Process"""
def loadworld(inQueue,outQueue):
	while True:
		chunkqueue = inQueue.get()
		
		for v in chunkqueue.copy():
			if worldtype == 3:
				outChunk = cave_terraingen(seed,v,adjacent,adjacent[:4,:2])
			else:
				outChunk = async_terraingen(seed,worldtype,v[0],v[1],adjacent[:4,:2],tree)[v]
			
			outQueue.put(outChunk)
			chunkqueue.remove(v)
			compressed_pickle(str(v),outChunk)
			time.sleep(0.001)

def loadunload_chunks(starting=False):
	global loadedchunks_range,prevloaded,activearray,activearray_indices,used_buffers,available_buffers,chunkbuffer,seed,world
	global chunkstoload,chunkstounload,loading,VAOs,used_VAOs,loadOut,loadQueue,loading_fromfile,commitQueue,commitCache
	global masks
	global lightQ
	global is_Loading
	loadedchunks = loadedchunks_range+numpy.array([[int(player.x//8),int(player.z//8)]],dtype='int32')
	settuple = set(map(tuple, loadedchunks))
			
	"""Retrieve Chunks"""
	if True:
		"""From File (Thread)"""
		while len(loadOut) > 0:
			getload = loadOut.popleft()
			for un in getload:
				break
			commitQueue.append(((int(un[0]//8),int(un[2]//8)),getload))
			commitCache.add((int(un[0]//8),int(un[2]//8)))
			loading_fromfile.remove((int(un[0]//8),int(un[2]//8)))


		"""Newly Generated (Process)"""
		if not outQueue.empty():				
			retrieveworld = outQueue.get()
			for bn in retrieveworld:
				break
			commitQueue.append(((int(bn[0]//8),int(bn[2]//8)),retrieveworld))
			commitCache.add((int(bn[0]//8),int(bn[2]//8)))
			loading.remove((int(bn[0]//8),int(bn[2]//8)))

	
	"""Request for Chunks from Processes/Thread"""
	if True:
		toload = settuple-world.keys()
		if len(toload) > 0:
			is_Loading = True
		toload = toload-commitCache
		toload = toload-loading
		
		send_ticket = False
		for nj in toload.copy():
			file = "world_saves\\"+slot+"\\"+str(nj)+".pbz2"
			if os.path.exists(file):
				if nj not in loading_fromfile.copy():
					loadQueue.append(nj)
					loading_fromfile.add(nj)
					send_ticket = True
				toload.remove(nj)

		if send_ticket:
			loadTicket.put(True)	

		inQueue.put(sortnearest([player.x,player.z],list(toload)))
		loading.update(toload)
		

	if len(commitQueue)>0:
		pullfromcache = commitQueue.popleft()
		world[pullfromcache[0]] = pullfromcache[1]
		commitCache.remove(pullfromcache[0])
	
	loadedchunks = settuple.intersection(world.keys())
	chunkstounload.update(prevloaded-loadedchunks)
	chunkstoload.update(loadedchunks-prevloaded)
	prevloaded = copy.copy(loadedchunks)
	
	
	if len(chunkstounload) > 0 or len(chunkstoload) > 0:
		
		for o,u in zip_longest(chunkstounload.copy(),chunkstoload.copy()):
			"""Unload Chunk"""
			if o != None and o in world.keys():
				world,activearray,activearray_indices,chunkbuffer,used_buffers,available_buffers,VAOs,used_VAOs = unload_chunk(o,world,activearray,activearray_indices,chunkbuffer,used_buffers,available_buffers,VAOs,used_VAOs)
				chunkstounload.remove(o)
				del masks[o]
				try:del lightmaps[o]
				except:pass
				try:lightQ.remove(n)
				except:pass
			"""Load Chunk"""
			if u != None and u in world.keys():
			
				dictconvert = world[u]
				dictconvert = dict_to_numpy(dictconvert.items())

				if len(activearray) > 0:
					activearray = activearray + [dictconvert]
					activearray_indices[u] = len(activearray)-1
				else:
					activearray = [dictconvert]
					activearray_indices[u] = 0
				
				newvertindices = numpy.ravel(vertindices_select[dictconvert[:,3]])
				
				newvertindices = numpy.reshape(newvertindices,(int(len(newvertindices)/6),6))
				newcubeverts,hiddenmask = newverts(points,surfaces,dictconvert[:,:3])

				
				newcubeverts = newcubeverts[hiddenmask]
				newvertindices = newvertindices[hiddenmask]

				newvertindices = numpy.ravel(newvertindices)
				masks[u] = hiddenmask
				
				#temptime = time.time()
				chunkbuffer[u] = genbuffers(newcubeverts,newvertindices)
				"""
				if u not in lightmaps and not starting:
					lightQ.add(u)
				"""
				#print(round((time.time()-temptime)*1000,8))
				chunkstoload.remove(u)
						
def e_dist(a, b):

	"""Distance calculation for 1D, 2D and 3D points using einsum
	: a, b   - list, tuple, array in 1,2 or 3D form
	:-----------------------------------------------------------------------
	"""
	
	b = numpy.atleast_2d(b)
	a_dim = a.ndim
	b_dim = b.ndim
	if a_dim == 1:
		a = a.reshape(1, 1, a.shape[0])
	if a_dim >= 2:
		a = a.reshape(numpy.prod(a.shape[:-1]), 1, a.shape[-1])
	if b_dim > 2:
		b = b.reshape(numpy.prod(b.shape[:-1]), b.shape[-1])
	diff = a - b
	dist_arr = numpy.einsum('ijk,ijk->ij', diff, diff)
	dist_arr = numpy.sqrt(dist_arr)
	dist_arr = numpy.squeeze(dist_arr)
	return dist_arr

def main():
	global Running
	global world,currentnear,is_looking,seed,Texture
	global player
	global fov,projection
	global sunx,suny,reversepath
	global buffers_to_rebuild
	bufferindices(renderdist)
	
	"""SETUP"""
	if True:
		player = Player()
		lastblockchange,lastpress,lastplace=0,0,0
		mousemove = (0,0)
		mousepos = (0,0)
		justswitched = True
		inwindow = True
		buffers_to_rebuild = set()
		world = dict()

		"""WINDOW INIT"""
		pygame.init()
		display = (width,height)
		pygame.display.set_caption("Blocks (Preparing...)")
		icon = pygame.image.load(resource_path('cobblestone.png'))
		pygame.display.set_icon(icon)
		if fullscreen == 1:
			pygame.display.set_mode(display, FULLSCREEN|DOUBLEBUF|OPENGL)
		else:
			pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
		
		set3d()

		"""LOAD TEXTURES"""
		"""
		if True:
			im = pil.open("sphaxtextures.png")
			im = im.tobytes("raw", "RGBA", 0, -1)
			am = pil.open('texture.png')
			am=am.tobytes("raw", "RGBA", 0, -1)
			bm = pil.open("cursed.png")
			bm=bm.tobytes("raw", "RGBA", 0, -1)
			cm = pil.open("gui.png")
			cm=cm.tobytes("raw", "RGBA", 0, -1)
			gm = pil.open("hotbar.png")
			gm=gm.tobytes("raw", "RGBA", 0, -1)
			with bz2.BZ2File('textures' + '.pbz2', 'w') as foo: 
				cPickle.dump((im,am,bm,cm,gm), foo)
		"""
		fileload = bz2.BZ2File(resource_path('textures.pbz2'), 'rb')
		fileload = cPickle.load(fileload)
		if highres:
			alltextures = (loadimg(fileload[0],2048,2048),loadimg(fileload[1],256,256),loadimg(fileload[2],768,768),loadimg(fileload[3],200,160),loadimg(fileload[4],256,256))   
		else:
			alltextures = (loadimg(fileload[1],256,256),loadimg(fileload[2],768,768),loadimg(fileload[3],200,160),loadimg(fileload[4],256,256))
		Texture = alltextures[0]

		"""OPENGL SHADER COMPILATION"""
		global shader,lineshader,uishader
		shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),OpenGL.GL.shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER),validate=False)
		lineshader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(LINE_VERTEX_SHADER, GL_VERTEX_SHADER),OpenGL.GL.shaders.compileShader(LINE_FRAGMENT_SHADER, GL_FRAGMENT_SHADER))
		uishader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(UI_VERTEX_SHADER, GL_VERTEX_SHADER),OpenGL.GL.shaders.compileShader(UI_FRAGMENT_SHADER, GL_FRAGMENT_SHADER),validate=False)
		
		menuvisible = False
		buttonattributes = [2,2,[0,2]]
		lastsave = 0
		lastfov = 0


		"""CHUNK LOAD PREP"""
		global prevloaded,activearray,activearray_indices,loadedchunks_range,chunkbuffer,chunkstoload,chunkstounload,loading,loading_fromfile,commitQueue,commitCache
		global VAOs,used_VAOs
		global masks
		global lightmaps,lightQ
		global is_Loading
		is_Loading = False
		loadedchunks_range = numpy.array([[n,i] for n in range(-(renderdist-1),renderdist) for i in range(-(renderdist-1),renderdist)],dtype='int32')
		
		
		activearray = numpy.empty((0,0,4),dtype='int')
		activearray_indices = dict()
		chunkbuffer = dict()
		
		prevloaded = set()
		chunkstoload = set()
		chunkstounload = set()

		loading = set()
		loading_fromfile = set()

		commitQueue = deque()
		commitCache = set()

		masks = dict()

		lightmaps = dict()
		lightQ = set()

		VAOs = {glGenVertexArrays(1) for b in range(len(available_buffers))}
		used_VAOs = dict()
		hotbarSetup()
	
	
	try:
		get_playerdata = decompress_nonnp('player_data')
		player,sunx,reversepath = get_playerdata
		#player,nsunx,nreversepath = get_playerdata
		del get_playerdata
		player.hotbarupdate = True
	except:
		while not len(activearray) > 0:
			loadunload_chunks()
		cubes = numpy.concatenate(activearray)
		ystart= cubes[numpy.logical_and(cubes[:,0] == player.x,cubes[:,2] == player.z)]
		del cubes
		try:
			player.y = numpy.max(ystart[:,1:2])+2
		except: player.y = 60

	pygame.display.set_caption("Blocks (Loading Chunks...)")
	while len(activearray_indices) < ((renderdist*2)-1)**2:
		loadunload_chunks()


	pygame.display.set_caption("Blocks")
	clock = pygame.time.Clock()

	while Running:
		"""CHUNK LOADING"""
		is_Loading = False
		loadunload_chunks()
		#newlight()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				Running = False
			if time.time()-lastblockchange>0.15:
				if inwindow and pygame.mouse.get_focused() and event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == 5:
						if player.hotbarselect+1 > 8:
							player.update_selection(1)
						else:
							player.update_selection(player.hotbarselect+2)
					if event.button == 4:
						if player.hotbarselect-1 < 0:
							player.update_selection(9)
						else:
							player.update_selection(player.hotbarselect)

		if inwindow and pygame.mouse.get_focused():
			"""GET MOUSE MOVEMENT AND UPDATE PITCH/YAW"""
			mousemove = pygame.mouse.get_rel()
			if justswitched:
				justswitched = False
				mousemove = (0,0)
				pygame.mouse.set_pos(mousepos)
				
			player.pitch += (mousemove[0]/10)
			if player.pitch < 0:
				player.pitch = 360 + (mousemove[0]/10)
			elif player.pitch > 360:
				player.pitch = (mousemove[0]/10)
			player.yaw += (mousemove[1]/10)
			if player.yaw > 90:
				player.yaw = 90
			elif player.yaw < -90:
				player.yaw = -90
			
			pygame.mouse.set_visible(False)
			pygame.event.set_grab(True)
			menuvisible = False
		else:
			"""SHOW MENU"""
			if inwindow :inwindow = False
			justswitched = True
			mousepos = pygame.mouse.get_pos()
			pygame.event.set_grab(False)
			pygame.mouse.set_visible(True)
			menuvisible = True
			buttonattributes[2] = [0,2]
			buttonsize = buttonattributes[1]
			buttonspacing = ((height/2+(10*buttonsize))-(height/2-(10*buttonsize)))/5
			buttonspacing += ((height/2+(10*buttonsize))-(height/2-(10*buttonsize)))

			widthrange = [width/2-(100*buttonsize),width/2+(100*buttonsize)]
			heightrange = [height/2-(10*buttonsize)-(buttonspacing/2),height/2+(10*buttonsize)-(buttonspacing/2)]
			if pygame.mouse.get_focused():
				mousepos = pygame.mouse.get_pos()
				if widthrange[0]<=mousepos[0]<=widthrange[1]:
					"""SAVE BUTTON CLICKED"""
					if heightrange[0]<=mousepos[1]<=heightrange[1]:
						buttonattributes[2][0] = 1
						if pygame.mouse.get_pressed()[0] == 1 and time.time()-lastsave > 0.3:
							for saving in activearray_indices:
								compressed_pickle(str(saving),world[saving])
							compressed_nonnp('player_data',(player,sunx,reversepath))
							lastsave = time.time()
					"""QUIT BUTTON CLICKED"""
					if heightrange[0]+buttonspacing<=mousepos[1]<=heightrange[1]+buttonspacing:
							buttonattributes[2][1] = 3
							if pygame.mouse.get_pressed()[0] == 1:
								Running = False
				
		"""KEYBOARD INPUT"""
		if pygame.key.get_pressed()[pygame.K_ESCAPE]:
			if time.time()-lastpress > 0.15:
				lastpress = time.time()
				inwindow = not inwindow
		if inwindow and pygame.mouse.get_focused():
			nearcubes = []
			for i in adjacent_chunks + (int(player.x//8),int(player.z//8)):
				try:nearcubes.append(activearray[activearray_indices[tuple(i)]])
				except:pass
			try:
				nearcubes = numpy.concatenate(nearcubes)
			except:
				nearcubes = numpy.array([[0,256,0]])
			nearcubes = nearcubes[numpy.logical_and(nearcubes[:,0] > player.x-7,nearcubes[:,0] < player.x+7)]
			nearcubes = nearcubes[numpy.logical_and(nearcubes[:,1] > player.y-7,nearcubes[:,1] < player.y+7)]
			nearcubes = nearcubes[numpy.logical_and(nearcubes[:,2] > player.z-7,nearcubes[:,2] < player.z+7)]
			"""
			#Freelook
			x += numpy.sin(numpy.deg2rad(pitch))*numpy.cos(numpy.deg2rad(yaw))*0.1
			z -= numpy.cos(numpy.deg2rad(pitch))*numpy.cos(numpy.deg2rad(yaw))*0.1
			y = y + -1*(numpy.sin(numpy.deg2rad(yaw)))*0.1
			"""
			if pygame.key.get_pressed()[pygame.K_LCTRL]:
				lastfov = time.time()
				if fov != 20:
					fov = 20
					projection = glm.perspective(numpy.deg2rad(fov),width/height,0.1,farclip)
					projection = numpy.array(projection)
			else:
				if time.time()-lastfov>0.1:
					if fov != start_fov:
						fov = copy.copy(start_fov)
						projection = glm.perspective(numpy.deg2rad(fov),width/height,0.1,farclip)
						projection = numpy.array(projection)
			if pygame.key.get_pressed()[pygame.K_LSHIFT] and player.flytoggle == 1:
				player.y -= 0.1
				if collisionpadding(nearcubes[:,:3],player.x,player.y,player.z): player.y += 0.1
			

			if pygame.key.get_pressed()[pygame.K_w]:
				xchange = math.sin(math.radians(player.pitch))*0.1
				zchange = -math.cos(math.radians(player.pitch))*0.1

				xmove,zmove = False,False
				if not collisionpadding(nearcubes[:,:3],player.x+xchange,player.y,player.z):xmove = True
				if not collisionpadding(nearcubes[:,:3],player.x,player.y,player.z+zchange):zmove = True

				if xmove:
					if not zmove:
						
						if 0<= player.pitch <= 90:
							xchange *=(abs(0-player.pitch)/90)
						if 270<=player.pitch<=360:
							xchange *=(abs(360-player.pitch)/90)
						if 90<=player.pitch<=270:
							xchange *= (abs(180-player.pitch)/90)		
					player.x += xchange
					
				if zmove:
					if not xmove:
						if -90 <= (player.pitch-90) <= 90:
							zchange *=(abs(90-player.pitch)/90)
						else:
							zchange *=(abs(270-player.pitch)/270*3)
					player.z += zchange				
			if pygame.key.get_pressed()[pygame.K_s]:
				xchange = -math.sin(math.radians(player.pitch))*0.1
				zchange = math.cos(math.radians(player.pitch))*0.1
				if not collisionpadding(nearcubes[:,:3],player.x+xchange,player.y,player.z):player.x += xchange
				if not collisionpadding(nearcubes[:,:3],player.x,player.y,player.z+zchange):player.z += zchange
			if pygame.key.get_pressed()[pygame.K_a]:
				xchange = -math.sin(math.radians(player.pitch+90))*0.1
				zchange = math.cos(math.radians(player.pitch+90))*0.1
				if not collisionpadding(nearcubes[:,:3],player.x+xchange,player.y,player.z):player.x += xchange
				if not collisionpadding(nearcubes[:,:3],player.x,player.y,player.z+zchange):player.z += zchange                 
			if pygame.key.get_pressed()[pygame.K_d]:
				xchange = math.sin(math.radians(player.pitch+90))*0.1
				zchange = -math.cos(math.radians(player.pitch+90))*0.1
				if not collisionpadding(nearcubes[:,:3],player.x+xchange,player.y,player.z):player.x += xchange
				if not collisionpadding(nearcubes[:,:3],player.x,player.y,player.z+zchange):player.z += zchange

			if time.time()-lastblockchange>0.15:
				if pygame.key.get_pressed()[K_TAB]:
					player.flytoggle = not player.flytoggle
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_1]:
					player.update_selection(1)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_2]:
					player.update_selection(2)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_3]:
					player.update_selection(3)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_4]:
					player.update_selection(4)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_5]:
					player.update_selection(5)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_6]:
					player.update_selection(6)  
					lastblockchange = time.time()             
				if pygame.key.get_pressed()[pygame.K_7]:
					player.update_selection(7)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_8]:
					player.update_selection(8)
					lastblockchange = time.time()
				if pygame.key.get_pressed()[pygame.K_9]:
					player.update_selection(9)
					lastblockchange = time.time()

				if pygame.key.get_pressed()[pygame.K_F1] and highres:
					lastblockchange = time.time()
					if Texture != alltextures[1]:
						Texture = alltextures[1]
					elif Texture == alltextures[1]:
						Texture = alltextures[0]
				if pygame.key.get_pressed()[pygame.K_F2]:
					lastblockchange = time.time()
					if Texture != alltextures[len(alltextures)-3]:
						Texture = alltextures[len(alltextures)-3]
					else:
						Texture = alltextures[0]
			if pygame.key.get_pressed()[pygame.K_SPACE]:
					
				if player.flytoggle:
					player.y += 0.1
					if collisionpadding(nearcubes[:,:3],player.x,player.y,player.z): player.y -= 0.1
					
				if collisionpadding(nearcubes[:,:3],player.x,(player.y-0.1),player.z):
					if (not player.flytoggle) and (not player.jumping):
						player.jumping = True
		
		"""GET NEARBY BLOCKS FOR PHYSICS CHECKING"""
		nearcubes = []
		for i in adjacent_chunks + (int(player.x//8),int(player.z//8)):
			try:nearcubes.append(activearray[activearray_indices[tuple(i)]])
			except:pass
		try:
			nearcubes = numpy.concatenate(nearcubes)
		except:
			nearcubes = numpy.array([[0,256,0]])
		checknear = copy.copy(nearcubes[:,:3])
		checknear = checknear[numpy.logical_and(checknear[:,0] > player.x-7,checknear[:,0] < player.x+7)]
		checknear = checknear[numpy.logical_and(checknear[:,2] > player.z-7,checknear[:,2] < player.z+7)]
		
		"""PHYSICS"""
		if player.jumping:
			if player.timesincejump < 30 and (not player.flytoggle):
				jumpheight = 0.15+(-1/4*(0.0025)*(player.timesincejump**2))
				player.timesincejump += 1
				if jumpheight >0:
					player.y += jumpheight

					if collisionpadding(checknear,player.x,player.y,player.z):
						player.y -= jumpheight
						player.timesincejump = -1
						player.jumping = False
				
			else:
				player.timesincejump = -1
				player.jumping = False
			
		if not player.flytoggle:
			player.y,player.timesince = gravity(player.timesince,checknear,player.x,player.y,player.z)       
		else: player.timesince = 0
			
		"""CHECK BLOCK IN LINE OF SIGHT/BREAK-PLACE"""
		temppos = numpy.array([player.x,player.y,player.z])
		checknear = checknear[numpy.logical_and(checknear[:,1] > temppos[1]-7,checknear[:,1] < temppos[1]+7)]
		
		
		is_looking = False
		if len(checknear) > 0:
			sorting = e_dist(checknear, temppos)
			checkclose=checknear[numpy.argsort(sorting)][numpy.arange(len(sorting[sorting <= 36]))]

			currentnear = lookingat(player.x,player.y,player.z,numpy.deg2rad(player.pitch),numpy.deg2rad(player.yaw),checkclose)
			if type(currentnear) != type(None):
				is_looking = True

			if is_looking:
				cn = currentnear
				
				if time.time()-lastplace>0.15:
					mousepress = pygame.mouse.get_pressed()
					#print(cn)
					if mousepress != (0,0,0) and menuvisible == False:

						lastplace = time.time()
						"""Mousepress[0] is Left Click, Mousepress[2] is Right Click"""
						if mousepress[2] == 1 and player.blockselection != -1:
							if int(currentnear[1]) < 255:
								"""Check Which Side"""
								if True:
									checkside = [
										[cn[0],cn[1],cn[2]+0.5],
										[cn[0],cn[1],cn[2]-0.5],
										[cn[0]+0.5,cn[1],cn[2]],
										[cn[0]-0.5,cn[1],cn[2]],
										[cn[0],cn[1]+0.5,cn[2]],
										[cn[0],cn[1]-0.5,cn[2]]
									]

									distfromcenter = numpy.linalg.norm(temppos-numpy.array(cn))-0.5
									reversex = player.x+ numpy.sin(numpy.deg2rad(player.pitch))*numpy.cos(numpy.deg2rad(player.yaw))*distfromcenter
									reversez = player.z- numpy.cos(numpy.deg2rad(player.pitch))*numpy.cos(numpy.deg2rad(player.yaw))*distfromcenter
									reversey = player.y+ -1*(numpy.sin(numpy.deg2rad(player.yaw)))*distfromcenter
									side_guess = [reversex,reversey,reversez]

									sides = copy.copy(checkside)
									sides = sortnearest(side_guess,sides)
									countercheckside = copy.copy(checkside)
									checkside = sides

								for ig in range(3):
									if checkside[0][ig] != cn[ig]:
										newblock = copy.copy(checkside[0])
										timesneg = -1
										if countercheckside.index(checkside[0]) % 2 == 0:
											timesneg = 1
										newblock[ig] += (0.5*timesneg)
										break
								newblock = [int(newblock[0]),int(newblock[1]),int(newblock[2])]
								
								if not collisionpadding(numpy.array([newblock]),player.x,player.y,player.z):
									checkchunk = (newblock[0]//8,(newblock[2]//8))
									if checkchunk not in world.keys() or tuple(newblock) not in world[checkchunk]:
										place_block([newblock[0],newblock[1],newblock[2],player.blockselection],real=True)
										#light_update((newblock[0]//8,newblock[2]//8))

						elif mousepress[0] == 1:
							"""Check if not Bedrock and below World Height"""
							
							if 0 < int(currentnear[1]):
								remove_block(currentnear,real=True,in_wk=-1)
								#light_update((currentnear[0]//8,currentnear[2]//8))
								
		"""TP BACK TO SPAWN IF OUT OF WORLD"""		
		if player.y < 0:
			for saving in activearray_indices.keys():
				compressed_pickle(str(saving),world[saving])
			player.x,player.z = 0,0
			while (int(player.x//8),int(player.z//8)) not in activearray_indices.keys():
				loadunload_chunks()

			cubes = numpy.concatenate(activearray)
			ystart= cubes[numpy.logical_and(cubes[:,0] == player.x,cubes[:,2] == player.z)]
			del cubes
			try:
				player.y = numpy.max(ystart[:,1:2])+2
			except:
				player.y = 100


		
		"""NULLIFY SCREEN SHAKE WHEN GRAVITY ENABLES"""
		if player.timesince < 0.06:
			model,view = movement(player.x,round(player.y,1),player.z,player.pitch,player.yaw)
		else:
			model,view = movement(player.x,player.y,player.z,player.pitch,player.yaw)
		
		"""TIME CYCLE"""
		if True:
			if sunx >= 255:
				reversepath = -1 
			if sunx <= -255:
				reversepath = 1
			suny = (reversepath*-1)*math.sqrt(abs((255**2)-(sunx**2)))
			#sunx = sunx + (reversepath*0.01)
		
		"""DRAW"""
		drawbuffers(model,view,used_buffers)
		draw2d(menuvisible,display,alltextures[len(alltextures)-2],alltextures[len(alltextures)-1],buttonattributes)
		
		pygame.display.flip()
		clock.tick(vsync)

def run():
	if __name__ == 'test' or __name__ == "__main__":
		global pool,savePool,manager,inQueue,outQueue,saveQueue,loadTicket
		freeze_support()
		manager = Manager()
		inQueue = manager.Queue()
		outQueue = manager.Queue()
		saveQueue = manager.Queue()
		loadTicket = manager.Queue()


		loadThread1 = threading.Thread(target=decompress_pickle,args=(loadTicket,))
		loadThread1.start()
	
		with Pool(max(2,cpu_count())-1) as pool:
			pool.apply_async(loadworld, (inQueue, outQueue))
			with Pool(1) as savePool:
				savePool.apply_async(async_compressed_pickle, (saveQueue, ))
				main()
				loadTicket.put(False)
				while not saveQueue.empty():
					pass

if  __name__ == "__main__":
	run()
