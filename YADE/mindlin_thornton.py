#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## SCRIPT TO TEST A NEW CONSTITUTIVE LAW (MINDLIN - nonlinear elastic model)
from math import *
#import math as ma
## list of engines
# -------------------------------------------------------------------------------------------------
# problem data
# -------------------------------------------------------------------------------------------------
theta = 15.0/180.0*pi
velocity = 0.05
sphere_radius = 100.0e-6
tan_vect = [1.0,0.0,0.0]
# -------------------------------------------------------------------------------------------------


O.engines=[
	ForceResetter(),
	InsertionSortCollider([Bo1_Sphere_Aabb(),Bo1_Box_Aabb()]),
	InteractionLoop(
		[Ig2_Sphere_Sphere_ScGeom(),Ig2_Box_Sphere_ScGeom()],
		[Ip2_FrictMat_FrictMat_MindlinPhys()],
		[Law2_ScGeom_MindlinPhys_Mindlin()]
	),
	NewtonIntegrator(damping=0.0,gravity=(0,0,0)),
	###
	### NOTE this extra engine:
	###
	### You want snapshot to be taken every 1 sec (realTimeLim) or every 50 iterations (iterLim),
	### whichever comes soones. virtTimeLim attribute is unset, hence virtual time period is not taken into account.
	PyRunner(iterPeriod=1,command='myAddPlotData()')
]

## define and append material
mat=FrictMat(young=70e9,poisson=0.3,density=2.65e3,frictionAngle=19.29004622,label='Friction')
O.materials.append(mat)

## create two spheres (one will be fixed) and append them


s0=sphere([0.0,0.0,+sphere_radius],sphere_radius,color=[0,1,0],material='Friction') # verde
s1=sphere([0.0,0.0,-sphere_radius],sphere_radius,color=[0,0,1],material='Friction') # blu
O.bodies.append(s0)
O.bodies.append(s1)

## time step
O.dt=.01*PWaveTimeStep()
O.saveTmp('Mindlin')

from yade import qt
qt.View()
qt.Controller()

############################################
##### now the part pertaining to plots #####
############################################

from yade import plot
## make one plot: step as function of fn
plot.plots={'fn':('fs')}

## this function is called by plotDataCollector
## it should add data with the labels that we will plot
## if a datum is not specified (but exists), it will be NaN and will not be plotted

def myAddPlotData():
	if O.interactions[0,1].isReal:
		i=O.interactions[0,1]
		#O.pause()
		## store some numbers under some labels
		shear_component  = tan_vect[0]*i.phys.shearForce[0]+tan_vect[1]*i.phys.shearForce[1]+tan_vect[2]*i.phys.shearForce[2]
		plot.addData(fn=i.phys.normalForce[0],fs=shear_component,fs0=i.phys.shearForce[0],fs1=i.phys.shearForce[1],step=O.iter,un=2*s0.shape.radius-s1.state.pos[0]+s0.state.pos[0],kn=i.phys.kn)	


vel_n = velocity*cos(theta)
vel_t = velocity*sin(theta)

# top particle initial velocity
O.bodies[0].state.vel[0]= vel_t		 	 # tangential velocity component 
O.bodies[0].state.vel[1]= 0.0			 # out of plane velocity component
O.bodies[0].state.vel[2]= -vel_n		 # normal velocity component


# bottom particle initial velocity
O.bodies[1].state.vel[0]= -vel_t		 # tangential velocity component 
O.bodies[1].state.vel[1]= 0.0			 # out of plane velocity component
O.bodies[1].state.vel[2]= +vel_n		 # normal velocity component


#O.run(200000,True); 
plot.plot(subPlots=False)

## We will have:
## 1) data in graphs (if you call plot.plot())
## 2) data in file (if you call plot.saveGnuplot('/tmp/a')
## 3) data in memory as plot.data['step'], plot.data['fn'], plot.data['un'], etc. under the labels they were saved

