from datetime import datetime, timedelta
import pandas as pd

pv = pd.read_csv('database\PV.csv', index_col='datetime', parse_dates=True)
load = pd.read_csv('database\load.csv', index_col='datetime', parse_dates=True)

def pvprofile(start, length):
    return pv[start:start + timedelta(hours=length)]/1000

def loadprofile(start, length):
    current = load[start:start + timedelta(hours=length)]
    current = current.drop(["p1"], axis=1)
    current = current.drop(["lef"], axis=1)

    total = current.sum(axis=1)
    total = pd.DataFrame(total, columns=["value"])
    return total.loc[total["value"] >= 0]/1000