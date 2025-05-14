import numpy as np
from gpcam import GPOptimizer
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split



class GPmodelALDWindow_dev(object):
    
    def piecewise_nd_asymmetric_ellipsoid(self, coords, center, radii, constant=10, slopes_pos=None, slopes_neg=None):
        """
        Generalized piecewise function in n-dimensional space with asymmetric slopes and ellipsoidal boundary.
        Inside an n-dimensional ellipsoid, the function is constant.
        Outside, it transitions to linear functions with independent slopes above and below center.

        Parameters:
        coords (ndarray): An (N, D) array where N is the number of points and D is the dimensionality.
        radii (array-like): Radii for each dimension, defining the ellipsoid.
        constant (float): Constant value inside the ellipsoid.
        slopes_pos (ndarray): Slopes for positive directions in each dimension.
        slopes_neg (ndarray): Slopes for negative directions in each dimension.

        Returns:
        ndarray: Function values for each point in coords.
        """
        coords = np.asarray(coords, dtype=np.float64) - center
        radii = np.asarray(radii, dtype=np.float64)
        n_dims = coords.shape[1]
        
        if slopes_pos is None:
            slopes_pos = np.ones(n_dims, dtype=np.float64)
        if slopes_neg is None:
            slopes_neg = np.ones(n_dims, dtype=np.float64)
        
        slopes_pos = np.asarray(slopes_pos, dtype=np.float64)
        slopes_neg = np.asarray(slopes_neg, dtype=np.float64)

        # Compute the normalized distance from the origin for each point
        normalized_coords = coords / radii
        r = np.linalg.norm(normalized_coords, axis=1)

        # Initialize the output array as float64
        values = np.full(coords.shape[0], constant, dtype=np.float64)

        # Mask for points outside the ellipsoid
        outside_mask = r > 1

        # Compute the linear terms for each dimension
        for dim in range(n_dims):
            pos_mask = coords[:, dim] > 0
            neg_mask = coords[:, dim] <= 0
            
            values[outside_mask & pos_mask] += slopes_pos[dim] *  coords[outside_mask & pos_mask, dim]
            values[outside_mask & neg_mask] += slopes_neg[dim] * coords[outside_mask & neg_mask, dim]

        # Apply the smooth transition factor

        values[outside_mask] = constant + (values[outside_mask] - constant) * (1 - 1/r[outside_mask])

        return values
    
    
    # GP Model Components
       
    # Noise Function
    # def my_noise(self,x,hps):
    #     Nk = self.num_of_kernel_hps
    #     my_s = np.ones(len(x))*hps[Nk]
    #     noise = np.diag(my_s)
    #     return noise

    # Prior Mean Function
    def my_mean(self,x,hps):
        # Hyperparameters for spheriodal ALD window in N-dim space

        # mean value at center point (1)
        # center point (N)
        # radius in each parameter (N)
        # high side slope outside sphere for each parameter (N)
        # low side slope outside sphere for each parameter (N)
        # central slope inside sphere for each parameter (N) # SKIP FOR NOW

        Nd = self.num_of_input_dimensions
        Nk = self.num_of_kernel_hps
        Nn = self.number_of_noise_hps

        mean = self.piecewise_nd_asymmetric_ellipsoid(coords=x, 
                                                 constant= hps[Nk+Nn],
                                                 center=hps[Nk+Nn+1:Nk+Nn+1+Nd],
                                                 radii=hps[Nk+Nn+1+Nd:Nk+Nn+1+2*Nd],
                                                 slopes_pos=hps[Nk+Nn+1+2*Nd:Nk+Nn+1+3*Nd],
                                                 slopes_neg=hps[Nk+Nn+1+3*Nd:Nk+Nn+1+4*Nd])
        
        return mean

    def __init__(self, df, input_names, output_name,
                               parameter_space_limits,
                               output_deviation_variable=None,
                               prev_trained_GP_hps=None):
        
        # TODO: Make use of prev_trained_GP_hps
        
        # Define general variables
        input_variables = self.input_names = input_names
        output_variable = self.output_name = output_name

        
        self.num_of_input_dimensions = Nd = num_of_input_dimensions = len(input_variables)
        self.num_of_kernel_hps = Nk = 1+ Nd
        self.number_of_noise_hps = Nn = 0
        self.number_of_mean_hps = Nm = 1+4*Nd
        
        self.num_hyperparams = Nk + Nn+ Nm # self.num_of_input_dimensions*5 + 3 #5N+3

        self.hyperparams_mapping = ['hp{i}' for i in range(self.num_hyperparams)]
        self.hyperparams_mapping[0] = 'kernel_variance' # signal variance (1)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[1+i_p] = f'kernel_length_{in_param}' # kernel length for all input dimensions (N)
        
        # No Noise function for now
        
        self.hyperparams_mapping[Nk+Nn] = 'mean_center_value' # mean value at center point (1)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[Nk+Nn+1+i_p] = f'mean_center_pos_{in_param}' # center point position for all input dimensions         # center point (N)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[Nk+Nn+1+Nd+i_p] = f'mean_radius_{in_param}' # radius of flat window for each input dimension         #  (N)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[Nk+Nn+1+2*Nd+i_p] = f'mean_slope_pos_{in_param}' # pos slope for each input dimension         #  (N)
        for i_p, in_param in enumerate(self.input_names):
            self.hyperparams_mapping[Nk+Nn+1+3*Nd+i_p] = f'mean_slope_neg_{in_param}' # neg slope for each input dimension         #  (N)         # center point (N)

        # radius in each parameter (N)
        # high side slope outside sphere for each parameter (N)
        # low side slope outside sphere for each parameter (N)

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
        if output_deviation_variable is None:
            self.y_var = np.ones_like(self.y_data, dtype=np.float64)*abs(np.mean(self.y_data))/100
        else: 
            self.y_var = np.array(df_normalized[output_deviation_variable])**2

    
        ###########################################################################
        ###########################################################################
        ###########################################################################
        # Define and fit GP Model
        
        # see self.my_mean, self.my_noise
        
    
        # Fit the GP Model
    
        # Defining the bounds of hyperparameter optimization
        Nd = num_of_input_dimensions
        self.bounds = bounds = np.empty((self.num_hyperparams,2))
        # Kernel Sq Exp 
        y_range_sq = (np.max(self.y_data)-np.min(self.y_data))**2
        bounds[0] = np.array([1e-7*y_range_sq,y_range_sq])   # signal variance      
        bounds[1:Nk] = np.array([0.02,1.5])   # kernel length for all input dimensions
        # Noise
        if Nn!=0: bounds[Nk:Nk+Nn] = np.array([0,0]) #1e-6,np.var(self.y_data)])                     
    
        # Mean function hyperparameter bounds
        #bounds[num_of_input_dimensions+2] = np.array([np.min(self.y_data),np.max(self.y_data)])                             
        # constant
        bounds[Nk+Nn] = np.array([np.min(self.y_data),np.max(self.y_data)])
        # center
        bounds[Nk+Nn+1:Nk+Nn+1+Nd] = np.array([0,1])
        # radii
        bounds[Nk+Nn+1+Nd:Nk+Nn+1+2*Nd] = np.array([0,2]) #was [0,1]
        # slopes_pos
        max_slope = (np.max(self.y_data) - np.min(self.y_data))/ 1.0 * 20 # 1.0 is scaled range of input params, 3.0 is a arbitrary safety factor, initially was 3, changed to 100, then to 20
        bounds[Nk+Nn+1+2*Nd:Nk+Nn+1+3*Nd] = np.array([-max_slope, +max_slope])
        # slopes_neg
        bounds[Nk+Nn+1+3*Nd:Nk+Nn+1+4*Nd] = np.array([-max_slope, +max_slope])

        if prev_trained_GP_hps is None:
            self.init_hps =np.mean(bounds,axis=1)
        else:
            self.init_hps = prev_trained_GP_hps
    
        self.my_gpo = GPOptimizer(self.x_data,self.y_data,
                             #hyperparameter_bounds = bounds,
                             # Currently using default kernel, he default is a stationary anisotropic kernel:
                             # anisotropic Matern kernel with automatic relevance determination (ARD)
                             #gp_kernel_function=my_kernel, 
                             init_hyperparameters = self.init_hps,
                             gp_mean_function=self.my_mean, 
                             #gp_noise_function=self.my_noise
                             noise_variances = self.y_var)
    
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
    
    
    
        new_predicted_output = self.my_gpo.posterior_mean(new_point_normalized)["f(x)"]
        new_predicted_uncertainty  = self.my_gpo.posterior_covariance(new_point_normalized,add_noise = True)["v(x)"]
    
        print('New Point Identified!')
        return {'new_points': new_points, 
                "new_predicted_output":new_predicted_output, 
                "new_predicted_uncertainty":new_predicted_uncertainty}

    

    def hps_to_dict(self, hps=None):
        """Convert hyperparameters array to dictionary using hyperparameters_mapping"""
        if hps is None:
            hps = self.current_trained_hps
        return {name: value for name, value in zip(self.hyperparams_mapping, hps)}

    def hps_from_dict(self, hps_dict):
        """Convert dictionary of hyperparameters back to array using hyperparameters_mapping"""
        return np.array([hps_dict[name] for name in self.hyperparams_mapping])

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
                                 #gp_noise_function=self.my_noise
                                 noise_variances = self.y_var)
                                 
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

def Get_New_Points_With_GP_ALD(df, input_names, output_name,
                           parameter_space_limits,
                           output_deviation_variable,
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
    df = pd.DataFrame(df)
    import time
    t0 = t00 = time.monotonic()
    gpmodel = GPmodelALDWindow_dev(df, input_names, output_name, parameter_space_limits, output_deviation_variable,  prev_trained_GP_hps)
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