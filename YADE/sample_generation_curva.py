from yade import pack, qt, plot
from math import *
from numpy import *

def exportStuffFunction(Omega):		 #Store the variables	
# -----------------------------------------------------------------------------------------------------------------------
# description: export the time, the kinetic energy and the position along z-axis of the ball
# -----------------------------------------------------------------------------------------------------------------------
# input variables
# - Omega:      object controlling the whole simulation
# -----------------------------------------------------------------------------------------------------------------------
    
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
    phi = utils.voxelPorosity(end=(5.35,5.35,2))
    snf = std(normal_forces)
    ssf = std(shear_forces)
    unb=utils.unbalancedForce()
    
    

    
    
    print('phi: '+str(phi)+', normal force std: '+str(snf)+', shear force std: ' +str(ssf)+' unbalanced force: '+str(unb)+' max accel: '+str(max_accell))
#   effective porosity computation
    plot.addData(t=Omega.time,phi=utils.voxelPorosity(end=(5.35,5.35,2)),snf = snf, ssf=ssf,unb=unb,mac = max_accell)
    if unb<0.01:
			print('Unbalanced force is smaller than 0.01, pausing.')
			Omega.pause()
			set_final_material_properties()
            

#calculate the porosity std in a set of blocks
def sample_bin_porosity():
    all_phi = []
    num_poro_bins = 10
    for i in range (0,num_poro_bins-1):
        for j in range (0,num_poro_bins-1): #ashtag torrette
            ll=((5.35/(num_poro_bins)*i),((5.35/(num_poro_bins)*j)),0)
            ur=((5.35/(num_poro_bins)*(i+1)),((5.35/(num_poro_bins)*(j+1))),2)
            k=1
  #          for k in range(0,num_poro_bins/2-1):
   #             ll=((5.35/(num_poro_bins)*i),((5.35/(num_poro_bins)*j)),((2./(num_poro_bins)*k)))
    #            ur=((5.35/(num_poro_bins)*(i+1)),((5.35/(num_poro_bins)*(j+1))),((2./(num_poro_bins)*(k+1))))
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

#   material definition: frictional material called Sabbia and Muro
  O.materials.append(FrictMat(young=1000e6, poisson=0.25, density=2650, frictionAngle=radians(0), label='Muro')) 
  O.materials.append(FrictMat(young=10e6, poisson=0.25, density=2650, frictionAngle=radians(0), label='Sabbia_nofric')) #I can't seem to correctly set material properties by using sp.toSimulation so I'm using Sabbia as the default material and manual set wall materials. I'm sorry.

# -----------------------------------------------------------------------------------------------------------------------    


def computational_method():
# -----------------------------------------------------------------------------------------------------------------------
# description: definition of the computational strategy
# -----------------------------------------------------------------------------------------------------------------------

#   HOW THE model computes
    O.engines=[
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb(),Bo1_Wall_Aabb()]), 
        InteractionLoop(					
        [Ig2_Wall_Sphere_ScGeom(),Ig2_Sphere_Sphere_ScGeom()], 			
        [Ip2_FrictMat_FrictMat_MindlinPhys(label='interazione')], 
        [Law2_ScGeom_MindlinPhys_Mindlin(label='myViscoElasticLaw')]),
        NewtonIntegrator(damping=0.3,gravity=(0,0,0),label='NI'), #setting no gravity for the first iterations, following Ciantia's PCRM paper
        PyRunner(command='exportStuffFunction(O)',iterPeriod=5000),
        #PyRunner(command='sample_bin_porosity()',iterPeriod=10000),
        GlobalStiffnessTimeStepper()
        ]

    global rr
#   rendering generation
    rr = yade.qt.Renderer()
    rr.shape = False
    
#   contact showing 
    rr.intrPhys=True

#   record the numerical results
    plot.plots={'t':('phi','phistd',None,'ssf','snf',None,'unb',None,'mac')} #Phi: porosity, Sigma: Standard Deviation in contact force
#   diagram the numerical results
 #   plot.plot()


# -----------------------------------------------------------------------------------------------------------------------
    

def model_generation():
# -----------------------------------------------------------------------------------------------------------------------
# description: generation of the sample
# -----------------------------------------------------------------------------------------------------------------------

#   minimu,maximum particle diameter 
#   units [m]
    min_diameter = 0.2
    max_diameter = 0.2
    porosity = 0.40    
    box_size = 5.35
    box_height = 2.0
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
    sample_volume = box_height*box_size**2.0
    solid_volume = sample_volume/(1.0+void_ratio)
    particle_volume = 4.0/3.0*pi*(mean_radius)**3.0
    num_particles = int(solid_volume/particle_volume)
    print('Num_particles = ',num_particles)
    

#   sieve size (therefore the maximum and the minimum particle diameter)
    psdSizes = [0.1,0.12,0.14,0.16,0.18,0.2,0.22,0.24,0.26,0.28,0.3]   
    psdCumm = [0.,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.]       #   maximum and minimum particel size percentage    
    num_bins = len(psdSizes)
    
    
    
    #   boundary generation
    global top, bottom, west, south, east, north
    bottom = O.bodies.append(utils.wall(0,axis=2,material='Muro'))
    south = O.bodies.append(utils.wall(0,axis=1,material='Muro'))
    west = O.bodies.append(utils.wall(0,axis=0,material='Muro'))
    north = O.bodies.append(utils.wall(5.35,axis=1,material='Muro'))
    east = O.bodies.append(utils.wall(5.35,axis=0,material='Muro'))
    top = O.bodies.append(utils.wall(box_height,axis=2,material='Muro'))
    
    sp = pack.SpherePack()

    for bin_idx in range (0,num_bins-1):
        inverse_idx = (num_bins-2)-bin_idx
        print(inverse_idx)
        local_radius = (psdSizes[inverse_idx+1]+psdSizes[inverse_idx])/(4.*2) #should be 4 but i want 2x times smaller particles
        local_volume = 4.0/3.0*pi*local_radius**3.0
        target_volume = solid_volume*(psdCumm[inverse_idx+1]-psdCumm[inverse_idx])
        num_particles = int(target_volume/local_volume)
        sp.makeCloud((0,0,0),(box_size,box_size,box_height),rMean = local_radius/mult,rRelFuzz = 0,num=num_particles)
        print(num_particles)
    sp.toSimulation()
    
    print('Num. particles added: '+str(len(O.bodies)))

#   timestep setting
    O.dt = 0.05*utils.PWaveTimeStep() 	

def expand_particles():    
#   expansion cycles
    
    for i in range(0,num_expansion):
        utils.growParticles(multiplier=mult_fact,updateMass=True) #I'm afraid scaling the particles does not change mass. apparently this kills walls? whyyyy
    #    for particle in O.bodies:
      #      if isinstance(particle.shape,Sphere):   # cicla solo sulle sfere
     #           particle.shape.radius*=mult_fact
      #          particle.state.mass = (4./3*pi*particle.shape.radius**3)*particle.mat.density
                
        O.run(500,True)
        print('-----------------------')
        print('iterazione: ' +str(i)+', dt: '+str(O.dt))
        
    
    
    
#   rotation locking
    for particle in O.bodies:
        if isinstance(particle.shape,Sphere):
            particle.state.blockedDOFs='XYZ'

    
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
    finalSandMat = FrictMat(young=10e6, poisson=0.25, density=2650, frictionAngle=radians(11.3), label='Sabbia') 
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
    model_generation()
    expand_particles()
    plot.plot()
    NI.gravity = ((0,0,-9.81))
    O.run()
   # O.run(100000,True)
      #O.run(10000,True)
   # particle_settlement()
   # particle_compression()
  #  O.run()
# -----------------------------------------------------------------------------------------------------------------------	   

main()



