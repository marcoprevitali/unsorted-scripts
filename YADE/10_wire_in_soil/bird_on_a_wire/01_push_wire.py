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

vel = 1e-2


O.load('mySample.xml.bz2')
fname_nodes = 'nodes.txt'
fname_conn = 'connections.txt'
fname_balls = 'balls.txt'

fid_nodes = open(fname_nodes,'w')
fid_conns = open(fname_conn,'w')
fid_balls = open(fname_balls,'w')
myWireConnections = []
myWireNodes = []
myWalls = []
for b in O.bodies:
    if isinstance(b.shape,GridConnection):
        myWireConnections.append(b)
    elif isinstance(b.shape,GridNode):
        myWireNodes.append(b)
    elif isinstance(b.shape,Wall):
        myWalls.append(b)

topWall = myWalls[5]
leftWall = myWalls[2]
rightWall = myWalls[4]

#leftWall.state.vel = [vel,0,0]
#rightWall.state.vel = [vel,0,0]
#O.bodies.erase(topWall.id)

fid_nodes.write('time,id,x,y,z,vx,vy,vz\n')
fid_conns.write('time,x,y,z,momentBendX,momentBendY,momentBendZ,momentTwistX,momentTwistY,momentTwistZ,normalForceX,normalForceY,normalForceZ,shearForceX,shearForceY,shearForceZ\n')
fid_balls.write('time,radius,x,y,z,vx,vy,vz,spinx,spiny,spinz\n')

def exportDataStep():
    t = O.time
    print('Exporting stuff..')
    for b in myWireNodes:   
        p = b.state.pos
        v = b.state.vel
        i = b.id
        fid_nodes.write(str(t)+','+str(i)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(v[0])+','+str(v[1])+','+str(v[2])+'\n')
    for c in myWireConnections:
        cc = c.intrs()
        for ccc in cc:
            p = ccc.geom.contactPoint
            mb = ccc.phys.momentBend
            mt = ccc.phys.momentTwist
            nf = ccc.phys.normalForce
            sf = ccc.phys.shearForce
            fid_conns.write(str(t)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(mb[0])+','+str(mb[1])+','+str(mb[2])+','+str(mt[0])+','+str(mt[1])+','+str(mt[2])+','+str(nf[0])+','+str(nf[1])+','+str(nf[2])+','+str(sf[0])+','+str(sf[1])+','+str(sf[2])+'\n')
    for b in O.bodies:
        if isinstance(b.shape,Sphere):
            p = b.state.pos
            v = b.state.vel
            s = b.state.angMom
            r = b.shape.radius
            fid_balls.write(str(t)+','+str(r)+','+str(p[0])+','+str(p[1])+','+str(p[2])+','+str(v[0])+','+str(v[1])+','+str(v[2])+','+str(s[0])+','+str(s[1])+','+str(s[2])+'\n')

O.engines[-1].dead = True    
O.engines+=[PyRunner(command='exportDataStep()',iterPeriod=1000)]
#O.engines+=[VTKRecorder(fileName='output/3d-vtk-',recorders=['all'],iterPeriod=1000)]
#O.run(100000,True)

#fid_nodes.close()
#fid_balls.close()
#fid_conns.close()
print('Done')
