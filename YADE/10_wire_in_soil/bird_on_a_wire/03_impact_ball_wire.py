from builtins import range
from builtins import zip
from yade import pack,geom,qt
from yade.gridpfacet import *
from pylab import *
import bisect as bi
from yade import export,polyhedra_utils
from yade import pack, qt, plot
from math import *
from numpy import *

box_length = 4.0;
box_width = 2.0;
box_height = 1.0;
wire_thickness = 0.05;

def material_definition():
# -----------------------------------------------------------------------------------------------------------------------
    # description: definition of the materials
    # -----------------------------------------------------------------------------------------------------------------------    

    O.materials.append(CohFrictMat(young=8e5,poisson=0.3,density=4e3,frictionAngle=radians(30),normalCohesion=1e9,shearCohesion=1e9,momentRotationLaw=True,label='gridNodeMat'))

    O.materials.append(CohFrictMat(young=8e5,poisson=0.3,density=4e3,frictionAngle=radians(30),normalCohesion=1e9,shearCohesion=1e9,momentRotationLaw=True,label='gridCoMat'))

    O.materials.append(CohFrictMat(young=8e5,poisson=0.3,density=4e3,frictionAngle=radians(30),normalCohesion=4e4,shearCohesion=1e9,momentRotationLaw=False,label='spheremat'))
    
    #   material definition: frictional material called Sabbia and Muro
    O.materials.append(FrictMat(young=8.4e10, poisson=0.25, density=2690, frictionAngle=radians(0), label='Muro')) 
    O.materials.append(FrictMat(young=8.4e8, poisson=0.25, density=2690, frictionAngle=radians(0), label='Sabbia_nofric')) #I can't seem to correctly set material properties by using sp.toSimulation so I'm using Sabbia as the default material and manual set wall materials. I'm sorry.
    O.materials.append(FrictMat(young=4000000.0,poisson=0.5,frictionAngle=.4,density=1600,label='spheremat'))
    O.materials.append(FrictMat(young=1.0e6,poisson=0.2,density=2.60e3,frictionAngle=.4,label='walllmat'))

  #  O.materials.append(CohFrictMat(young=8e5,poisson=0.3,density=4e3,frictionAngle=radians(30),normalCohesion=1,shearCohesion=1,momentRotationLaw=False,label='Sabbia_nofric'))
#    O.materials.append(CohFrictMat(young=1e9,poisson=0.3,density=4e3,frictionAngle=radians(30),normalCohesion=1e12,shearCohesion=1e12,momentRotationLaw=True,label='gridNodeMat'))
#    O.materials.append(CohFrictMat(young=1e9,poisson=0.3,density=4e3,frictionAngle=0,normalCohesion=1e40,shearCohesion=1e40,momentRotationLaw=True,label='cylindermat'))
    # -----------------------------------------------------------------------------------------------------------------------    


def computational_method():
# -----------------------------------------------------------------------------------------------------------------------
# description: definition of the computational strategy
# -----------------------------------------------------------------------------------------------------------------------


    ### Engines need to be defined first since the function gridConnection creates the interaction
    O.engines=[
    ForceResetter(),
    InsertionSortCollider([
		Bo1_ChainedCylinder_Aabb(),
		Bo1_Sphere_Aabb(),
		Bo1_Box_Aabb()
    ]),
    InteractionLoop(
        [Ig2_ChainedCylinder_ChainedCylinder_ScGeom6D(), Ig2_Sphere_ChainedCylinder_CylScGeom(), Ig2_Sphere_Sphere_ScGeom(),Ig2_Box_Sphere_ScGeom()],			
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(setCohesionNow=True,setCohesionOnNewContacts=False,label='ipf'),Ip2_FrictMat_FrictMat_FrictPhys()],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment(label='law'),Law2_ScGeom_FrictPhys_CundallStrack(),Law2_CylScGeom_FrictPhys_CundallStrack()]
    ),
    NewtonIntegrator(gravity=(0,0,0),damping=0.3,label='newton'),
    ]


    O.materials.append(CohFrictMat(young=8e5,poisson=0.3,density=4000,frictionAngle=.3,normalCohesion=1e40,shearCohesion=1e40,momentRotationLaw=True,label='cylindermat'))





    global rr
#   rendering generation
 #   rr = yade.qt.Renderer()
 #   rr.shape = False
    
#   contact showing 
 #   rr.intrPhys=True

#   record the numerical results
    plot.plots={'t':('phi','phistd',None,'ssf','snf',None,'unb',None,'mac')} #Phi: porosity, Sigma: Standard Deviation in contact force
#   diagram the numerical results
 #   plot.plot()
myWireInteractions = []
nodesIds = []
# -----------------------------------------------------------------------------------------------------------------------
def generate_string():

    nL=30
    L=box_width
    rCyl = wire_thickness/2

    ### Create all nodes first :
    global nodesIds
    for i in linspace(0,L,nL):
        b=chainedCylinder(begin=Vector3(box_length/2,i,box_height/2), radius=rCyl,end=Vector3(box_length/2,i+L/nL,box_height/2),color=Vector3(0.6,0.5,0.5),material='cylindermat')
        if i == 0 or i == L:
            b.state.blockedDOFs='xyz'
            b.shape.color=[0,0,1]
   
    
def model_generation():
    s = sphere((box_length/2,box_width/2,box_height/3),radius = 0.05,wire=False,fixed=False,material='spheremat')
    s.state.vel = [0,0,10]
    O.bodies.append(s)
    s = sphere((box_length/2,box_width/2,box_height/6),radius = 0.05,wire=False,fixed=False,material='spheremat')
    s.state.vel = [0,0,10]
    O.bodies.append(s)

def main():
# -----------------------------------------------------------------------------------------------------------------------	   
# description: main rountine
# -----------------------------------------------------------------------------------------------------------------------	        
    material_definition()   # material definition
    computational_method()    # physic definition before starting the model generation    
    generate_string()
    model_generation()
    newton.gravity = ((0,0,-9.81))


    #O.run(10000,True)
    

      #O.run(10000,True)
   # particle_settlement()
   # particle_compression()
  #  O.run()
# -----------------------------------------------------------------------------------------------------------------------	   

main()
