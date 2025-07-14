from .gpmodel_base import GPModelBase
import numpy as np

def piecewise_nd_asymmetric_ellipsoid(coords, center, radii, constant=10, slopes_pos=None, slopes_neg=None):
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
        
        values[outside_mask & pos_mask] += slopes_pos[dim] * coords[outside_mask & pos_mask, dim]
        values[outside_mask & neg_mask] += slopes_neg[dim] * coords[outside_mask & neg_mask, dim]

    # Apply the smooth transition factor

    values[outside_mask] = constant + (values[outside_mask] - constant) * (1 - 1/r[outside_mask])

    return values

class GPModelALDWindow(GPModelBase):
    # Model includes prior mean function for spheroidal ALD window within input domain
    # GP Model Components
    # hyper parameters 
    #[ kernel variance, kernel dims (N), noise (1), mean_func_hps (1 + 4N)]

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
        mean_hps = self.extract_mean_hps_from_hps(hps)

        mean = piecewise_nd_asymmetric_ellipsoid(coords=x, 
                                                 constant= mean_hps[0], # mean value at center point (1)
                                                 center=mean_hps[1:1+Nd], # center point position for all input dimensions         # center point (N)
                                                 radii=mean_hps[1+Nd:1+2*Nd], # radius of flat window for each input dimension         #  (N)
                                                 slopes_pos=mean_hps[1+2*Nd:1+3*Nd], # pos slope for each input dimension         #  (N)
                                                 slopes_neg=mean_hps[1+3*Nd:1+4*Nd]) # neg slope for each input dimension         #  (N)

        
        return mean
    
    def setup(self):
        Nd = self.num_of_input_dimensions
        self.number_of_mean_hps = Nm = 1+4*Nd

        self.mean_hps_names = ['']*Nm
        self.mean_hps_names[0] = 'mean_center_value' # mean value at center point (1)
        for i_p, in_param in enumerate(self.input_names):
            self.mean_hps_names[1+i_p] = f'mean_center_pos_{in_param}' # center point position for all input dimensions         # center point (N)
        for i_p, in_param in enumerate(self.input_names):
            self.mean_hps_names[1+Nd+i_p] = f'mean_radius_{in_param}' # radius of flat window for each input dimension         #  (N)
        for i_p, in_param in enumerate(self.input_names):
            self.mean_hps_names[1+2*Nd+i_p] = f'mean_slope_pos_{in_param}' # pos slope for each input dimension         #  (N)
        for i_p, in_param in enumerate(self.input_names):
            self.mean_hps_names[1+3*Nd+i_p] = f'mean_slope_neg_{in_param}' # neg slope for each input dimension         #  (N)

        y_data = self.df[self.output_name]
        # Mean function hyperparameter bounds
        self.mean_hps_bounds = np.zeros(shape=(self.number_of_mean_hps,2),dtype=float)
        # constant
        self.mean_hps_bounds[0] = np.array([np.min(y_data),np.max(y_data)])
        # center(s) # in normalized input units
        self.mean_hps_bounds[1:1+Nd] = np.array([0,1])
        # radii # in normalized input units
        self.mean_hps_bounds[1+Nd:1+2*Nd] = np.array([0,2]) #was [0,1]
        # slopes_pos
        max_slope = (np.max(y_data) - np.min(y_data))* 5/ 1.0  # 1.0 is scaled range of input params, 3.0 is a arbitrary safety factor, initially was 3, changed to 100, then to 20, then to 5
        self.mean_hps_bounds[1+2*Nd:1+3*Nd] = np.array([-max_slope, +max_slope]) # np.array([0,0])
        # bounds[Nk+Nn+1+2*Nd] = np.array([0,0])
        # bounds[Nk+Nn+1+3*Nd-1] = np.array([0,0])
        # slopes_neg
        self.mean_hps_bounds[1+3*Nd:1+4*Nd] =  np.array([-max_slope, +max_slope]) # np.array([0,0]) #

