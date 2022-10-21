# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *

import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import optimization
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior


import numpy as np, scipy as sp, math as ma

# main beam parameters, position on X is always 0
beam_max_y = 0.0
beam_min_y = -10.0

num_springs = 9

# material parameters
YoungBeam = 1.0e5
PoissonBeam = 0.3

horizDisp = 0.1

Mdb()

# create the materials
mdb.models['Model-1'].Material(name='Elastoplastic')
mdb.models['Model-1'].materials['Elastoplastic'].Elastic(table=((YoungBeam, PoissonBeam),
    ))


# insert the material plasticity table here. first column is the true stress, the second is the plastic strain
mdb.models['Model-1'].materials['Elastoplastic'].Plastic(table=((10.0,
    0.0), ))

mdb.models['Model-1'].Material(name='Material-2')
mdb.models['Model-1'].materials['Material-2'].Elastic(table=((YoungBeam, PoissonBeam), ))




# create the beam geometry (as a line)

spring_distance = (beam_max_y-beam_min_y)/(num_springs+1)
session.viewports['Viewport: 1'].setValues(displayedObject=None)
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=1.0)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.setPrimaryObject(option=STANDALONE)
for i in range(0,num_springs):
    pos_y_spring = beam_max_y - spring_distance * (i+1)
    s.Line(point1=(0.0, pos_y_spring + spring_distance), point2=(0.0, pos_y_spring))

s.VerticalConstraint(entity=g[2], addUndoState=False)
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=TWO_D_PLANAR,
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['Part-1']
p.BaseWire(sketch=s)
s.unsetPrimaryObject()
p = mdb.models['Model-1'].parts['Part-1']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
p = mdb.models['Model-1'].parts['Part-1']
e = p.edges




s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=1.0)
g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
s1.setPrimaryObject(option=STANDALONE)

for i in range(0,num_springs):
    pos_y_spring = beam_max_y - spring_distance * (i+1)
    p = mdb.models['Model-1'].parts['Part-1']
    p.DatumPointByCoordinate(coords=(0.0, pos_y_spring, 0.0))
    s1.Line(point1=(-0.2, pos_y_spring), point2=(-0.1, pos_y_spring))
    s1.HorizontalConstraint(entity=g[2], addUndoState=False)
p = mdb.models['Model-1'].Part(name='FixedBeam', dimensionality=TWO_D_PLANAR,
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['FixedBeam']
p.BaseWire(sketch=s1)
s1.unsetPrimaryObject()
p = mdb.models['Model-1'].parts['FixedBeam']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
session.viewports['Viewport: 1'].partDisplay.setValues(sectionAssignments=ON,
    engineeringFeatures=ON)
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
    referenceRepresentation=OFF)


# assign the beam sections and materials
mdb.models['Model-1'].CircularProfile(name='Profile-1', r=0.1)
mdb.models['Model-1'].BeamSection(name='Beam1', integration=DURING_ANALYSIS,
    poissonRatio=0.3, profile='Profile-1', material='Elastoplastic',
    temperatureVar=LINEAR, consistentMassMatrix=False)
mdb.models['Model-1'].BeamSection(name='Section-2',
    integration=DURING_ANALYSIS, poissonRatio=0.0, profile='Profile-1',
    material='Material-2', temperatureVar=LINEAR,
    consistentMassMatrix=False)
a = mdb.models['Model-1'].rootAssembly

a = mdb.models['Model-1'].rootAssembly
a.DatumCsysByDefault(CARTESIAN)
p = mdb.models['Model-1'].parts['Part-1']
a.Instance(name='Part-1-1', part=p, dependent=ON)
p = mdb.models['Model-1'].parts['FixedBeam']
a.Instance(name='FixedBeam-1', part=p, dependent=ON)


# connect stuff
a = mdb.models['Model-1'].rootAssembly
v11 = a.instances['FixedBeam-1'].vertices
v12 = a.instances['Part-1-1'].vertices
for i in range(0,num_springs):
    id_fixed = num_springs*2-1 - i
    if i%2 > 0:
        id_fixed = i
    id_beam = num_springs-i

    print(id_fixed)
    print(id_beam)
    print('----')
    a.WirePolyLine(points=((v11[id_fixed], v12[id_beam]), ), mergeType=IMPRINT, meshable=OFF)
    a = mdb.models['Model-1'].rootAssembly
    e1 = a.edges
    edges1 = e1.getSequenceFromMask(mask=('[#1 ]', ), )
    a.Set(edges=edges1, name='Wire-Fixed-'+str(i))

for i in range(0,num_springs):
    mdb.models['Model-1'].ConnectorSection(name='ConnSect-'+str(i),
        translationalType=AXIAL)

    #elastic_0 = connectorBehavior.ConnectorElasticity(components=(1, ),
    #    behavior=NONLINEAR, table=((0.1, 0.01), (0.2, 0.015), (0.3, 0.02))) # could load txt

    elastic_0 = connectorBehavior.ConnectorElasticity(components=(1, ), table=((
        1.0, ), ))

    mdb.models['Model-1'].sections['ConnSect-'+str(i)].setValues(behaviorOptions =(
        elastic_0, ) )
    mdb.models['Model-1'].sections['ConnSect-'+str(i)].behaviorOptions[0].ConnectorOptions(     )
mdb.models['Model-1'].ConnectorSection(name='ConnSect-Trains',
    assembledType=TRANSLATOR)
a = mdb.models['Model-1'].rootAssembly


for i in range(0,num_springs):
    a = mdb.models['Model-1'].rootAssembly
    region=a.sets['Wire-Fixed-'+str(i)]
    csa = a.SectionAssignment(sectionName='ConnSect-'+str(i), region=region)


p = mdb.models['Model-1'].parts['FixedBeam']
e = p.edges
edges = e.getSequenceFromMask(mask=('[#1ff ]', ), )
region=p.Set(edges=edges, name='Set-2')
p = mdb.models['Model-1'].parts['FixedBeam']
p.assignBeamSectionOrientation(region=region, method=N1_COSINES, n1=(0.0, 0.0,
-1.0))


p = mdb.models['Model-1'].parts['Part-1']
e = p.edges
edges = e.getSequenceFromMask(mask=('[#1ff ]', ), )
region=p.Set(edges=edges, name='Set-2')
p = mdb.models['Model-1'].parts['Part-1']
p.assignBeamSectionOrientation(region=region, method=N1_COSINES, n1=(0.0, 0.0,
-1.0))
a = mdb.models['Model-1'].rootAssembly
a.regenerate()

a = mdb.models['Model-1'].rootAssembly
e1 = a.instances['FixedBeam-1'].edges
edges1 = e1.getSequenceFromMask(mask=('[#1ff ]', ), )
v1 = a.instances['FixedBeam-1'].vertices
verts1 = v1.getSequenceFromMask(mask=('[#3ffff ]', ), )
region = a.Set(vertices=verts1, edges=edges1, name='Set-10')
mdb.models['Model-1'].EncastreBC(name='BC-1', createStepName='Initial',
region=region, localCsys=None)
a = mdb.models['Model-1'].rootAssembly
v1 = a.instances['Part-1-1'].vertices
verts1 = v1.getSequenceFromMask(mask=('[#1 ]', ), )
region = a.Set(vertices=verts1, name='Set-11')
mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Initial',
region=region, u1=SET, u2=SET, ur3=UNSET, amplitude=UNSET,
distributionType=UNIFORM, fieldName='', localCsys=None)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(loads=OFF, bcs=OFF,
predefinedFields=OFF, connectors=OFF, adaptiveMeshConstraints=ON)
mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial',
timePeriod=100.0, maxNumInc=1000, initialInc=1.0, minInc=0.001,
maxInc=1.0)


mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial',
timePeriod=100.0, maxNumInc=1000, initialInc=1.0, minInc=0.001,
maxInc=1.0)

mdb.models['Model-1'].boundaryConditions['BC-2'].setValuesInStep(
        stepName='Step-1', u1=horizDisp, u2=FREED)


p = mdb.models['Model-1'].parts['Part-1']
p.seedPart(size=0.1, deviationFactor=0.1, minSizeFactor=0.1)
p = mdb.models['Model-1'].parts['Part-1']
p.generateMesh()
p = mdb.models['Model-1'].parts['FixedBeam']
p.seedPart(size=0.01, deviationFactor=0.1, minSizeFactor=0.1)
p = mdb.models['Model-1'].parts['FixedBeam']
p.generateMesh()
a = mdb.models['Model-1'].rootAssembly
a.regenerate()

p = mdb.models['Model-1'].parts['FixedBeam']
e = p.edges
edges = e.getSequenceFromMask(mask=('[#1ff ]', ), )
region = regionToolset.Region(edges=edges)
p = mdb.models['Model-1'].parts['FixedBeam']
p.SectionAssignment(region=region, sectionName='Section-2', offset=0.0,
    offsetType=MIDDLE_SURFACE, offsetField='',
    thicknessAssignment=FROM_SECTION)
p1 = mdb.models['Model-1'].parts['Part-1']
p = mdb.models['Model-1'].parts['Part-1']
e = p.edges
edges = e.getSequenceFromMask(mask=('[#1ff ]', ), )
region = regionToolset.Region(edges=edges)
p = mdb.models['Model-1'].parts['Part-1']
p.SectionAssignment(region=region, sectionName='Beam1', offset=0.0,
    offsetType=MIDDLE_SURFACE, offsetField='',
    thicknessAssignment=FROM_SECTION)

mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=1,
    numGPUs=0)

mdb.jobs['Job-1'].submit(consistencyChecking=ON)

print('Running..')

