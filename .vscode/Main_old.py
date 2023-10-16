import pandas as pd
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
import pyomo.environ as pyo

weekdays = ["mon","tue","wed","thu","fri","sat","sun"]

#Importing data from Excel and establishing dataframes
df_energy_cost = pd.read_excel("Data.xlsx", sheet_name="energy_cost")
df_vehicles = pd.read_excel("Data.xlsx", sheet_name="vehicles")
df_teams = pd.read_excel("Data.xlsx", sheet_name="teams")

Ωt = list(df_energy_cost.h)
Ωve = list(df_vehicles.plate)

df_vehicles.set_index("plate", inplace = True)
df_energy_cost.set_index("h", inplace = True)

Δt = 1 
pTrafo = 200

model = pyo.ConcreteModel()

# Variables
model.Pg = pyo.Var(Ωt, within = pyo.NonNegativeReals)
model.pSlo_status = pyo.Var(Ωt, Ωve, within = pyo.Binary)
model.pFas_status = pyo.Var(Ωt, Ωve, within = pyo.Binary)
model.pVe = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)
model.Eve = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)
model.pSlo = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)
model.pFas = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)
model.pSlo_z = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)
model.pFas_z = pyo.Var(Ωt, Ωve, within = pyo.NonNegativeReals)

# Establishing objetive function
model.value = pyo.Objective(expr = sum(df_energy_cost.loc[t].custo * model.Pg[t] for t in Ωt)
     ,sense = pyo.minimize)

# Restraints
model.initEnergy = pyo.ConstraintList()
for ve in Ωve:
     model.initEnergy.add(expr = model.Eve[18,ve] == df_vehicles.loc[ve].maxEnergy)

# sum of all power to vechicles in time 
model.activePower = pyo.ConstraintList()
for t in Ωt:
     model.activePower.add(expr = model.Pg[t] == sum(model.pVe[t,ve] for ve in Ωve))

# total power lower than maximum power (in time)
model.tranformerCapacity = pyo.ConstraintList()
for t in Ωt:
     model.tranformerCapacity.add(expr = model.Pg[t] <= pTrafo)

# Power received cannot be higher than vehicle total maximum energy
model.maxEnergy = pyo.ConstraintList()
for ve in Ωve:
     model.maxEnergy.add(expr = df_vehicles.loc[ve].maxEnergy <= model.Eve[18,ve] + sum(model.pVe[t,ve] for t in Ωt))

# Isso deve ser reduntante com a restrição de cima
model.maxEnergy_redundancy = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.maxEnergy_redundancy.add(expr = df_vehicles.loc[ve].maxEnergy >= model.Eve[t,ve])

# Charging power regime
model.powerRegime = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.powerRegime.add(expr = model.pVe[t,ve] == model.pSlo[t,ve] + model.pFas[t,ve])

# Linearizations start (slow charging)
model.linearization_pSlo_step1= pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pSlo_step1.add(expr = model.pSlo_z[t,ve] <= df_vehicles.loc[ve].pSlo_max * model.pSlo_status[t,ve])

model.linearization_pSlo_step2 = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pSlo_step2.add(expr = model.pSlo_z[t,ve] <= model.pSlo[t,ve])

model.linearization_pSlo_step3 = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pSlo_step3.add(expr = model.pSlo_z[t,ve] >= model.pSlo[t,ve] - (1-model.pSlo_status[t,ve]) * df_vehicles.loc[ve].pSlo_max)

# Linearizations start (fast charging)
model.linearization_pFas_step1= pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pFas_step1.add(expr = model.pFas_z[t,ve] <= df_vehicles.loc[ve].pFas_max * model.pFas_status[t,ve])

model.linearization_pFas_step2 = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pFas_step2.add(expr = model.pFas_z[t,ve] <= model.pFas[t,ve])

model.linearization_pFas_step3 = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.linearization_pFas_step3.add(expr = model.pFas_z[t,ve] >= model.pFas[t,ve] - (1-model.pFas_status[t,ve]) * df_vehicles.loc[ve].pFas_max)

# Mininum power for the fast charging regime
model.fastChargeFloor = pyo.ConstraintList()
for ve in Ωve:
      for t in Ωt:
            model.fastChargeFloor.add(expr = model.pFas[t,ve] >= df_vehicles.loc[ve].pFas_min)

# SOC
model.SOC = pyo.ConstraintList()
      for ve in Ωve:
            for t in Ωt:
                  if t == 18:
                      model.SOC.add(expr = model.Eve[t,ve] == model.Eve[,ve] + model.pVe[t,ve]) 
                  else:
                       
                  

#Every vehicle should be fully loaded at the end of the period 
model.fullyLoaded = pyo.ConstraintList()
for ve in Ωve:
      model.fullyLoaded.add(expr = model.Eve[6,ve] == df_vehicles.loc[ve].maxEnergy)

# No superposition of loading regimes
for ve in Ωve:
      for t in Ωt:
            model.fastChargeFloor.add(expr = model.pSlo_status[t,ve] + model.pFas_status[t,ve] <= 1)

solution = SolverFactory("glpk")
results = solution.solve(model)

if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
  print ("this is feasible and optimal")
elif results.solver.termination_condition == TerminationCondition.infeasible:
  print ("do something about it? or exit?")
else:
 # something else is wrong
  print (str(results.solver))






# numberofRows_energy_cost = df_energy_cost.shape[0]
# # Establishing the relation between energy cost and time of the day
# energy_cost = {}
# i = 0
# while i != numberofRows_energy_cost:
#     energy_cost[df_energy_cost.loc[i,"h"]] = df_energy_cost.loc[i,"custo"]
#     i += 1
# print(energy_cost)
# numberofRows_vehicles = df_vehicles.shape[0]
# # Establishing initial energy of the vehicles
# initEnergy = {}
# i = 0
# while i != numberofRows_vehicles:
#     initEnergy[df_vehicles.loc[i,"plate"]] = df_vehicles.loc[i,"initEnergy"]
#     i += 1

# #Establishing the maximum power in slow charging regime
# pSlo_max = {}
# i = 0
# while i != numberofRows_vehicles:
#     initEnergy[df_vehicles.loc[i,"plate"]] = df_vehicles.loc[i,"pSlo_max"]
#     i += 1

# #Establishing the minimum power in fast charging regime
# pFas_min = {}
# i = 0
# while i != numberofRows_vehicles:
#     pFas_min[df_vehicles.loc[i,"plate"]] = df_vehicles.loc[i,"pFas_min"]
#     i += 1

# #Establishing the maximum power in fast charging regime
# pFas_max = {}
# i = 0
# while i != numberofRows_vehicles:
#     pFas_max[df_vehicles.loc[i,"plate"]] = df_vehicles.loc[i,"pFas_max"]
#     i += 1

# #Establishing the maximum energy of the vehicles
# maxEnergy = {}
# i = 0
# while i != numberofRows_vehicles:
#     maxEnergy[df_vehicles.loc[i,"plate"]] = df_vehicles.loc[i,"maxEnergy"]
#     i += 1

# numberofRows_teams = df_teams.shape[0]

# #Establishing teams starting hours
# initTime = {}
# i = 0
# while i != numberofRows_teams:
#     initTime[df_teams.loc[i,"teamID"]] = df_teams.loc[i,"initTime"]
#     i += 1

# #Establishing teams ending hours
# endTime = {}
# i = 0
# while i != numberofRows_teams:
#     endTime[df_teams.loc[i,"teamID"]] = df_teams.loc[i,"endTime"]
#     i += 1


# #Establishing teams last working day
# endDay = {}
# i = 0
# while i != numberofRows_teams:
#     endDay[df_teams.loc[i,"teamID"]] = df_teams.loc[i,"endDay"]
#     i += 1

# for key in endDay:
#     if endDay[key] == "fri":
#         endDay[key] = ["mon","tue","wed","thu","fri"]
#     else:
#         endDay[key] = ["mon","tue","wed","thu","fri","sat","sun"]