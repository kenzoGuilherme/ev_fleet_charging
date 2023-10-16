from optimizer import dataprocessing
import pandas as pd
import numpy as np

def datacreator(path, name):
    data        = dataprocessing.Input(path)
    par         = dataprocessing.Data(name)

    edscosts    = data.sheetreader(data.sheet5, 3)
    pardata     = data.sheetreader(data.sheet6, 3)
    
    par.parametersprocessing(pardata, edscosts)

    return par