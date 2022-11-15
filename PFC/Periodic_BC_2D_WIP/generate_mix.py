import itasca as it, math as ma, numpy as np

width = it.fish.get('width')
height = it.fish.get('height')
porosity = it.fish.get('poros')

solid_volume = width*height*(1-porosity)

vol_tri = it.fish.get('solid_vol_triangles')
vol_hex = it.fish.get('solid_vol_hexagons')
vol_cir = it.fish.get('solid_vol_circles')
vol_sqr = it.fish.get('solid_vol_squares')
vol_pen = it.fish.get('solid_vol_pentagons')
vol_hep = it.fish.get('solid_vol_heptagons')
vol_ico = it.fish.get('solid_vol_icosagons')
total_input_vol = vol_tri+vol_hex+vol_cir+vol_sqr+vol_pen+vol_hep+vol_ico

vol_tri /= total_input_vol
vol_hex /= total_input_vol
vol_cir /= total_input_vol
vol_sqr /= total_input_vol
vol_pen /= total_input_vol
vol_hep /= total_input_vol
vol_ico /= total_input_vol

d1 = it.fish.get('diam1')
d2 = it.fish.get('diam2')
p1 = it.fish.get('perc1')
p2 = it.fish.get('perc2')
 


 
init_scale = it.fish.get('init_scale')


#volume = width*height
#solid_volume = volume * (1.0-porosity)
#volume_triangle = init_scale * solid_volume / num_triangles
#side_triangle = 2.0*ma.sqrt(volume_triangle/ma.sqrt(3.0))
#circumradius = side_triangle / ma.sqrt(3.0)


def generate_shape(n_corners,name):
    angle = 2.0/n_corners*ma.pi
    str_verts = ''
    for i in range(0,n_corners):
        scaling_val = 2.0
        str_verts += str(ma.cos(angle*i))+" "+str(ma.sin(angle*i)*scaling_val)+" "
    print(str_verts)
    it.command("rblock template create "+name+" vertices " + str_verts)


# triangles
n_corners = 3
name = "'tri'"
generate_shape(n_corners,name)


# squares
n_corners = 4
name = "'sqr'"
generate_shape(n_corners,name)

#hexagons
n_corners = 6
name = "'hex'"
generate_shape(n_corners,name)

n_corners = 5
name = "'pen'"
generate_shape(n_corners,name)

n_corners = 7
name = "'hep'"
generate_shape(n_corners,name)

n_corners = 20
name = "'ico'"
generate_shape(n_corners,name)

# do nothing with triangles for now

# circles, for simplicity im generating them at the full scale
sol_vol1 = solid_volume*vol_cir*p1/(p1+p2)
sol_vol2 = solid_volume*vol_cir*p2/(p1+p2)
vol1 = (d1/2)**2*ma.pi
vol2 = (d2/2)**2*ma.pi
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
print('Number of small circles skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large circles skipped: '+str((sol_vol2/vol2)-n2))
if vol_cir>0:
    it.command("ball generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" radius "+str(d1/2*init_scale))
    it.command("ball generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" radius "+str(d2/2*init_scale))

# squares
sol_vol1 = solid_volume*vol_sqr*p1/(p1+p2)
sol_vol2 = solid_volume*vol_sqr*p2/(p1+p2)
vol1 = (d1)**2
vol2 = (d2)**2
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
if vol_sqr>0:
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" size "+str(vol1*init_scale)+" templates 1 'sqr'")
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" size "+str(vol2*init_scale)+" templates 1 'sqr'")
print('Number of small squares skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large squares skipped: '+str((sol_vol2/vol2)-n2))
# hexagons
sol_vol1 = solid_volume*vol_hex*p1/(p1+p2)
sol_vol2 = solid_volume*vol_hex*p2/(p1+p2)
vol1 = 6*(d1/2)**2*ma.sqrt(3.0)/4
vol2 = 6*(d2/2)**2*ma.sqrt(3.0)/4
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
if vol_hex>0:
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" size "+str(vol1*init_scale)+" templates 1 'hex'")
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" size "+str(vol2*init_scale)+" templates 1 'hex'")
print('Number of small hexagons skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large hexagons skipped: '+str((sol_vol2/vol2)-n2))
# pentagons
sol_vol1 = solid_volume*vol_pen*p1/(p1+p2)
sol_vol2 = solid_volume*vol_pen*p2/(p1+p2)
vol1 = 5*(d1/2)**2*(ma.sqrt((5+ma.sqrt(5.0))/2))/4
vol2 = 5*(d2/2)**2*(ma.sqrt((5+ma.sqrt(5.0))/2))/4
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
if vol_pen>0:
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" size "+str(vol1*init_scale)+" templates 1 'pen'")
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" size "+str(vol2*init_scale)+" templates 1 'pen'")
print('Number of small pentagons skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large pentagons skipped: '+str((sol_vol2/vol2)-n2))
# heptagons
sol_vol1 = solid_volume*vol_hep*p1/(p1+p2)
sol_vol2 = solid_volume*vol_hep*p2/(p1+p2)
vol1 = (7*d1**2*(1/(ma.tan(ma.pi/7))))/4 
vol2 = (7*d2**2*(1/(ma.tan(ma.pi/7))))/4 
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
if vol_hep>0:
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" size "+str(vol1*init_scale)+" templates 1 'hep'")
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" size "+str(vol2*init_scale)+" templates 1 'hep'")
print('Number of small heptagons skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large heptagons skipped: '+str((sol_vol2/vol2)-n2))
# icosagons
sol_vol1 = solid_volume*vol_ico*p1/(p1+p2)
sol_vol2 = solid_volume*vol_ico*p2/(p1+p2)
vol1 = 31.5687*(d1**2)
vol2 = 31.5687*(d2**2)
n1 = ma.floor(sol_vol1/vol1)
n2 = ma.floor(sol_vol2/vol2)
if vol_ico>0:
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n1)+" size "+str(vol1*init_scale)+" templates 1 'ico'")
    it.command("rblock generate box 0 "+str(width)+" 0 "+str(height)+" number "+str(n2)+" size "+str(vol2*init_scale)+" templates 1 'ico'")
print('Number of small icosagons skipped: '+str((sol_vol1/vol1)-n1))
print('Number of large icosagons skipped: '+str((sol_vol2/vol2)-n2))
