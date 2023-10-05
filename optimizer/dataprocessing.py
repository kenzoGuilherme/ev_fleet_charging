from datetime import timedelta
import pandas as pd

class Input:
    def __init__(self, path):
        self.path = path
        self.sheet1 = "Vehicles"
        self.sheet2 = "EVCS"
        self.sheet3 = "Connector"
        self.sheet4 = "BESS"
        self.sheet5 = "Electricity_costs"
        self.sheet6 = "Parameters"
        return
    
    def sheetreader(self, sheet, skiprows):
        dataframe = pd.read_excel(self.path, sheet, skiprows=skiprows)
        return dataframe
    

class Data:
    def __init__(self, name):
        self.name = name
        return
    
    def parametersprocessing(self, param, edscosts):
        self.Pmax_eds   = param.iloc[0]["Value"]
        self.Pmin_eds   = param.iloc[1]["Value"]
        self.Pmax_tg    = param.iloc[2]["Value"]
        self.Pmax_pv    = param.iloc[3]["Value"]
        self.Pmax_load  = param.iloc[4]["Value"]
        self.csh        = param.iloc[5]["Value"]
        self.cev        = param.iloc[6]["Value"]
        self.Δt         = param.iloc[7]["Value"]
        self.Hours      = param.iloc[8]["Value"]
        self.ceds       = list(edscosts.Energy_price)
        self.Δt         = int(self.Δt)

        return

class EVCS:
    def __init__(self, name, power, output):
        self.name = name
        self.Maxpower = power
        self.outputs = output
        return
            



