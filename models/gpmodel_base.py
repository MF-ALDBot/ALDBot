from gpcam import GPOptimizer
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import pandas as pd

class GPModelBase(object):

    #Default Noise Function
    def my_noise(self,x,hps):
        Nk = self.num_of_kernel_hps
        my_s = np.ones(len(x))*hps[Nk]
        noise = np.diag(my_s)
        return noise #my_s
    
    def my_mean(self,x,hps):
        raise NotImplementedError("my_mean needed to implemented")
    
    def __init__(self, df, input_names, output_name,
                               parameter_space_limits,
                               output_deviation_variable=None, # if output_deviation_variable exists, use as y_var, otherwise use a uniform noise hyperparameter to estimate noise
                               prev_trained_GP_hps=None,
                               train_gp_model=True,
                               train_method="global",
                               train_max_iter=4000):
        
        # Define general variables
        self.input_names = input_names
        self.output_name = output_name

        self.df = df
        self.train_method = train_method
        self.train_max_iter = train_max_iter
        
        self.num_of_input_dimensions = Nd = len(self.input_names)
        self.num_of_kernel_hps = Nk = 1+ Nd
        if output_deviation_variable is None:
            self.number_of_noise_hps = Nn = 1
        else:
            self.number_of_noise_hps = Nn = 0

        self.setup()

        Nm = self.number_of_mean_hps

        self.num_hyperparams = Nk + Nn+ Nm

        # Default hyperparameter naming
        self.hyperparams_mapping = [f'hp{i}' for i in range(self.num_hyperparams)]
        self.hyperparams_mapping[0] = 'kernel_variance' # signal variance (1)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[1+i_p] = f'kernel_length_{in_param}' # kernel length for all input dimensions (N)
        if not (output_deviation_variable is None):
            self.hyperparams_mapping[Nk] = 'noise_variance' # noise variance (1)
        for i in range(Nm):
            self.hyperparams_mapping[Nk+Nn+i] = self.mean_hps_names[i] #f'hp_mean_{i}'     

        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Normalize Input

        limits_df = pd.DataFrame([ [limits[0] for limits in parameter_space_limits],   # mins
                                   [limits[1] for limits in parameter_space_limits] ], # maxs
                                 columns=self.input_names)

        # Create the scaler object
        self.scaler = MinMaxScaler()
        self.scaler.fit(limits_df)
        self.df_normalized = df_normalized = df.copy()
        df_normalized[self.input_names] = self.scaler.transform(df[self.input_names])

        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Preparing the data for the GP Model
        
        self.x_data = np.array(df_normalized[self.input_names])
        self.y_data = np.array(df_normalized[self.output_name])

        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Define and fit GP Model

        # Defining the bounds of hyperparameter optimization
        self.bounds = bounds = np.empty((self.num_hyperparams,2))
        # Kernel 3/2 Matern
        y_range_sq = (np.max(self.y_data)-np.min(self.y_data))**2
        bounds[0] = np.array([1e-7*y_range_sq,y_range_sq])   # signal variance      #np.array([1e-7,1])       # 
        bounds[1:Nk] = np.array([0.1,1.5])   # kernel length for all input dimensions
       
        # Noise
        if output_deviation_variable is None:
            bounds[Nk:Nk+Nn] = np.array([1e-6,1])                  
    
        # mean function hyperparamter bounds
        bounds[Nk+Nn:] = self.mean_hps_bounds

        if prev_trained_GP_hps is None:
            self.init_hps =np.mean(bounds,axis=1)
        else:
            self.init_hps = prev_trained_GP_hps

        if output_deviation_variable is None:
            self.gp_noise_function = self.my_noise
            self.y_var = None
        else: 
            self.gp_noise_function = None
            self.y_var = np.array(df_normalized[output_deviation_variable])**2

        self.my_gpo = self.create_gpmodel(self.x_data, self.y_data)
        
        if train_gp_model: # Make it false when you need to calculate the rmse only
            # previous trained hyperparameters implies that no training is required -- as long as data is the same
            # don't use prev_trained_GP_hps if data has changed!!
            if prev_trained_GP_hps is None:
                print("training GP model...")
                self.train_model(self.my_gpo)
                print("GP Training Complete!")
                
        self.current_trained_hps = self.my_gpo.get_hyperparameters

    def create_gpmodel(self, x,y):
        return GPOptimizer(x,y,
                             #gp_kernel_function=my_kernel, 
                             init_hyperparameters = self.init_hps,
                             prior_mean_function=self.my_mean, 
                             noise_function=self.gp_noise_function,
                             noise_variances = self.y_var,
                             )

    def train_model(self, gpmodel):
        gpmodel.train(hyperparameter_bounds = self.bounds, 
                      init_hyperparameters = self.init_hps, 
                      method=self.train_method  , max_iter = self.train_max_iter)
        return gpmodel

    def identify_new_points(self, num_new_points = 1):
            
        # Run Bayesian Optimization to identify new point
        
        # Specifying the domain of search for the Bayesian Optimization. 
        # If you don't want to search in any of the input dimensions, restrict the domain to be [0,0] or any other normalized point of interest
        Optimization_domain = np.tile([0, 1], (self.num_of_input_dimensions, 1))
    
        print("Running Bayesian Optimization...")
        
        # Identifying New Data point
        my_function_evaluation = self.my_gpo.ask(Optimization_domain,n = num_new_points, acquisition_function='variance',max_iter=300, info=False)
        
        new_point_normalized = my_function_evaluation['x']
    
        # Restore the new_point from the normalized domain to the regular domain
        new_points = self.scaler.inverse_transform(new_point_normalized)
    
        # Get the predicted output and uncertainty for the new point
        new_predicted_output = self.my_gpo.posterior_mean(new_point_normalized)["f(x)"]
        new_predicted_uncertainty  = self.my_gpo.posterior_covariance(new_point_normalized,add_noise = True)["v(x)"]
    
        print('New Point Identified!')
        return {'new_points': new_points, 
                "new_predicted_output":new_predicted_output, 
                "new_predicted_uncertainty":new_predicted_uncertainty}

    def hps_to_dict(self, hps=None):
        """Convert hyperparameters array to dictionary using hyperparameters_mapping"""
        if hps is None:
            hps = self.current_trained_hps()
        return {name: value for name, value in zip(self.hyperparams_mapping, hps)}

    def hps_from_dict(self, hps_dict):
        """Convert dictionary of hyperparameters back to array using hyperparameters_mapping"""
        return np.array([hps_dict[name] for name in self.hyperparams_mapping])
    

    def perform_rmse(self, num_RMSE_trials = 0):    
        # Performing RMSE Calculations to estimate prediciton performance for unseen experiments
        # returns a list of RMSE values for each trial
        all_rmse = []
    
        print("Computing RMSE...")
        
        for i in range(num_RMSE_trials):

            #print("RMSE Trial: ", i)
            
            # Split the data into test/train split
            X_train, X_test, y_train, y_test = train_test_split(self.x_data, self.y_data, test_size=0.2)

            # Fit the GP using the training data
            my_gp_for_RMSE = self.create_gpmodel(X_train, y_train)
            self.train_model(my_gp_for_RMSE)
            # Calculate RMSE
            rmse = my_gp_for_RMSE.rmse(X_test,y_test)
            
            all_rmse.append(rmse)
        print("RMSE calculation is done")
        
        return all_rmse
    
    def posterior(self, prediction_points_df, predict_mean = True, predict_cov=True, cov_add_noise=True): # Set predict_cov to False if you don't need uncertainty, this simplifies plotting the 4d cubes
        # ensure we select the required columns in the correct order
        prediction_points_df = prediction_points_df[self.input_names]
        prediction_points_normalized = self.scaler.transform(prediction_points_df)

        # Calculate the predicted mean and uncertainty
        if predict_mean:
            f = self.my_gpo.posterior_mean(prediction_points_normalized)["m(x)"] # note new versions of GPCAM will require "m(x)"
        else:
            f = None

        if predict_cov:
            # Calculate the posterior covariance (uncertainty)
            v2 = self.my_gpo.posterior_covariance(prediction_points_normalized, add_noise=cov_add_noise)["v(x)"]
            v = np.sqrt(v2)
        else:
            v = None
        
        return f,v

    def extract_mean_hps_from_hps(self, hps):
        Nn = self.number_of_noise_hps 
        Nk = self.num_of_kernel_hps        
        return hps[Nk+Nn:]

