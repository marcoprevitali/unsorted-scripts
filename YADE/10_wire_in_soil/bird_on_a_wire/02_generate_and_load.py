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
import numpy as np
box_length = 6.0;
box_width = 2.0;
box_height = 1.0;
wire_thickness = 0.05;

def exportStuffFunction():		 #Store the variables	
# -----------------------------------------------------------------------------------------------------------------------
# description: export the time, the kinetic energy and the position along z-axis of the ball
# -----------------------------------------------------------------------------------------------------------------------
# input variables
# - Omega:      object controlling the whole simulation
# -----------------------------------------------------------------------------------------------------------------------
    Omega = O
    # calculate all the interaction forces
    normal_forces = []
    shear_forces = []
    for i in Omega.interactions:
        if i.isReal:
            fn = i.phys.normalForce
            fs = i.phys.shearForce
            normal_forces.append(fn)
            shear_forces.append(fs)
    
    #--------------------------------------
    # Calculate particle acceleration
    #--------------------------------------
    max_accell=0
    for particle in Omega.bodies:      
        if isinstance(particle.shape,Sphere):
            massa = particle.state.mass
            forza = Omega.forces.f(particle.id)
            forza_gravity = -massa*9.81
            forza_somma = (forza[0],forza[1],forza[2]+forza_gravity)
            modulo_unbalanced = (forza[0]**2+forza[1]**2+forza[2]**2)**0.5
            accell = modulo_unbalanced/massa
            max_accell=max(max_accell,accell)
    phi = utils.voxelPorosity(end=(box_length,box_width,box_height))
    snf = std(normal_forces)
    ssf = std(shear_forces)
    unb=utils.unbalancedForce()
    
    

    
    
    print('phi: '+str(phi)+', normal force std: '+str(snf)+', shear force std: ' +str(ssf)+' unbalanced force: '+str(unb)+' max accel: '+str(max_accell))
#   effective porosity computation
    plot.addData(t=Omega.time,phi=utils.voxelPorosity(end=(box_length,box_width,box_height)),snf = snf, ssf=ssf,unb=unb,mac = max_accell)
    if unb<0.001:
        print('Unbalanced force is smaller than 0.01, pausing.')
        Omega.pause()
        set_final_material_properties()
        O.run(1,True)
        O.save('mySample.xml.bz2')

#calculate the porosity std in a set of blocks
def sample_bin_porosity():
    all_phi = []
    num_poro_bins = 10
    for i in range (0,num_poro_bins-1):
        for j in range (0,num_poro_bins-1): #ashtag torrette
            ll=((box_width/(num_poro_bins)*i),((box_width/(num_poro_bins)*j)),0)
            ur=((box_length/(num_poro_bins)*(i+1)),((box_length/(num_poro_bins)*(j+1))),box_height)
            k=1
  #          for k in range(0,num_poro_bins/2-1):
   #             ll=((8./(num_poro_bins)*i),((8./(num_poro_bins)*j)),((2./(num_poro_bins)*k)))
    #            ur=((8./(num_poro_bins)*(i+1)),((8./(num_poro_bins)*(j+1))),((2./(num_poro_bins)*(k+1))))
            local_poro = utils.voxelPorosity(start=ll,end=ur)
            #print('Bin ('+str(i)+','+str(j)+','+str(k)+'), phi:' + str(local_poro))
            all_phi.append(local_poro)
    phi_std = std(all_phi) 
    print('Phi std: '+str(phi_std))
    print('-------------------------------')
    plot.addData(phistd=phi_std)

# -----------------------------------------------------------------------------------------------------------------------		


def material_definition():
# -----------------------------------------------------------------------------------------------------------------------
    # description: definition of the materials
    # -----------------------------------------------------------------------------------------------------------------------    
    O.materials.append(FrictMat(young=1e9,poisson=0.5,frictionAngle=.4,density=2700,label='spheremat'))
    O.materials.append(FrictMat(young=1.0e9,poisson=0.2,density=2.60e3,frictionAngle=.4,label='walllmat'))


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
		Bo1_Box_Aabb(),
		Bo1_Wall_Aabb()
    ]),
    InteractionLoop(
        [Ig2_ChainedCylinder_ChainedCylinder_ScGeom6D(), Ig2_Sphere_ChainedCylinder_CylScGeom(), Ig2_Sphere_Sphere_ScGeom(),Ig2_Box_Sphere_ScGeom(),Ig2_Wall_Sphere_ScGeom()],			
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
# -----------------------------------------------------------------------------------------------------------------------
def generate_string():

    nL=100
    L=box_width
    rCyl = wire_thickness/2

    ### Create all nodes first :
    for i in linspace(0,L,nL):
        b=chainedCylinder(begin=Vector3(box_length/2,i,box_height/2), radius=rCyl,end=Vector3(box_length/2,i+L/nL,box_height/2),color=Vector3(0.6,0.5,0.5),material='cylindermat')
        myWireInteractions.append(b)
        if i == 0 or i == L:
            b.state.blockedDOFs='xyz'
            b.shape.color=[0,0,1]
    O.bodies[0].state.blockedDOFs='xyz'
    O.bodies[0].shape.color=[0,0,1]
    O.bodies[-1].state.blockedDOFs='xyz'
    O.bodies[-1].shape.color=[0,0,1]
            
def model_generation():
# -----------------------------------------------------------------------------------------------------------------------
# description: generation of the sample
# -----------------------------------------------------------------------------------------------------------------------

#   minimu,maximum particle diameter 
#   units [m]
    min_diameter = 0.2
    max_diameter = 0.2
    porosity = 0.48    
    global num_expansion
    global mult
    num_expansion = 50
    mult = 1.6
    
    
#   mult factor for particle upscaling
    global mult_fact
    mult_fact = mult**(1./num_expansion) 
    
#   mean value of the particle radius and its deviation in percentage
    mean_radius = 0.25*(min_diameter+max_diameter)
    dev_radius = (max_diameter-min_diameter)/(4.0*mean_radius)  #0.50
    
    
#   computatation of the solid volume
    void_ratio = porosity/(1.0-porosity)
    sample_volume = box_height*box_length*box_width
    solid_volume = sample_volume/(1.0+void_ratio)
    particle_volume = 4.0/3.0*pi*(mean_radius)**3.0
    num_particles = int(solid_volume/particle_volume)
    #print('Num_particles = ',num_particles)
    

#   sieve size (therefore the maximum and the minimum particle diameter)
    psdDiameters = [0.06, 0.0682324380424000, 0.0710997353998000, 0.0772008664226000, 0.0821178966456000,  0.0864538196182000, 0.0958245796964000, 0.102982122662400, 0.109541196841400, 0.117723291930200, 0.127825231472800, 0.138794027359800, 0.150704065299400, 0.161960789053600, 0.180000000000000]
    
    # [0.1,0.12,0.14,0.16,0.18,0.2,0.22,0.24,0.26,0.28,0.3]   
    psdCumm = [0, 4.11, 8.25, 15.54, 22.838,  30.13,	 38.01, 46.09, 54.57, 61.671, 69.94, 78.42, 88.08, 94.39, 100]       #   maximum and minimum particel size percentage    
    
    num_bins = len(psdDiameters)
    
    
    

    
   
	

        #   boundary generation
    global top, bottom, west, south, east, north
    bottom = O.bodies.append(utils.wall(0,axis=2,material='walllmat'))
    south = O.bodies.append(utils.wall(0,axis=1,material='walllmat'))
    west = O.bodies.append(utils.wall(0,axis=0,material='walllmat'))
    north = O.bodies.append(utils.wall(box_width,axis=1,material='walllmat'))
    east = O.bodies.append(utils.wall(box_length,axis=0,material='walllmat'))
    top = O.bodies.append(utils.wall(box_height,axis=2,material='walllmat'))
    
    
    sp = pack.SpherePack()

    cum_num_particles = 0.0
    for bin_idx in range (0,num_bins-1):
        inverse_idx = (num_bins-2)-bin_idx
        local_radius = (psdDiameters[inverse_idx+1]+psdDiameters[inverse_idx])/(4.) 
        local_sphere_volume = 4.0/3.0*pi*local_radius**3.0
        target_volume = 1e-2*solid_volume*(psdCumm[inverse_idx+1]-psdCumm[inverse_idx])
        num_particles = int(target_volume/local_sphere_volume)
        cum_num_particles += num_particles
       
        print('Bin: '+str(bin_idx)+', from d: '+str(psdDiameters[inverse_idx])+' [m] to d: '+str(psdDiameters[inverse_idx+1])+' [m], from vol_perc: '+str(psdCumm[inverse_idx])+' [-] to vol_perc: '+str(psdCumm[inverse_idx+1])+' [-], target volume: '+str(target_volume)+' [m3],  num. particles: '+str(num_particles))
        sp.makeCloud((0,0,0),(box_length,box_width,box_height),rMean = local_radius/mult,rRelFuzz = 0,num=num_particles)
        
    sp.toSimulation(color=[.3,.3,.3],material='spheremat')
    
    print('Total number of particles: '+str(len(O.bodies)-6))
#    print('cumulated number of particles: ',cum_num_particles)

#   timestep setting
    O.dt = 0.05*utils.PWaveTimeStep() 	

def expand_particles():    
#   expansion cycles
    for i in range(0,num_expansion):
        utils.growParticles(multiplier=mult_fact,updateMass=True)
    #    for particle in O.bodies:
      #      if isinstance(particle.shape,Sphere):   # cicla solo sulle sfere
     #           particle.shape.radius*=mult_fact
      #          particle.state.mass = (4./3*pi*particle.shape.radius**3)*particle.mat.density
                
        O.run(500,True)
        print('-----------------------')
        print('iterazione: ' +str(i)+', dt: '+str(O.dt))
        
    
    #   rotation locking
   # for particle in O.bodies:
   #     if isinstance(particle.shape,Sphere):
   #         particle.state.blockedDOFs='XYZ'
   #         particle.state.color = [0.1,0.7,0.1]
    #nodesIds[0]

    

# -----------------------------------------------------------------------------------------------------------------------	

    
    
# -----------------------------------------------------------------------------------------------------------------------	    

def particle_settlement():
# -----------------------------------------------------------------------------------------------------------------------
# description: settling phase
# -----------------------------------------------------------------------------------------------------------------------    
#   simulation running
    
    O.run(10000,True)

#   deleting particles outside boundaries
  #  for i in range(0,len(O.bodies)-1):
#	if O.bodies[i].state.pos[2]>2:
		#O.bodies.erase(i)
		
    #O.bodies.erase(tappo)
# -----------------------------------------------------------------------------------------------------------------------	        

def particle_compression():
	O.engines+=[PyRunner(command='compressSand()',iterPeriod=50)]
	O.engines[4].dead=True
	O.run(True)

def set_final_material_properties():
    finalSandMat = FrictMat(young=8.4e8, poisson=0.25, density=2690, frictionAngle=0.325, label='Sabbia') 
    pairs=[(i.id1,i.id2) for i in O.interactions]
    for b in O.bodies:b.mat=finalSandMat
    O.interactions.clear()
    for id1,id2 in pairs:utils.createInteraction(id1,id2)


def main():
# -----------------------------------------------------------------------------------------------------------------------	   
# description: main rountine
# -----------------------------------------------------------------------------------------------------------------------	        
    material_definition()   # material definition
    computational_method()    # physic definition before starting the model generation    
    generate_string()
    newton.gravity = ((0,0,-9.81))
    O.run(1000000,True)
    
    newton.gravity = ((0,0,0))
    model_generation()
    expand_particles()
 #   plot.plot()
    newton.gravity = ((0,0,-9.81))
    O.engines+=[PyRunner(command='exportStuffFunction()',iterPeriod=1000)]

    O.run(10000,True)
    for particle in O.bodies:
        if isinstance(particle.shape,Sphere):
            particle.shape.Wire = True
      #O.run(10000,True)
   # particle_settlement()
   # particle_compression()
  #  O.run()
# -----------------------------------------------------------------------------------------------------------------------	   

main()
vel = 2.0
fname_nodes = 'nodes.txt'
fname_conns = 'connections.txt'
fname_balls = 'balls.txt'
fname_conns_wire ='wire.txt'
fid_nodes = open(fname_nodes,'w')
fid_conns = open(fname_conns,'w')
fid_balls = open(fname_balls,'w')
fid_conns_wire=open(fname_conns_wire,'w')

myWireConnections = []
myWireNodes = []
myWalls = []
for b in O.bodies:
    if isinstance(b.shape, ChainedCylinder ):
        myWireNodes.append(b)
    elif isinstance(b.shape,Wall):
        myWalls.append(b)

topWall = myWalls[5]
leftWall = myWalls[2]
rightWall = myWalls[4]

leftWall.state.vel = [vel,0,0]
rightWall.state.vel = [vel,0,0]
O.bodies.erase(topWall.id)

fid_nodes.write('time,id,x,y,z,vx,vy,vz\n')
fid_conns.write('time,id1,id2,x,y,z,momentBendX,momentBendY,momentBendZ,momentTwistX,momentTwistY,momentTwistZ,normalForceX,normalForceY,normalForceZ,shearForceX,shearForceY,shearForceZ\n')
fid_balls.write('time,id,radius,x,y,z,vx,vy,vz,spinx,spiny,spinz\n')
fid_conns_wire.write('time,id0,id1,id2,x,y,z,momentBendX,momentBendY,momentBendZ,momentTwistX,momentTwistY,momentTwistZ,normalForceX,normalForceY,normalForceZ,shearForceX,shearForceY,shearForceZ\n')

def exportDataStep():
    t = O.time
    print('Exporting stuff..')
    for b in myWireNodes:   
        p = b.state.pos
        v = b.state.vel
        a = b.state.angMom
        i = b.id
        fid_nodes.write(str(t)+','+str(i)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(v[0])+','+str(v[1])+','+str(v[2])+','+str(a[0])+','+str(a[1])+','+str(a[2])+'\n')
    for ccc in O.interactions:
        mb = [0,0,0]
        mt = [0,0,0]
        if isinstance(ccc,FrictPhys):
            mb = ccc.phys.momentBend
            mt = ccc.phys.momentTwist
        p = ccc.geom.contactPoint
        nf = ccc.phys.normalForce
        sf = ccc.phys.shearForce
        id1 = ccc.id1
        id2 = ccc.id2
        fid_conns.write(str(t)+','+str(id1)+','+str(id2)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(mb[0])+','+str(mb[1])+','+str(mb[2])+','+str(mt[0])+','+str(mt[1])+','+str(mt[2])+','+str(nf[0])+','+str(nf[1])+','+str(nf[2])+','+str(sf[0])+','+str(sf[1])+','+str(sf[2])+'\n')
    for ccc in myWireInteractions:
        p = ccc.state.pos
        myInt = ccc.intrs()
        id0 = ccc.id
        mb = np.array([0,0,0])
        mt = np.array([0,0,0])
        nf = np.array([0,0,0])
        sf = np.array([0,0,0])
        for c in myInt:
            if not isinstance(c.phys,FrictPhys):
                mb += np.array(c.phys.moment_bending)
                mt += np.array(c.phys.moment_twist)
            if isinstance(c.phys,FrictPhys):
                sf = sf+np.array(c.phys.shearForce)
                nf = nf+np.array(c.phys.normalForce)
            id1 = c.id1
            id2 = c.id2
        #print(nf)
        fid_conns_wire.write(str(t)+','+str(id0)+','+str(id1)+','+str(id2)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(mb[0])+','+str(mb[1])+','+str(mb[2])+','+str(mt[0])+','+str(mt[1])+','+str(mt[2])+','+str(nf[0])+','+str(nf[1])+','+str(nf[2])+','+str(sf[0])+','+str(sf[1])+','+str(sf[2])+'\n')
    for b in O.bodies:
        if isinstance(b.shape,Sphere):
            p = b.state.pos
            v = b.state.vel
            s = b.state.angMom
            r = b.shape.radius
            idd = b.id
            fid_balls.write(str(t)+','+str(idd)+','+str(r)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(v[0])+','+str(v[1])+','+str(v[2])+','+str(s[0])+','+str(s[1])+','+str(s[2])+'\n')

O.engines[-1].dead = True    
O.engines+=[PyRunner(command='exportDataStep()',iterPeriod=1000)]

O.run(500000)

#fid_nodes.close()
#fid_balls.close()
#fid_conns.close()
print('Done')
