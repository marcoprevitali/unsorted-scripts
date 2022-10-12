import itasca as it, math as ma, numpy as np
from scipy.optimize import minimize
it.command("""
python-reset-state off
model new
program call '00_generate' 
""")
initial_emod = 1e9 #[deg] from Albaba et al., 2015
initial_sb_fa = 0.6 #[-] my own parameter which governs how tighly locked the double-twists should be. default should be 1.1
initial_kratio = 1.0

target_young = 3.0e7

initial_values = np.array([initial_emod,initial_sb_fa,initial_kratio])

# bounds for the parameters
min_emod = 1.0
max_emod = 36.0
min_sb_fa = 1.09
max_sb_fa = 1.35
min_kratio = 1.09
max_kratio = 1.35
# calibration outputs
iteration_number = 0
curve_rmse = 0

def calculate_params():
    if it.cycle()%check_iter == 0:
        stress = it.fish.get('stress')
        poisson = it.fish.get('poisson')
        strain = it.fish.get('eps_ax')+1.0e-13
        young = stress/strain
        vec_poisson.append(poisson)
        vec_young.append(young)
        vec_strain.append(strain)
        global max_stress
        max_stress = max(max_stress,stress)


def mySimulation(initial_values):

    emod = initial_values[0]
    kratio = initial_values[2]
    tensileStrength = 1e9
    cohesionFactor = 1e9
    fa = initial_values[1]

    it.fish.set('emod',emod)
    it.fish.set('kratio',kratio)
    it.fish.set('tensileStrength',tensileStrength)
    it.fish.set('cohesionFactor',cohesionFactor)
    it.fish.set('fa',fa)
    it.fish.set('sb_fa',fa)
    it.command("model save 'geom_init'")
    it.command("program call '01_stress'")
    # where to calculate properties
    check_iter = 1e3
    vec_poisson = [];
    vec_young = [];
    vec_strain = [];
    max_stress = 0;


    it.set_callback("calculate_params",-1)

    it.command("""
    program call '03_UCT'
    """)

    my_young = np.median(vec_young)
    my_poisson = np.median(vec_poisson)

    print('Young: ' +str(my_young)+ ', Poisson: ' +str(my_poisson))

    return abs(my_young-target_young)
    
    
bnds = [[min_emod, max_emod],[min_sb_fa, max_sb_fa],[min_kratio, max_kratio]]
#construct the bounds in the form of constraints


cons = []
for factor in range(len(bnds)):
    lower, upper = bnds[factor]
    l = {'type': 'ineq',
         'fun': lambda x, lb=lower, i=factor: x[i] - lb}
    u = {'type': 'ineq',
         'fun': lambda x, ub=upper, i=factor: ub - x[i]}
    cons.append(l)
    cons.append(u)


#res = minimize(mySimulation,initial_values,constraints=cons,method='COBYLA', options={'rhobeg': [0.2,20],'disp': True,'maxiter':500})
res = minimize(mySimulation,initial_values,method='powell', options={'disp': True,'maxiter':500})


