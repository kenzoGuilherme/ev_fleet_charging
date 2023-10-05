from optimizer import dataprocessing
import pandas as pd
import numpy as np

def datacreator(path, name):
    data        = dataprocessing.Input(path)
    par         = dataprocessing.Data(name)
    evs         = data.sheetreader(data.sheet1, 3)
    evcs        = data.sheetreader(data.sheet2, 3)
    connectors  = data.sheetreader(data.sheet3, 3)
    bess        = data.sheetreader(data.sheet4, 3)
    edscosts    = data.sheetreader(data.sheet5, 3)
    pardata     = data.sheetreader(data.sheet6, 3)

    evs.set_index("Name", inplace=True)
    bess.set_index("Name", inplace=True)
    evcs.set_index("Name", inplace=True)
    connectors.set_index("Connector", inplace=True)
    
    par.parametersprocessing(pardata, edscosts)


    return par, evs, bess, evcs, connectors, edscosts


