from yade import pack, qt, plot
from math import *
from numpy import *

d50 = 0.06
theta = 45.0/180.0*pi
velocity = 0.05


O.dt = 1e-9

young_mod = 4.2e5*1e3  # moltiplicato per 1000 per tenere conto dell'equivalenza 
ks = 0.0

sandMat = FrictMat(young=young_mod, poisson=0.25, density=2690, frictionAngle=0.325, label='Sand') 

b1 = O.bodies.append(utils.sphere((0,0,d50/2),radius=d50/2,material=sandMat))
b2 = O.bodies.append(utils.sphere((0,0,-d50/2),radius=d50/2,material=sandMat))
                     
O.engines=[
    ForceResetter(), 
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(							
        [Ig2_Sphere_Sphere_ScGeom()], 			
        [Ip2_FrictMat_FrictMat_FrictPhys()], 	
        [Law2_ScGeom_FrictPhys_CundallStrack()]),
        NewtonIntegrator(damping=0.0,gravity=(0,0,0)),
        PyRunner(command='AddPlotData()',iterPeriod=1)	
        ]
    

plot.plots={'displ':('fn','fs')} 

for b in O.bodies:
    b.state.blockedDOFs='xyzXYZ'

def AddPlotData():
	if O.interactions[0,1].isReal:
		i=O.interactions[0,1]
		tan_vect = [1.0,0.0,0.0]
		#shear_component  = tan_vect[0]*i.phys.shearForce[0]+tan_vect[1]*i.phys.shearForce[1]+tan_vect[2]*i.phys.shearForce[2]
		#normal_comonent = i.phys.normalForce[0]
        normal_component = (i.phys.normalForce[0]**2+i.phys.normalForce[1]**2+i.phys.normalForce[2]**2)**0.5
        shear_component = (i.phys.shearForce[0]**2+i.phys.shearForce[1]**2+i.phys.shearForce[2]**2)**0.5
        disp = O.bodies[0].state.displ()
        plot.addData(displ = disp[2], fn=normal_component,fs=shear_component)	
        

vel_n = velocity*cos(theta)
vel_t = velocity*sin(theta)

# top particle initial velocity
O.bodies[0].state.vel[0]= vel_t		 	 # tangential velocity component 
O.bodies[0].state.vel[1]= 0.0			 # out of plane velocity component
O.bodies[0].state.vel[2]= -vel_n		 # normal velocity component


# bottom particle initial velocity
#O.bodies[1].state.vel[0]= -vel_t		 # tangential velocity component 
#O.bodies[1].state.vel[1]= 0.0			 # out of plane velocity component
#O.bodies[1].state.vel[2]= +vel_n		 # normal velocity component


O.run(10000,True)
plot.plot()
plot.saveDataTxt('yade_force_data.txt')
a = O.interactions[0,1]
print(a.phys.normalForce)
print(a.phys.shearForce)
