from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from datetime import timedelta
import pyomo.environ as pyo
import pandas as pd

class Sets:
        def __init__(self, date, data): # evs, bess, evcs, connectors):
            self.time   = list(
                pd.date_range(
                    start = date, 
                    periods = int(data.Hours * 60/data.Δt), 
                    freq = f'{data.Δt}T'
                )
            )
#            self.evs    = list(evs.index)
#            self.bess   = list(bess.index)
#            self.connectors = list(connectors.index)
            return
        
df_BESS = pd.read_excel("data.xlsx", sheet_name="BESS")
df_Connector = pd.read_excel("data.xlsx", sheet_name="Connector")
df_Vehicles = pd.read_excel("data.xlsx", sheet_name="Vehicles")

evs = set()
for x in  range(0, len(list(df_Vehicles.Name))):
    evs.add(df_Vehicles.loc[x,"Name"])
df_Vehicles.set_index("Name", inplace = True)

C = set()
for y in  range(0, len(list(df_Connector.Connector))):
    C.add(df_Connector.loc[y,"Connector"])
df_Connector.set_index("Connector", inplace = True)



def optimization(sets, par):
    Δt = par.Δt/60

    model = pyo.ConcreteModel()

### Variables definition   

    model.pTotalGrid   = pyo.Var(sets.time, within=pyo.Reals)
    model.pPosGrid     = pyo.Var(sets.time, within=pyo.NonNegativeReals)
    model.pNegGrid     = pyo.Var(sets.time, within=pyo.NonNegativeReals)

    model.pEV       = pyo.Var(evs, sets.time, within = pyo.NonNegativeReals)
    model.SoCEV     = pyo.Var(evs, sets.time, within = pyo.NonNegativeReals)
    model.αevcs     = pyo.Var(evs, C, sets.time, within = pyo.Binary)

    model.pChargeBess      = pyo.Var(sets.time, within=pyo.NonNegativeReals)
    model.pDischargeBess   = pyo.Var(sets.time, within=pyo.NonNegativeReals)
    model.SoCBess          = pyo.Var(sets.time, within=pyo.NonNegativeReals)

### Objective Function

    model.value = pyo.Objective(
        expr =  Δt * sum(model.pPosGrid[t] * par.ceds[t.hour] for t in sets.time),        
        sense = pyo.minimize)

### Constraints

#   Bess SoC Development 
    model.bessDynamic = pyo.ConstraintList()
    for t in sets.time:
        if t != sets.time[0]:
            model.bessDynamic.add(expr = model.SoCBess[t] == model.SoCBess[t-timedelta(hours = Δt)] 
                                    + (model.pChargeBess[t] - model.pDischargeBess[t]) 
                                    * Δt / df_BESS.loc[0,"Capacity"])
        else:
            model.bessDynamic.add(expr = model.SoCBess[t] == df_BESS.loc[0,"Minimum SOC"])

#   Bess SoC Boundaries
#   Bess SoC Boundaries (Lower)
    model.bessSoCBoundariesLower = pyo.ConstraintList()
    model.bessSoCBoundariesLower.add(expr = model.SoCBess[t] >= df_BESS.loc[0,"Minimum SOC"])
                                
#   Bess SoC Boundaries (Higher)
    model.bessSoCBoundariesHigher = pyo.ConstraintList()
    model.bessSoCBoundariesHigher.add(expr = model.SoCBess[t] <= 1)                    
        
#  Powerflow
    model.powerflow = pyo.ConstraintList()
    for t in sets.time:
        model.powerflow.add(expr = model.pTotalGrid[t] == sum(model.pEV[ev, t] for ev in evs)
                             + model.pChargeBess[t] - model.pDischargeBess[t])

#   EDS Constraints
    model.gridConstraint = pyo.ConstraintList()
    for t in sets.time:
        model.gridConstraint.add(expr = model.pTotalGrid[t] == model.pPosGrid[t] - model.pNegGrid[t])
                      
#   EVs SoC Development
    model.evSoCDevelopment = pyo.ConstraintList()
    model.initialSoC = pyo.ConstraintList()
    model.finalSoC = pyo.ConstraintList()

    for ev in evs:
        for t in sets.time:
            if t.hour == df_Vehicles.loc[ev,"arrival"]:
                model.initialSoC.add(expr = model.SoCEV[ev,t] == df_Vehicles.loc[ev,"initialSoC"])
            if t.hour == df_Vehicles.loc[ev,"departure"]:
                model.finalSoC.add(expr = model.SoCEV[ev,t] == 1)

        for t in sets.time[1:]: 
            model.evSoCDevelopment.add(expr = model.SoCEV[ev,t] == model.SoCEV[ev,t-timedelta(hours = Δt)] 
                                            + (model.pEV[ev,t]) * Δt /df_Vehicles.loc[ev,"MaxEnergy"])


#   α Constraints
    model.α_limit = pyo.ConstraintList()
    for ev in evs:
        for t in sets.time:
            model.α_limit.add(expr = model.pEV[ev, t] <= sum(df_Connector.loc[c,"Pmax"] * model.αevcs[ev, c, t] for c in C))

    model.α_ev_limit = pyo.ConstraintList()
    for t in sets.time:
        for c in C:
            model.α_ev_limit.add(expr = sum(model.αevcs[ev, c, t] for ev in evs) <= 1)

    model.α_connector_lim = pyo.ConstraintList()
    for t in sets.time:
        for ev in evs:
            model.α_connector_lim.add(expr = sum(model.αevcs[ev, c, t] for c in C) <= 1)  

    model.α_switch = pyo.ConstraintList()
    for ev in evs:
        for c in C:
            for t in sets.time[1:]:
                model.α_switch.add(expr = model.αevcs[ev, c, t-timedelta(hours = Δt)] - model.αevcs[ev, c, t] 
                                   <= model.SoCEV[ev,  t-timedelta(hours = Δt)]) 

###

    solution = SolverFactory("gurobi")
    solution.options['FeasibilityTol'] = 1e-02  # Set the feasibility tolerance
    solution.options['OptimalityTol'] = 1e-02   # Set the optimality tolerance
    solution.options['BarConvTol'] = 1e-02      # Set the barrier convergence tolerance
    results = solution.solve(model)

    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        print ("this is feasible and optimal")
    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print ("do something about it? or exit?")
        return
    else:
        # something else is wrong
        print (str(results.solver))
        return
    
    print(f'Função objetivo: {model.value()}')

    return model, evs, C