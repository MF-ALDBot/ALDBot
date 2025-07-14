from .gpmodel_base import GPModelBase
import numpy as np


class GPModelConstMean(GPModelBase):

    def my_mean(self,x,hps):
        mean_hps = self.extract_mean_hps_from_hps(hps)
        mean = np.ones(len(x))*mean_hps[0]
        return mean
    
    def setup(self):
        self.number_of_mean_hps = 1 
        self.mean_hps_bounds = np.zeros(shape=(self.number_of_mean_hps,2),dtype=float)
        self.mean_hps_bounds[0] = np.array([np.min(self.df[self.output_name]),np.max(self.df[self.output_name])])
        self.mean_hps_names = ["mean_value"]
