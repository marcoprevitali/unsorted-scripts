import itasca as it, math as ma, numpy as np
it.command("python-reset-state false")

vec_nodes = []
vec_elements = []


fid = open('cilindro.msh','r')
a = fid.readline()
a = fid.readline()

while True:
    a = fid.readline()
    a = a.rstrip()
    b = a.split()
    myVec = []
    try:
        for c in b:
            myVec.append(float(c))
        vec_nodes.append(myVec)
    except:    
        break;
a = fid.readline()
a = fid.readline()
while True:
    a = fid.readline()
    a = a.rstrip()
    b = a.split()
    myVec = []
    try:
        for c in b:
            myVec.append(float(c))
        vec_elements.append(myVec)
    except:    
        break;
fid.close()

for element in vec_elements:
    myString = ""
    for i in range(1,len(element)):
        a = vec_nodes[int(element[i])-1]
 #       print(i)
  #      print(int(element[i]))
        for j in range(1,len(a)):
                myString+=(str(a[j]) +' ')
    #            print('j:'+str(j)+' '+str(str(a[j])))
    if i == 4:
        try:
            it.command("rblock create vertices " + myString)
        except:
            print('failed to build element: ' +str(element))
 #   print('-------')
    