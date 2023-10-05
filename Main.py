from datetime import datetime, timedelta
from optimizer import datacreator
import pandas as pd
import numpy as np
import optimizer
import pickle
import json
import time

class clock:
    def __init__(self):
        self.start = 0
        self.end = 0
        pass

    def counter(self):
        self.total_seconds = np.round(self.end - self.start, decimals=2)
        return

PATH = 'database\data.xlsx'

start = datetime(2013, 8, 2, 0, 0, 0)
end = datetime(2013, 8, 2, 23, 0, 0)
now = start

par, evs, bess, evcs, connectors, edscosts = datacreator.datacreator(PATH, "shopping")

sets = optimizer.Sets(now, par, evs, bess, evcs, connectors)
results = optimizer.optimization(sets, par, evs, bess, evcs, connectors, edscosts)


