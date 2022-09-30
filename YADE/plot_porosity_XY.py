from yade import pack, qt, plot
import math as ma, numpy as np
import matplotlib.pyplot as plt


O.load('sample_calvetti_hr_001.xml.bz2')


#calculate the porosity std in a set of blocks
def sample_bin_porosity():
	all_phi = []
	num_poro_bins =15
	H=np.zeros((num_poro_bins,num_poro_bins))
	for i in range (0,num_poro_bins):
		for j in range (0,num_poro_bins): #ashtag torrette
			ll=((5.35/(num_poro_bins)*i),((5.35/(num_poro_bins)*j)),0)
			ur=((5.35/(num_poro_bins)*(i+1)),((5.35/(num_poro_bins)*(j+1))),2)
			k=1
			local_poro = utils.voxelPorosity(start=ll,end=ur)
            		print('Bin ('+str(i)+','+str(j)+','+str(k)+'), phi:' + str(local_poro))
            		all_phi.append(local_poro)
			H[i,j]=local_poro
	print('-------------------------------')
    
	plt.imshow(H)
	plt.colorbar()    
	plt.show()
    

sample_bin_porosity()
    
