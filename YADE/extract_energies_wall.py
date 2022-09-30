from yade import pack, qt, plot
import math as ma, numpy as np
import matplotlib.pyplot as plt


O.load('sample_calvetti_hr_001.xml.bz2')
NI.damping=0.0
peso_grave = 850
raggio_grave = 0.9/2
maxZ = 0
for i in O.bodies:
	maxZ = max(O.bodies.state.pos[2],maxZ)
posizione_grave = (5.35/2,5.35/2,maxZ+raggio_grave+0.1)
velocita_grave = -20



O.bodies.erase(5)
O.engines[4].dead=True
O.engines[5].dead=True
fidb=open('output/bottom.txt','w')
fidb.write('t    x   y   n \n')
fidn=open('output/north.txt','w') #in realt tipo bho
fidn.write('t    x   z   n \n')
fidw=open('output/west.txt','w') #in realt tipo bho
fidw.write('t    x   z   n \n')
fide=open('output/east.txt','w') #in realt tipo bho
fide.write('t    x   z   n \n')
fids=open('output/south.txt','w') #in realt tipo bho
fids.write('t    x   z   n \n')
fid_boulder = open ('output/boulder_pos.txt','w')
fid_boulder.write('t    x   y   z \n')
fid_sec = open ('output/contact_section.txt','w')
fid_sec.write('t    x   y   z    f \n')
# generate the boulder
volume_grave = 4./3*raggio_grave**3*ma.pi
densita_grave = peso_grave/volume_grave
graveMat = FrictMat(young=10e6, poisson=0.25, density=densita_grave, frictionAngle=radians(11.3), label='Grave') 
grave_id = O.bodies.append(utils.sphere(posizione_grave,radius=raggio_grave,material=graveMat))
grave_instance = O.bodies[grave_id]
grave_instance.state.vel[2] = velocita_grave


O.engines+=[PyRunner(command='exportDataStep()',iterPeriod=10)]
O.engines+=[VTKRecorder(filename='output/3d-vtk-',recorders=['all'],iterPeriod=10)]

def exportDataStep():
    cb = O.bodies[0].intrs()
    cs = O.bodies[1].intrs()
    cw = O.bodies[2].intrs()
    cn = O.bodies[3].intrs()
    ce = O.bodies[4].intrs()
    
    section_interactions = []
    for i in O.interactions:
        if i.geom.contactPoint[1] < 5.35/2+5.35/20 and i.geom.contactPoint[1] > 5.35/2-5.35/20:
            total_force = (i.phys.shearForce[0]**2+i.phys.shearForce[1]**2+i.phys.shearForce[2]**2)**0.5+(i.phys.normalForce[0]**2+i.phys.normalForce[1]**2+i.phys.normalForce[2]**2)**0.5
            fid_sec.write(str(O.time)+' '+str(i.geom.contactPoint[0])+'   '+str(i.geom.contactPoint[1])+'   '+str(i.geom.contactPoint[2])+'  '+str(total_force)+'\n')
    
    
    boulder = O.bodies[-1]
    for i in cb:
        pos = O.bodies[i.id2].state.pos
        force = i.phys.normalForce
        fidb.write(str(O.time)+' '+str(pos[0])+' '+str(pos[1])+' '+str(force[2])+'\n');
    for i in cs:
        pos = O.bodies[i.id2].state.pos
        force = i.phys.normalForce
        fidn.write(str(O.time)+' '+str(pos[0])+' '+str(pos[2])+' '+str(force[1])+'\n');
    for i in cw:
        pos = O.bodies[i.id2].state.pos
        force = i.phys.normalForce
        fide.write(str(O.time)+' '+str(pos[1])+' '+str(pos[2])+' '+str(force[0])+'\n');
    for i in cn:
        pos = O.bodies[i.id2].state.pos
        force = i.phys.normalForce
        fids.write(str(O.time)+' '+str(pos[0])+' '+str(pos[2])+' '+str(-force[1])+'\n');
    for i in ce:
        pos = O.bodies[i.id2].state.pos
        force = i.phys.normalForce
        fidw.write(str(O.time)+' '+str(pos[1])+' '+str(pos[2])+' '+str(-force[0])+'\n');
    fid_boulder.write(str(O.time)+' '+str(boulder.state.pos[0])+'   '+str(boulder.state.pos[1])+'   '+str(boulder.state.pos[2])+'\n')
    print(O.iter)
    if utils.unbalancedForce()<0.01:
        Omega.pause()
        fidn.close()
        fidb.close()
    
O.run(2500,True)
        
fidn.close()
fidb.close()
fids.close()
fidw.close()
fide.close()
fid_boulder.close()
fid_sec.close()

