import itasca
itasca.command("python-reset-state false")
from vec import vec3
from vec import vec2
import numpy as np
import math
volume_solids = itasca.fish.get('sum')
def compute_geometry():
    width_equilibrate = itasca.domain_max_x() - itasca.domain_min_x()
    thick_equilibrate = itasca.domain_max_y() - itasca.domain_min_y()
    itasca.fish.set('xmax',itasca.domain_max_x())
    itasca.fish.set('xmin',itasca.domain_min_x())
    itasca.fish.set('ymax',itasca.domain_max_y())
    itasca.fish.set('ymin',itasca.domain_min_y())
    area_to = width_equilibrate * thick_equilibrate
    area_le = thick_equilibrate 
    area_fr = width_equilibrate 
    vol = area_to 
    return area_to, area_le, area_fr, vol, width_equilibrate, thick_equilibrate
    #      0      1        2      3       4        5                  6

width_0  = compute_geometry()[4]
thick_0  = compute_geometry()[5]
tsyy = 0.0    # kPa
phi = 30        # degrees, set to 0 for isotropic
gain_x = 1e-2
gain_y = 1e-2
sr_cap = 999




k_zero = (1.0-math.sin(math.radians(phi)))
k_zero=0.7
ts_horiz = tsyy * k_zero

tsxx = ts_horiz

def compute_stress():
    w = itasca.domain_max_x() - itasca.domain_min_x()
    t = itasca.domain_max_y() - itasca.domain_min_y()
    volume = w*t
    force  = itasca.rblockrblockarray.force_global()
    branch = itasca.rblockrblockarray.branch()
    return np.einsum('ki,kj->ij',force,branch) / (-1.0*volume)
    
    
def servo_iso_stress(*args):
   # global szz
    
    global gain_x
    global xrate
   # global sxx
    
    global gain_y
    global yrate
  #  global syy
    global width_equi
    global thick_equi
    global porosity
    global void_ratio
    global eps_x
    global eps_y
    global eps_vol
    global eps_dev
    global q_stress
    global p_stress
    global matrix
    tsxx = it.fish.get('tsxx')
    tsyy = it.fish.get('tsyy')
    eps_rate_y = it.fish.get('y_compression')
    width_equi  = compute_geometry()[4]
    thick_equi  = compute_geometry()[5]
    tot_vol = width_equi * thick_equi
    porosity = 1 - volume_solids / tot_vol
    void_ratio = tot_vol / volume_solids - 1
    eps_x = ( width_0 - width_equi) / width_0
    eps_y = ( thick_0 - thick_equi)/ thick_0
    eps_vol = eps_x + eps_y 
    eps_dev = 2./3.*(eps_y - eps_x)
    stress = compute_stress()
    sxx = -stress[0,0]
    syy = -stress[1,1]    
  #  print(stress)
    xdiff = tsxx - sxx
    ydiff = tsyy - syy
   # print(xdiff)
    #print(ydiff)
    # print(zdiff)
    # print('----')


    p =  (sxx+syy)/2
    q = syy-sxx
    xrate   = xdiff * gain_x
    xrate = min([abs(xrate),sr_cap]) * np.sign(xrate)

    if  tsxx==tsyy and tsxx ==0:
        matrix = [[0,0],[0,0]]
        set_domain_strain_rate(matrix)   
        print('Not doing anything')
    elif eps_rate_y == 0.0:
        yrate = ydiff * gain_y
        yrate = min([abs(yrate),sr_cap]) * np.sign(yrate)
        matrix = [[xrate,0],[0,yrate]]
        set_domain_strain_rate(matrix)
        print('Stress controlled, xrate:' +str(xrate)+', yrate: '+str(yrate))
    else:
        yrate = eps_rate_y
        matrix2 = [[xrate,0],[0,yrate]]
        set_domain_strain_rate(matrix2)
        print('Stress controlled with prescribed displacement on y')

    itasca.fish.set('sxx',sxx) 
    itasca.fish.set('xrate',xrate) 
    itasca.fish.set('syy',syy) 
    itasca.fish.set('yrate',yrate) 
    itasca.fish.set('thick_equi',thick_equi)
    itasca.fish.set('width_equi',width_equi)
    itasca.fish.set('poro',porosity)
    itasca.fish.set('void_ratio',void_ratio)
    itasca.fish.set('eps_x',eps_x)
    itasca.fish.set('eps_y',eps_y)
    itasca.fish.set('eps_vol',eps_vol)
    itasca.fish.set('p_kPa',p)
    itasca.fish.set('q_kPa',q)
    itasca.fish.set('eta',q/p)
    itasca.fish.set('eps_dev',eps_dev)

def servo_iso_strain(*args):
    xrate = -1.0 
    yrate = -1.0
    matrix = [[xrate,0,],[0,yrate]]
    set_domain_strain_rate(matrix)

def move_boundaries(*args):
    global matrix2
    matrix2 = [[xrate,0],[0,yrate]]
    set_domain_strain_rate(matrix2)
    
def set_domain_strain_rate(myMatrix):
#myMatrix= [[1,0],[0,1]]
    dt = itasca.timestep()
    eps_x = myMatrix[0][0]
    eps_y = myMatrix[1][1]
    x = compute_geometry()[4]
    y = compute_geometry()[5]
    dx = -eps_x*x*dt
    dy = -eps_y*y*dt
   # print(matrix)
  #  dx = min([abs(dx),x/100]) * np.sign(dx)
   # dy = min([abs(dy),y/100]) * np.sign(dy)
    print('Deforming: epsx:' +str(eps_x)+', epsy: '+str(eps_y)+', dx:'+str(dx)+', dy:'+str(dy))
    itasca.set_domain_max([x+dx,y+dy])
    
#itasca.set_callback("move_boundaries", -11.0) 
itasca.set_callback("servo_iso_stress", -11.0)
#itasca.set_callback("servo_tx_strain", -11.0)


