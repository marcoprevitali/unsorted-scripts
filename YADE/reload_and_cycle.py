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
    O.save('temp_ticino_sample_048.yade.gz')
    
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
    if unb<0.001:
			print('Unbalanced force is smaller than 0.01, pausing.')
			Omega.pause()
			set_final_material_properties()
			O.run(1,True)
			O.save('sample_ticino_8x8y3z_phi_048.xml.bz2')
    
O.load('temp_ticino_sample_048.yade.gz')
exportStuffFunction(O) #just4test
O.run()

