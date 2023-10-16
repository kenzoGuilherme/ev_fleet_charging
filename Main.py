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

par= datacreator.datacreator(PATH, "shopping")

sets = optimizer.Sets(now, par)
results, evs, C = optimizer.optimization(sets, par)

a = 1


##########################################################################################


from matplotlib.colors import ListedColormap
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


mpl.rc('font',family = 'serif', serif = 'cmr10')
enable = results.αevcs.get_values()
for ev in evs:
    plt.figure()
    dt = sets.time
    evcsnames = C
    heatmatrix = []
    for c in C:
        aux = []
        for t in sets.time:
            aux.append(enable[ev,c,t])
        
        heatmatrix.append(aux)

    cores = ['red', 'green']

    cores = ['red', 'green']
    cmap_personalizado = ListedColormap(cores)
    plt.imshow(heatmatrix, cmap=cmap_personalizado, aspect='auto', interpolation="nearest")
    plt.yticks(range(len(evcsnames)), evcsnames)
    horas = [d.strftime('%H:%M') for d in dt]
    plt.xticks(range(len(dt)), horas, rotation=45, ha='right')
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.tight_layout()
    plt.colorbar()  # Adicione uma barra de cores para referência
    plt.xlabel('Timestamp')
    plt.legend()
    plt.savefig(f'Results/{ev}-operation.png', format='png', dpi=300)
    plt.close("All")

a = 1

