from gurobipy import *
import matplotlib.pyplot as plt
import csv
import math
import random

################### Inputs ###################
random.seed(1)
a=10
b=3  #b<a
biomass=5   #5 biomass available at each site in each period
demand=26000   #13000 biomass demand, equally devided between T periods
mileage=0.01			#conversion factor for distance traveled
#mileage=10			#conversion factor for distance traveled
harvest=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1] # harvest availability limited
season=[1] * 8
h=[0] * 44
season=season+h
he=10            #unit inventory holding cost for biofuel
h=4.90   #Holding costs for feedstock, from Table 2
#beta=73.71 	#conversion rate of biomass type b, from Table 2
beta=50 	#conversion rate of biomass type b, from Table 2
graphing_1=True   #Network overview
graphing_storage=False    #Solutions
graphing_biorefinery=False

################### Functions ###################

def star(r,x,y,center):
	for vert in [-1,1]:
		x.append(center[0])
		y.append(center[1]+(r+random.uniform(0,0.1))*vert)
	for horiz in [-1,1]:
		x.append(center[0]+(r+random.uniform(0,0.1))*horiz)
		y.append(center[1])

	return x,y

def calculateDist(x1,y1,x2,y2):
	d=math.sqrt((x1-x2)**2+ (y1-y2)**2)

	return d

################### Facility Locations ###################
x_coord=[0]
y_coord=[0]
center=[0,0]
x_coord,y_coord=star(a,x_coord,y_coord,center)

for k in range(len(x_coord)):
	if k!=0:
		x_coord,y_coord=star(b,x_coord,y_coord,[x_coord[k],y_coord[k]])

if graphing_1:
	plt.scatter(x_coord, y_coord)
	plt.title("Biomass Supply Chain Locations")
	plt.show()


################### Indices ###################
T=52    #number of time periods
time=range(T)    #indices for time
k_site=range(len(x_coord))    #harvesting sites
j_site=range(len(x_coord))		#collection/ storing sites
i_site=range(len(x_coord))		#biorefinery sites
K_site=range(len(x_coord))		#customers or blending facilities
l_capacity=range(5)  #categories of biorefinery sizes
f_capacity=range(5)  #categories of collection facility sizes

################### Data ###################
p=88.33   #Harvest costs, from Table 2
alpha=[0.005, 0.001]		#Deterioration rate for in-field and on-site stock
psi_1=[23571207,28961559,34351911,45132615,50522967]		#Can CALCULTATE FROM SECTION 4.3
#psi_2=[23571207,28961559,34351911,45132615,50522967]			#Not clear for collection facilities
psi_2=[0,0,0,0,0] 			#no cost to open collection facilities
C=[10, 20, 30, 50, 60]  #biorefinery production capacities allowed
S_1=[10, 20, 30, 50, 60]   #biorefinery storage capacities allowed
S_2=[10, 20, 30, 50, 60]  #collection facility  storage capacities allowed
omega=44.30		 #unit cost of processing biomass

c=[[calculateDist(x_coord[j],y_coord[j],x_coord[i],y_coord[i])*mileage for j in j_site] for i in i_site]
c_2=c
c_3=c
c_1=c

#Define lambda_0 
lambda_0=[[biomass*harvest[k]*season[t] for t in time] for k in k_site]

#Define demand
d=[demand/T for t in time]

################### Model ###################
m = Model("biomass")

################### Decision Variables ###################
#phi: amount of biomass type b harvest from site k in period t
phi = []
for k in k_site:
	phi.append([])
	for t in time:
		phi[k].append(m.addVar(lb=0.0, obj=p,
								name="phi[%d,%d]" % (k, t)))

#z_1: amount of biomass type b stored at storing facility site j in period t
z_1 = []
for j in j_site:
	z_1.append([])
	for t in time:
		z_1[j].append(m.addVar(lb=0.0, obj=h,
								name="z_1[%d,%d]" % (j, t)))

#z_2: amount of biomass type b stored at biorefinery site i in period t
z_2 = []
for i in i_site:
	z_2.append([])
	for t in time:
		z_2[i].append(m.addVar(lb=0.0, obj=h,
								name="z_2[%d,%d]" % (i, t)))

#z: amount of biofuel stored at biorefinery site i in period t
z = []
for i in i_site:
	z.append([])
	for t in time:
		z[i].append(m.addVar(lb=0.0, obj=he,
								name="z[%d,%d]" % (i, t)))

#w: amount of biomass type b processed at biorefinery i in period t
w = []
for i in i_site:
	w.append([])
	for t in time:
		w[i].append(m.addVar(lb=0.0, obj=omega,
								name="w[%d,%d]" % (i, t)))

#y_1: amount of biomass type b shipped from harvesting site k to colllection facility j in period t
y_1 = []
for k in k_site:
	y_1.append([])
	for j in j_site:
		y_1[k].append([])
		for t in time:
			y_1[k][j].append(m.addVar(lb=0.0, obj=c_1[k][j],
									name="y_1[%d,%d,%d]" % (k, j, t)))

#y_2: amount of biomass type b shipped from harvesting site k to biorefintery i in period t
y_2 = []
for k in k_site:
	y_2.append([])
	for i in i_site:
		y_2[k].append([])
		for t in time:
			y_2[k][i].append(m.addVar(lb=0.0, obj=c_2[k][i],
									name="y_2[%d,%d,%d]" % (k, i, t)))

#y_3: amount of biomass type b shipped from collection facility j to biorefintery i in period t
y_3 = []
for j in j_site:
	y_3.append([])
	for i in i_site:
		y_3[j].append([])
		for t in time:
			y_3[j][i].append(m.addVar(lb=0.0, obj=c_3[j][i],
									name="y_3[%d,%d,%d]" % (j, i, t)))
#y: amount of biofuel shipped from  biorefinery i to blending facility kappa in period t
y = []
for i in i_site:
	y.append([])
	for K in K_site:
		y[i].append([])
		for t in time:
			y[i][K].append(m.addVar(lb=0.0, obj=c[i][K],
									name="y[%d,%d,%d]" % (i,K,t)))

#x_1: binary variable if a biorefinery located at i is opened of size l
x_1 = []
for i in i_site:
	x_1.append([])
	for l in l_capacity:
		x_1[i].append(m.addVar(vtype=GRB.BINARY, obj=psi_1[l],
								name="x_1[%d,%d]" % (i,l)))

#x_2: binary variable if a collection facility at j is opened of size f
x_2 = []
for j in j_site:
	x_2.append([])
	for f in f_capacity:
		x_2[j].append(m.addVar(vtype=GRB.BINARY, obj=psi_2[f],
								name="x_2[%d,%d]" % (j,f)))

#e: amount of biofuel produced at biorefinery site i in period t
e = []
for i in i_site:
	e.append([])
	for t in time:
		e[i].append(m.addVar(lb=0.0, obj=he,
								name="e[%d,%d]" % (i, t)))

################### Constraints ###################
# The objective is to minimize the total costs
m.modelSense = GRB.MINIMIZE

#Constraint 1
for k in k_site:
	for t in time:
		m.addConstr(phi[k][t]  <= lambda_0[k][t],
			name="BiomassAvailability[%d,%d]" % (k,t))

# for k in k_site:
# 	for t in time:
# 		m.addConstr(phi[k][1][t]  <= lambda_1[k][t],
# 			name="WoodyAvailability[%d,%d]" % (k,t))

#Constraint 2
for k in k_site:
	for t in time:
		m.addConstr(phi[k][t]  == sum(y_1[k][j][t] for j in j_site) +  sum(y_2[k][i][t] for i in i_site) ,
			name="FlowConservation_2[%d,%d]" % (k,t))

#Constraint 3
for j in j_site:
	for t in time:
		m.addConstr(sum(y_1[k][j][t] for k in k_site) + (1- alpha[0]) * z_1[j][t-1]  == sum(y_3[j][i][t] for i in i_site) +  z_1[j][t]  ,
			name="FlowConservation_3[%d,%d]" % (j,t))

#Constraint 4
for i in i_site:
	for t in time:
		m.addConstr(sum(y_2[k][i][t] for k in k_site) + sum(y_3[j][i][t] for j in j_site) + (1- alpha[1]) * z_2[i][t-1]  == w[i][t] +  z_2[i][t]  ,
			name="FlowConservation_4[%d,%d]" % (i,t))

#Constraint 5
for i in i_site:
	for t in time:
		m.addConstr(e[i][t] <= beta*w[i][t],
				name="BiofuelProduction[%d,%d]" % (i,t))

#Constraint 6
for i in i_site:
	for t in time:
		m.addConstr(e[i][t] + z[i][t-1] == sum(y[i][K][t] for K in K_site) + z[i][t],
				name="BiofuelFlowConservation[%d,%d]" % (i,t))

#Constraint 7
for j in j_site:
	for t in time:
		m.addConstr(z_1[j][t] <= sum(S_2[f]*x_2[j][f] for f in f_capacity),
				name="CollectionStorageCapacity_7[%d,%d]" % (j,t))

#Constraint 8
for i in i_site:
	for t in time:
		m.addConstr(z_2[i][t] <= sum(S_1[l]*x_1[i][l] for l in l_capacity),
				name="BiorefineryStorageCapacity_8[%d,%d]" % (i,t))

#Constraint 9
for i in i_site:
	for t in time:
		m.addConstr(e[i][t] <= sum(C[l]*x_1[i][l] for l in l_capacity),
				name="ProductionCapacity[%d,%d]" % (i,t))


#Constraint 10
for t in time:
	m.addConstr(quicksum(y[i][K][t] for K in K_site for i in i_site)==d[t],
			name="Demand[%d]" % (t))

#Constraint 11
for i in i_site:
	m.addConstr(sum(x_1[i][l] for l in l_capacity) <= 1,
		name="StorageSizeUniqueness[%d]" % (i))

#Constraint 12
for j in j_site:
	m.addConstr(sum(x_2[j][f] for f in f_capacity) <= 1,
		name="BiorefinerySizeUniqueness[%d]" % (j))

#Constraint 13
for j in j_site:
	m.addConstr(z_1[j][0]==0,
		name="InitialInventory_1[%d,0]" % (j))
for i in i_site:
	m.addConstr(z_2[i][0]==0,
		name="InitialInventory_2[%d,0]" % (i))

for i in i_site:
	m.addConstr(z[i][0]==0,
		name="InitialInventory_0[%d,0]" % (i))

# Save model
m.write('biomassPY.lp')

# Solve
m.optimize()

print('SOLUTION:')

transportation=0
for t in time:
	for k in k_site:
		for j in j_site:
			transportation+=c_1[k][j]*y_1[k][j][t].x
			if y_1[k][j][t].x>0 and k!=j:
				print(k,j,y_1[k][j][t].x,c_1[k][j])

	for k in k_site:
		for i in i_site:
			transportation+=c_2[k][i]*y_2[k][i][t].x
			if y_2[k][i][t].x>0 and k!=i:
				print(k,i,y_2[k][i][t].x,c_2[k][i])

	for j in j_site:
		for i in i_site:
			transportation+=c_3[j][i]*y_3[j][i][t].x
			if y_3[j][i][t].x>0 and i!=j:
				print(j,i,y_3[j][i][t].x,c_3[j][i])


	for i in i_site:
		for K in K_site:
			transportation+=c[i][K]*y[i][K][t].x
			if y[i][K][t].x>0 and i!=K:
				print(i,K,y[i][K][t].x,c[i][K])

print("Transportation costs %f" % transportation)

num_open=0
construction=0
for i in i_site:
	for l in l_capacity:
		construction+=psi_1[l]*x_1[i][l].x
		if x_1[i][l].x>0:
			num_open+=1

for j in j_site:
	for f in f_capacity:
		construction+=psi_2[f]*x_2[j][f].x

print("Construction costs %f" % construction)

storing=0
for t in time:
	for j in j_site:
		storing+=h*z_1[j][t].x

	for i in i_site:
		storing+=h*z_2[i][t].x
		storing+=he*z[i][t].x

print("Storage costs %f" % storing)

harvesting=0
for t in time:
	for k in k_site:
		harvesting+=p*phi[k][t].x

print("Harvesting costs %f" % harvesting)

processing=0
for t in time:
	for i in i_site:
		processing+=omega*w[i][t].x

print("Processing costs %f" % processing)

produced=0
for t in time:
	for K in K_site:
		for i in i_site:
			produced+=y[i][K][t].x


print("Biofuel Produced %f" % produced)

print(transportation)
print(construction)
print(harvesting)
print(storing)
print(processing)
print(num_open)


if graphing_biorefinery:
	x_open=list()
	y_open=list()
	for i in i_site:
		for l in l_capacity:
			if x_1[i][l].x>0:
				x_open.append(x_coord[i])
				y_open.append(y_coord[i])

	plt.scatter(x_coord, y_coord,  label="closed")
	plt.scatter(x_open, y_open,  label="open")
	plt.legend(loc="upper left")
	plt.title("Biorefineries")
	plt.show()

if graphing_storage:
	x_open=list()
	y_open=list()
	for j in j_site:
		for f in f_capacity:
			if x_2[j][f].x>0:
				x_open.append(x_coord[j])
				y_open.append(y_coord[j])

	plt.scatter(x_coord, y_coord,  label="closed")
	plt.scatter(x_open, y_open,  label="open")
	plt.legend(loc="upper left")
	plt.title("Storage Facilities")
	plt.show()
