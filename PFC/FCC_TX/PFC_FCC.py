import math
import itasca as it
import numpy as np


radius = 0.5     
num_cells = 6   
young = 1e6    
shear = 1e6      
density = 1.0    
target_mean_stress = 100
vec_friction = [0.1, 0.2, 0.3, 0.4, 0.5]
out_freq = 500
I = 1e-5
eps_zz_dot = - I/(2*radius*(density/target_mean_stress)**0.5)

# servo control to target pressure
gain_z = 1.0e-2
tszz = -target_mean_stress
gain_x = 1.0e-2
tsxx = -target_mean_stress
gain_y = 1.0e-2
tsyy =  -target_mean_stress
rate_max = 1.0e-2



# generate the FCC
a = 2.0 * np.sqrt(2.0) * radius # lattice constant a = 2sqrt(2) *R
basis = [  (0.0, 0.0, 0.0),
    (0.5*a, 0.5*a, 0.0),
    (0.5*a, 0.0, 0.5*a),
    (0.0, 0.5*a, 0.5*a)]
sphere_positions = []
for ix in range(num_cells):
    for iy in range(num_cells):
        for iz in range(num_cells):
            for dx, dy, dz in basis:
                x = (ix + dx/a) * a
                y = (iy + dy/a) * a
                z = (iz + dz/a) * a
                sphere_positions.append((x, y, z))

Lx = a * num_cells
Ly = a * num_cells
Lz = a * num_cells





def compute_stress():
  h = it.domain_max_z() - it.domain_min_z()
  w = it.domain_max_x() - it.domain_min_x()
  t = it.domain_max_y() - it.domain_min_y()
  volume = h*w*t
  force  = it.ballballarray.force_global()
  branch = it.ballballarray.branch()
  return np.einsum('ki,kj->ij',force,branch) / (-1.0*volume)


def servo_iso_stress():
    global tszz
    global gain_z
    global tsxx
    global gain_x
    global tsyy
    global gain_y
    global rate_max
    stress = compute_stress()
    sxx = stress[0,0]
    syy = stress[1,1]
    szz = stress[2,2]

    xdiff = tsxx - sxx
    ydiff = tsyy - syy
    zdiff = tszz - szz 

    xrate   = xdiff * gain_x
    yrate   = ydiff * gain_y
    zrate   = zdiff * gain_z

    xrate = min([abs(xrate),rate_max]) * np.sign(xrate)
    yrate = min([abs(yrate),rate_max]) * np.sign(yrate)
    zrate = min([abs(zrate),rate_max]) * np.sign(zrate)
    matrix = [[xrate,0,0],[0,yrate,0],[0,0,zrate]]
    it.set_domain_strain_rate(matrix)
 #   print(stress)
    
def servo_TX():
    global eps_zz_dot
    global tsxx
    global gain_x
    global tsyy
    global gain_y
    global rate_max
    stress = compute_stress()
    sxx = stress[0,0]
    syy = stress[1,1]
    szz = stress[2,2]

    xdiff = tsxx - sxx
    ydiff = tsyy - syy
    zdiff = tszz - szz 

    xrate   = xdiff * gain_x
    yrate   = ydiff * gain_y
    zrate   = eps_zz_dot

    xrate = min([abs(xrate),rate_max]) * np.sign(xrate)
    yrate = min([abs(yrate),rate_max]) * np.sign(yrate)
    zrate = min([abs(zrate),rate_max]) * np.sign(zrate)
    matrix = [[xrate,0,0],[0,yrate,0],[0,0,zrate]]
    it.set_domain_strain_rate(matrix)
    #print(stress)

def generateOutput():    
    global t0
    global eps_zz_dot
    global out_freq
    t = it.mech_age()-t0
    stress = compute_stress()
    eps_ax = -t * eps_zz_dot
    coord = 2.0 * it.contact.count()/it.ball.count()
    myLine = '%e,%e,%e,%e,%e,%e\n' % (t,stress[0][0],stress[1][1],stress[2][2],eps_ax,coord)
    fid_out_full.write(myLine)
    if (it.cycle()%out_freq==0):
        fid_out.write(myLine)
    

for friction in vec_friction:

    it.command("python-reset-state false")
    it.command("model new")



    it.set_domain_max([Lx,Ly,Lz])
    it.set_domain_condition('x','periodic')
    it.set_domain_condition('y','periodic')
    it.set_domain_condition('z','periodic')

    for pos in sphere_positions:
        it.ball.create(radius,pos)


    it.command("contact cmat default model linear property kn "+str(young)+" ks "+str(shear)+" fric "+str(friction))


    it.command("ball attribute dens "+str(density)+" damp 0.7 ")
    it.command("ball fix spin")     


    it.set_callback("servo_iso_stress", -1.0) #honestly i dont think there is any difference between -1 (before the cycle start) and 100 (after the end of the cycle)
    it.command("model large-strain on")
    it.command("model mechanical timestep fix 1e-5") #fix to have equally distributed results

    # cycle to target stress
    it.command("cycle 1000")
    
    # start triaxial
    it.remove_callback("servo_iso_stress", -1.0)
    it.set_callback("servo_TX", -1.0)
    

    
    fid_out = open('PFC-FCC-fric-'+str(friction)+'.csv','w')
    fid_out_full = open('PFC-FCC-FULL-fric-'+str(friction)+'.csv','w')
    t0 = it.mech_age()
    it.set_callback("generateOutput",100)
    coord = 2.0 * it.contact.count()/it.ball.count()
    stress = compute_stress()
    
    header = 'time,sxx,syy,szz,eps_zz,CN\n'
    fid_out.write(header)
    fid_out_full.write(header)
    
    myLine = '%e,%e,%e,%e,%e,%e\n' % (0.0,stress[0][0],stress[1][1],stress[2][2],0.0,coord)
    fid_out.write(myLine)
    fid_out_full.write(myLine)
    
    it.command("cycle 1000000")

    fid_out.close()
    fid_out_full.close()
