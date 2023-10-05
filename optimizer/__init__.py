from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from datetime import timedelta
import pyomo.environ as pyo
import pandas as pd


    

class Sets:
    def __init__(self, date, data, evs, bess, evcs, connectors):
        self.time   = list(
            pd.date_range(
                start = date, 
                periods = int(data.Hours * 60/data.Δt), 
                freq = f'{data.Δt}T'
            )
        )
        self.evs    = list(evs.index)
        self.bess   = list(bess.index)
        self.connectors = list(connectors.index)
        return


def optimization(sets, par, evs, bess, evcs, connectors, edscosts):
    Δt = par.Δt/60

    model = pyo.ConcreteModel()
    
    #   Variables definition
    model.Peds      = pyo.Var(sets.time, within=pyo.Reals)
    model.Ppeds     = pyo.Var(sets.time, within=pyo.NonNegativeReals)
    model.Pneds     = pyo.Var(sets.time, within=pyo.NonNegativeReals)
    
    model.Pev       = pyo.Var(sets.evs, sets.time, within = pyo.NonNegativeReals)
    model.EVSoC     = pyo.Var(sets.evs, sets.time, within = pyo.NonNegativeReals)
    model.αevcs     = pyo.Var(sets.evs, sets.connectors, sets.time, within = pyo.Binary)


    #   Objective Function
    model.value = pyo.Objective(
        expr =  Δt * sum(model.Ppeds[t] * par.ceds[t.hour] for t in sets.time),        
        sense = pyo.minimize 
    )


    #   Powerflow constraints
    model.powerflow = pyo.ConstraintList()
    for t in sets.time:
        model.powerflow.add(expr = model.Peds[t] == sum(model.Pev[k, t] for k in sets.evs))
    
   
    #   EDS Constraints
    model.eds_constraint = pyo.ConstraintList()
    for t in sets.time:
        model.eds_constraint.add(expr = model.Peds[t] == model.Ppeds[t] - model.Pneds[t])


    #   EV Constraints
    model.ev_SoCini     = pyo.ConstraintList()
    model.ev_SoCend     = pyo.ConstraintList()
    model.ev_SoC        = pyo.ConstraintList()
    for ev in sets.evs:
        model.ev_SoCini.add(expr = model.EVSoC[ev, sets.time[0] + timedelta(hours = int(evs.loc[ev].arrival))] == evs.loc[ev]["SoCini"])
        model.ev_SoCend.add(expr = model.EVSoC[ev, sets.time[0] + timedelta(hours = int(evs.loc[ev].departure))] == 1)
        for t in sets.time[1:]:
            model.ev_SoC.add(expr = model.EVSoC[ev, t] == model.EVSoC[ev, t - timedelta(hours = Δt)] + Δt * model.Pev[ev, t] / evs.loc[ev]["MaxEnergy"])
    
    model.α_limit       = pyo.ConstraintList()
    for ev in sets.evs:
        for t in sets.time:
            model.α_limit.add(expr = model.Pev[ev, t] <= sum(connectors.loc[c]["Pmax"] * model.αevcs[ev, c, t] for c in sets.connectors))

    model.α_ev_limit  = pyo.ConstraintList()
    for t in sets.time:
        for c in sets.connectors:
            model.α_ev_limit.add(expr = sum(model.αevcs[ev, c, t] for ev in sets.evs) <= 1)

    model.α_connector_lim = pyo.ConstraintList()
    for t in sets.time:
        for ev in sets.evs:
            model.α_connector_lim.add(expr = sum(model.αevcs[ev, c, t] for c in sets.connectors) <= 1)

    solution = SolverFactory("gurobi")
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
    #   Get next step control signal

    return model