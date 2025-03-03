import pandas as pd
import numpy as np

def generate_random_experiments(numb_of_experiments=10):

    filepath = '/Users/sasha_lab/Library/CloudStorage/GoogleDrive-arazumtcev@lbl.gov/Shared drives/ALDbot/Data/parameters.csv'

    parameters = pd.read_csv(filepath)

    experiments = []

    for _ in range(numb_of_experiments):
        
        experiment = {}
        for _, row in parameters.iterrows():
            
            param_name, min_val, max_val, step = row["Parameter"], row["Min"], row["Max"], row["Step"]
            possible_values = np.arange(min_val, max_val + step, step)
            experiment[param_name] = np.random.choice(possible_values)
        
        experiments.append(experiment)

    experiments = pd.DataFrame(experiments)
    
    return experiments