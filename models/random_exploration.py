import time
import pandas as pd
import numpy as np
def random_exploration(gp_model_path, df, 
                           input_names, output_name,
                           parameter_space_limits,
                           output_deviation_variable,  # if output_deviation_variable exists, use as y_var, otherwise use a uniform noise hyperparameter to estimate noise
                           num_new_points =  1,
                           num_RMSE_trials = 0,
                           prev_trained_GP_hps=None,
                           train_method=None,
                           train_max_iter=None):

    from ScopeFoundry.cb32_uuid import cb32_uuid
    mfid, _uuid = cb32_uuid()
    
    
    df = pd.DataFrame(df)
    t0 = t00 = time.monotonic()

    # Explore
    
    new_points = []
    for i, param_name in enumerate(input_names):
        x0,x1 = parameter_space_limits[i]
        new_points.append(np.random.uniform(low=x0, high=x1, size=num_new_points))
    
    new_points = np.array(new_points).reshape(1,-1)
    
    return {'recommendation_id':  mfid,
            'elapsed_time': time.monotonic() - t00,
            'new_points': new_points, 
            "new_predicted_output": None, 
            "new_predicted_uncertainty":None,
            "current_trained_hps": None,
            "average_rmse":None}