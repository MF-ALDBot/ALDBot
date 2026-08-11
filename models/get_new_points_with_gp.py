import pandas as pd
import importlib
def load_from_module_path(path):
    m,c = path.split(":")
    mod = importlib.import_module(m)
    C = getattr(mod, c)
    return mod, C

def Get_New_Points_With_GP(gp_model_path, df, 
                           input_names, output_name,
                           parameter_space_limits,
                           output_deviation_variable,  # if output_deviation_variable exists, use as y_var, otherwise use a uniform noise hyperparameter to estimate noise
                           num_new_points =  1,
                           num_RMSE_trials = 0,
                           prev_trained_GP_hps=None,
                           train_method="global",
                           train_max_iter=4000):

    '''
    Input: 
        gp_model_path:       Import path to the .py file which contains the GP model with the specific prior mean function to be used
        gp_model_name:       Name of the attribute in gp_model_path to be used.
        df:                  nx(d+1) A data frame that includes all collected experimental data. n is number of experiments
        input_names:         d list of the names of the d input variables
        output_name:         column name of output variable that GP will predict
        parameter_space_limits: dx2 numpy array that has the limits of the parameter space for all dimensions of length d.
        output_deviation_variable: column name of output variable variance
        num_new_points:      positive integer specifying the number of new point to find by the Bayesian Optimization
        num_RMSE_trials:     positive integer specifying the number of trials for cross-validation, if 0, cross-validation is skipped
        prev_trained_GP_hps: trained hyperparameters from the previous loop, if not given function assumes first run so information gain will be skipped
        
    Outputs a dictionary with the following keys:
        new_points:                 New points outputed from the Bayesian optimization, as an array
        new_predicted_output:      Predicted mean at the new point
        new_predicted_uncertainty: Predicted uncertainty at the new point
        current_trained_hps:       Trained GP hyperparameters
        average_rmse:              Mean RMSE from the cross validation
        
    ........................ Code prepared by Maher Alghalayini on February 12, 2025 ........................
    
    '''
    
    gp_model_module, GPmodel = load_from_module_path(gp_model_path)

    
    df = pd.DataFrame(df)
    import time
    t0 = t00 = time.monotonic()
    gpmodel = GPmodel(df, input_names, output_name, parameter_space_limits, output_deviation_variable, prev_trained_GP_hps,train_method=train_method,train_max_iter=train_max_iter)
    print(f"GPmodel trained in {time.monotonic() - t0} sec")
    t0 = time.monotonic()
    new_pt_dict = gpmodel.identify_new_points(num_new_points)
    print(f"New point ident in {time.monotonic() - t0} sec")
    t0 = time.monotonic()
    average_rmse = gpmodel.perform_rmse(num_RMSE_trials)
    print(f"RMSE calc in {time.monotonic() - t0} sec")

    from ScopeFoundry.cb32_uuid import cb32_uuid
    mfid, _uuid = cb32_uuid()


    #return  new_points, new_predicted_output, new_predicted_uncertainty, current_trained_hps, average_rmse
    return {'recommendation_id':  mfid,
            'elapsed_time': time.monotonic() - t00,
            'new_points': new_pt_dict['new_points'], 
            "new_predicted_output":new_pt_dict['new_predicted_output'], 
            "new_predicted_uncertainty":new_pt_dict['new_predicted_uncertainty'],
            "current_trained_hps":gpmodel.current_trained_hps,
            "average_rmse":average_rmse}