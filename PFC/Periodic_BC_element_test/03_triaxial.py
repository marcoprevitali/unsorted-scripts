import itasca
itasca.command("python-reset-state false")
from vec import vec3
from vec import vec2
import numpy as np
import math
filename = 'temp_50kPa_phi_30'
import itasca
itasca.command("model restore '"+filename+".sav'")

itasca.remove_callback("servo_iso_stress", -11.0)
#########################################################
height_0 = compute_geometry()[0]
width_0  = compute_geometry()[5]
thick_0  = compute_geometry()[6]


def servo_tx_strain(*args):
    global tszz
    global szz
    global zrate
    global tsxx
    global gain_x
    global xrate
    global sxx
    global tsyy
    global gain_y
    global yrate
    global syy
    global height_equi
    global width_equi
    global thick_equi
    global porosity
    global void_ratio
    global eps_z
    global eps_x
    global eps_y
    global eps_vol
    global eps_dev
    global q_stress
    global p_stress
    global matrix2
    height_equi = compute_geometry()[0]
    width_equi  = compute_geometry()[5]
    thick_equi  = compute_geometry()[6]
    tot_vol = height_equi * width_equi * thick_equi
    porosity = 1 - volume_solids / tot_vol
    void_ratio = tot_vol / tot_vol - 1
    eps_z = ( height_0 - height_equi) / height_0
    eps_x = ( width_0 - width_equi) / width_0
    eps_y = ( thick_0 - thick_equi)/ thick_0
    eps_vol = eps_x + eps_y + eps_z
    eps_dev = 2.0/3.0 * (eps_z - eps_x)
    stress = compute_stress()
    sxx = stress[0,0]
    syy = stress[1,1]
    szz = stress[2,2]
    p_stress = sxx + sxx + szz
    q_stress = szz - sxx
    xdiff = tsxx - sxx
    ydiff = tsyy - syy
    xrate = xdiff * gain_x
    yrate = ydiff * gain_y
    xrate = min([abs(xrate),5.0]) * np.sign(xrate)
    yrate = min([abs(yrate),5.0]) * np.sign(yrate)
    zrate = -5.0
    matrix2 = [[xrate,0,0],[0,yrate,0],[0,0,zrate]]
    itasca.fish.set('szz',-szz) 
    itasca.fish.set('zrate',zrate) 
    itasca.fish.set('sxx',-sxx) 
    itasca.fish.set('xrate',xrate) 
    itasca.fish.set('syy',-syy) 
    itasca.fish.set('yrate',yrate) 
    itasca.fish.set('thick_equi',thick_equi)
    itasca.fish.set('width_equi',width_equi)
    itasca.fish.set('height_equi',height_equi)
    itasca.fish.set('poro',porosity)
    itasca.fish.set('void_ratio',void_ratio)
    itasca.fish.set('eps_z',eps_z)
    itasca.fish.set('eps_x',eps_x)
    itasca.fish.set('eps_y',eps_y)
    itasca.fish.set('eps_vol',eps_vol)
    itasca.fish.set('eps_dev',eps_dev)
    itasca.fish.set('q_stress',-q_stress)
    itasca.fish.set('p_stress',-p_stress)

itasca.set_callback("servo_tx_strain", -11.0)

def move_boundaries(*args):
    global matrix2
    matrix2 = [[xrate,0,0],[0,yrate,0],[0,0,zrate]]
    itasca.set_domain_strain_rate(matrix2)

itasca.set_callback("move_boundaries", -11.0)

import itasca
itasca.command("""
  hist purge
  cy 160000
""")