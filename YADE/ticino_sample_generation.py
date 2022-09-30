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
    phi = utils.voxelPorosity(end=(8,8,3))
    snf = std(normal_forces)
    ssf = std(shear_forces)
    unb=utils.unbalancedForce()
    
    

    
    
    print('phi: '+str(phi)+', normal force std: '+str(snf)+', shear force std: ' +str(ssf)+' unbalanced force: '+str(unb)+' max accel: '+str(max_accell))
#   effective porosity computation
    plot.addData(t=Omega.time,phi=utils.voxelPorosity(end=(8.,8.,3.)),snf = snf, ssf=ssf,unb=unb,mac = max_accell)
    if unb<0.01:
			print('Unbalanced force is smaller than 0.01, pausing.')
			Omega.pause()
			set_final_material_properties()
       #     O.save('phi_04')

#calculate the porosity std in a set of blocks
def sample_bin_porosity():
    all_phi = []
    num_poro_bins = 10
    for i in range (0,num_poro_bins-1):
        for j in range (0,num_poro_bins-1): #ashtag torrette
            ll=((8./(num_poro_bins)*i),((8./(num_poro_bins)*j)),0)
            ur=((8./(num_poro_bins)*(i+1)),((8./(num_poro_bins)*(j+1))),3)
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

#   material definition: frictional material called Sabbia and Muro
  O.materials.append(FrictMat(young=8.4e10, poisson=0.25, density=2690, frictionAngle=radians(0), label='Muro')) 
  O.materials.append(FrictMat(young=8.4e8, poisson=0.25, density=2690, frictionAngle=radians(0), label='Sabbia_nofric')) #I can't seem to correctly set material properties by using sp.toSimulation so I'm using Sabbia as the default material and manual set wall materials. I'm sorry.

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
    porosity = 0.440    
    box_size = 8.
    box_height = 3.0
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
    #print('Num_particles = ',num_particles)
    

#   sieve size (therefore the maximum and the minimum particle diameter)
    psdDiameters = [0.06, 0.0682324380424000, 0.0710997353998000, 0.0772008664226000, 0.0821178966456000,  0.0864538196182000, 0.0958245796964000, 0.102982122662400, 0.109541196841400, 0.117723291930200, 0.127825231472800, 0.138794027359800, 0.150704065299400, 0.161960789053600, 0.180000000000000]
    
    # [0.1,0.12,0.14,0.16,0.18,0.2,0.22,0.24,0.26,0.28,0.3]   
    psdCumm = [0, 4.11, 8.25, 15.54, 22.838,  30.13,	 38.01, 46.09, 54.57, 61.671, 69.94, 78.42, 88.08, 94.39, 100]       #   maximum and minimum particel size percentage    
    
    num_bins = len(psdDiameters)
    
    
    
    #   boundary generation
    global top, bottom, west, south, east, north
    bottom = O.bodies.append(utils.wall(0,axis=2,material='Muro'))
    south = O.bodies.append(utils.wall(0,axis=1,material='Muro'))
    west = O.bodies.append(utils.wall(0,axis=0,material='Muro'))
    north = O.bodies.append(utils.wall(8.,axis=1,material='Muro'))
    east = O.bodies.append(utils.wall(8.,axis=0,material='Muro'))
    top = O.bodies.append(utils.wall(box_height,axis=2,material='Muro'))
    
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
        sp.makeCloud((0,0,0),(box_size,box_size,box_height),rMean = local_radius/mult,rRelFuzz = 0,num=num_particles)
        
    sp.toSimulation()
    
    print('Total number of particles: '+str(len(O.bodies)-6))
#    print('cumulated number of particles: ',cum_num_particles)

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



