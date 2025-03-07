import numpy as np
from gpcam import GPOptimizer
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split



class GPmodel(object):
    
    
        # GP Model Components
       
    # Noise Function
    def my_noise(self,x,hps):
        my_s = np.ones(len(x))*hps[self.num_of_input_dimensions+1]
        noise = np.diag(my_s)
        return noise

    # Prior Mean Function
    def my_mean(self,x,hps):
        mean = np.ones(len(x))*hps[self.num_of_input_dimensions+2]
        return mean

    def __init__(self, df, input_names, output_name,
                               parameter_space_limits,
                               prev_trained_GP_hps=None):
        
        # TODO: Make use of prev_trained_GP_hps
        
        # Define general variables
        input_variables = input_names
        output_variable = output_name
        
        self.num_of_input_dimensions = num_of_input_dimensions = len(input_variables)
        
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Normalize Input
        
        # Create the scaler object
        self.scaler = MinMaxScaler()
    
        # Fit the scaler to your custom range
        self.scaler.fit(np.array(parameter_space_limits).T)
    
        # Transform the selected columns
        df_normalized = df.copy()
        df_normalized[input_variables] = self.scaler.transform(df[input_variables])
        
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Preparing the data for the GP Model
        
        self.x_data = np.array(df_normalized[input_variables])
        self.y_data = np.array(df_normalized[output_variable])
    
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Define and fit GP Model
        
        # see self.my_mean, self.my_noise
        
    
        # Fit the GP Model
    
        # Defining the bounds of hyperparameter optimization
        self.bounds = bounds = np.empty((num_of_input_dimensions+3,2))
        # Kernel Sq Exp 
        bounds[0] = np.array([1e-4,10e1])                            
        bounds[1:num_of_input_dimensions+1] = np.array([0.02,1.5])                             
    
        # Noise
        bounds[num_of_input_dimensions+1] = np.array([1e-6,np.var(self.y_data)])                     
    
        # Mean
        bounds[num_of_input_dimensions+2] = np.array([np.min(self.y_data),np.max(self.y_data)])                             
    
        
        if prev_trained_GP_hps is None:
            self.init_hps =np.mean(bounds,axis=1)
        else:
            self.init_hps = prev_trained_GP_hps
    
        self.my_gpo = GPOptimizer(self.x_data,self.y_data,
                             #hyperparameter_bounds = bounds,
                             #gp_kernel_function=my_kernel, 
                             init_hyperparameters = self.init_hps,
                             gp_mean_function=self.my_mean, 
                             gp_noise_function=self.my_noise)
    
        # previous trained hyperparameters implies that no training is required -- as long as data is the same
        # don't use prev_trained_GP_hps if data has changed!!
        if prev_trained_GP_hps is None:
            print("training GP model...")
            self.my_gpo.train(hyperparameter_bounds = bounds, init_hyperparameters = self.init_hps, method='global', max_iter = 4000)
            
        self.current_trained_hps = self.my_gpo.hyperparameters
        
        print("GP Training Complete!")
        
    def identify_new_points(self, num_new_points = 1):
            
        #Bayesian Optimization to identify new point
        
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Run Bayesian Optimization to identify new point
        #num_of_input_dimensions = self.my_gpo.x_data[1]
        
        # Specifying the domain of search for the Bayesian Optimization. 
        # If you don't want to search in any of the input dimensions, restrict the domain to be [0,0] or any other normalized point of interest
        Optimization_domain = np.tile([0, 1], (self.num_of_input_dimensions, 1))
    
        print("Running Bayesian Optimization...")
        
        # Identifying New Data point
        my_function_evaluation = self.my_gpo.ask(Optimization_domain,n = num_new_points, acquisition_function='variance',max_iter=300, info=False)
        
        new_point_normalized = my_function_evaluation['x']
    
        # Restore the new_point from the normalized domain to the regular domain
        new_points = self.scaler.inverse_transform(new_point_normalized)
    
    
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Calculating information gained from the currently added new point
        
    #     if prev_trained_GP_hps.size != 0:
    
    #         print("Calculating information gain from new data...")
            
    #         # Assuming that the number of added new points from previous run is num_new_points
            
    #         my_gpo_previous = GPOptimizer(x_data[:-num_new_points,:],y_data[:-num_new_points],
    #                                  init_hyperparameters = prev_trained_GP_hps,  
    #                                  gp_mean_function=my_mean, 
    #                                  gp_noise_function=my_noise)
    
    #         ###########################################################################
    
    #         # Defining the parameter space to calculate the KL divergence between my_gpo_previous and my_gpo
            
    #         # Define the grid size and range
    #         n = 5 # Number of points per dimension
    #         variable_range = (0, 1)  # All variables have the same range [0, 1]
    
    #         # Create a design space for each dimension
    #         space = np.linspace(variable_range[0], variable_range[1], n)
    
    #         # Create a meshgrid for the given number of dimensions
    #         meshgrid = np.meshgrid(*[space] * num_of_input_dimensions)
    
    #         # Reshape the arrays into a 2D array
    #         my_space_total_normalized = np.vstack([grid.reshape(-1) for grid in meshgrid]).T
    
    #         ###########################################################################
    #         # Calculating the KL
    
    #         my_posterior_mean_GP1 = my_gpo_previous.posterior_mean(my_space_total_normalized)["f(x)"]
    #         my_posterior_covariance_GP1 = np.abs(my_gpo_previous.posterior_covariance(my_space_total_normalized, add_noise=False)['S'] )+ 1 * np.eye(len(my_space_total_normalized))
    
    #         my_posterior_mean_GP2 = my_gpo.posterior_mean(my_space_total_normalized)["f(x)"]
    #         my_posterior_covariance_GP2 = np.abs(my_gpo.posterior_covariance(my_space_total_normalized, add_noise=False)['S']) + 1 * np.eye(len(my_space_total_normalized))
    
    #         information_gain = my_gpo.kl_div(my_posterior_mean_GP1, my_posterior_mean_GP2, my_posterior_covariance_GP1, my_posterior_covariance_GP2)            
    
    
    #     else:
            
    #         print("This is the initial run, calculating information gain is not possible")
        
    #         information_gain = 0
    
        new_predicted_output = self.my_gpo.posterior_mean(new_point_normalized)["f(x)"]
        new_predicted_uncertainty  = self.my_gpo.posterior_covariance(new_point_normalized,add_noise = True)["v(x)"]
    
        print('New Point Identified!')
        return {'new_points': new_points, 
                "new_predicted_output":new_predicted_output, 
                "new_predicted_uncertainty":new_predicted_uncertainty}

    

    def perform_rmse(self, num_RMSE_trials = 0,):    
        # Performing RMSE Calculations to estimate prediciton performance for unseen experiments
    
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Performing RMSE Calculations to estimate prediciton performance for unseen experiments
    
        all_rmse = []
    
        print("Computing RMSE...")
        
        if num_RMSE_trials > 0:
            
            for _ in range(num_RMSE_trials):
                
                # Split the data into test/train split
                X_train, X_test, y_train, y_test = train_test_split(self.x_data, self.y_data, test_size=0.2)
    
                # Fit the GP using the training data
                my_gp_for_RMSE = GPOptimizer(X_train, y_train,
                                 #hyperparameter_bounds = bounds,
                                 #gp_kernel_function=my_kernel, 
                                 init_hyperparameters = self.init_hps,
                                 gp_mean_function=self.my_mean, 
                                 gp_noise_function=self.my_noise)
    
                my_gp_for_RMSE.train(hyperparameter_bounds = self.bounds, init_hyperparameters = self.init_hps, method='global', max_iter = 4000)
    
                # Calculate RMSE
                rmse = my_gp_for_RMSE.rmse(X_test,y_test)
                
                all_rmse.append(rmse)
    
            # Calculate average RMSE after the for loop ends
            average_rmse = np.mean(all_rmse)
    
        else:
            average_rmse = 0
    
        print("RMSE calculation is done")
        return average_rmse

def Get_New_Points_With_GP(df, input_names, output_name,
                           parameter_space_limits,
                           num_new_points =  1,
                           num_RMSE_trials = 0,
                           prev_trained_GP_hps=None):

    '''
    Input: 
        df:                  nx(d+1) A data frame that includes all collected experimental data. n is number of experiments
        input_names:         d list of the names of the d input variables
        output_name:         column name of output variable that GP will predict
        parameter_space:     dx2 numpy array that has the limits of the parameter space for all dimensions of length d.
        num_new_points:      positive integer specifying the number of new point to find by the Bayesian Optimization
        num_RMSE_trials:     positive integer specifying the number of trials for cross-validation, if 0, cross-validation is skipped
        prev_trained_GP_hps: trained hyperparameters from the previous loop, if not given function assumes first run so information gain will be skipped
        
    Outputs a dictionary with the following keys:
        new_points:                 New points outputed from the Bayesian optimization
        new_predicted_output:      Predicted mean at the new point
        new_predicted_uncertainty: Predicted uncertainty at the new point
        current_trained_hps:       Trained GP hyperparameters
        average_rmse:              Mean RMSE from the cross validation
        
    ........................ Code prepared by Maher Alghalayini on February 12, 2025 ........................
    
    '''
    import time
    t0 = t00 = time.monotonic()
    gpmodel = GPmodel(df, input_names, output_name, parameter_space_limits, prev_trained_GP_hps)
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