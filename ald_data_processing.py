import h5py as h5
import numpy as np
import pandas as pd
import os
from scipy.stats import linregress

def process_ald(data_file_path):

    with h5.File(data_file_path, 'r') as hf:
        thickness_data = hf['measurement/ald_run/thickness_data'][:]
        growth_data = hf['measurement/ald_run/growth_rate'][:]
        settings_attr = hf['measurement/ald_run/settings'].attrs
        settings = {key: settings_attr[key] for key in settings_attr.keys()}
        settings['sample'] = hf['app/settings'].attrs['sample']

        temperature = hf['hardware/productivity_plc/settings'].attrs['PID_SetPoint']

    sample_name = settings['Sample_name']
    cycle_count = settings['Number_of_ALD_cycles']
    folder_path = os.path.dirname(data_file_path)
    filepath_txt = folder_path + '/' + sample_name + '.txt'

    # Import the data from a .txt file
    # ellips_data = pd.read_csv(filepath_txt, sep='\s+', skiprows=10) \s+ seems to be invalid, trying tab-sep instead
    ellips_data = pd.read_csv(filepath_txt, sep='\t', skiprows=10)
    thickness_ellips_data = ellips_data["Thick(nm).2"].to_numpy()
    fit_diff_data = ellips_data["Fit_Diff"].to_numpy()

    #Working with thickness data collected once per ALD cycle (from .h5)

    x = np.linspace(1, len(thickness_data), len(thickness_data))
    slope, _, r_sq, _, _ = linregress(x[10:], thickness_data[10:])
    growth_data_cut = growth_data[9:]
    growth_data_filtered = growth_data_cut[growth_data_cut > 0.001] # changed from > 0.1 for Al2O3
    dep_rate_fit = slope if growth_data_filtered.size > 0 else 0  # preventing negative growth rates
    #dep_rate_mean = np.mean(growth_data_filtered)
    #dep_rate_deviation = np.std(growth_data_filtered)
    dep_rate_mean = np.mean(growth_data_filtered) if growth_data_filtered.size > 0 else 0
    dep_rate_deviation = np.std(growth_data_filtered) if growth_data_filtered.size > 2 else 1e-6
    thickness_start = thickness_ellips_data[0]
    thickness_end = thickness_ellips_data[-1]
    gpc_easy = (thickness_end - thickness_start)/cycle_count

    fit_diff_mean = np.mean(fit_diff_data)
    fit_diff_std = np.std(fit_diff_data)
    fit_diff_variation = fit_diff_std/fit_diff_mean*100

    print("Thickness line slope = {:.2f} nm/cycle with fitting R_sq = {:.4f}".format(dep_rate_fit, r_sq))
    print("Mean deposition rate = {:.2f} +- {:.2f} nm/cycle".format(dep_rate_mean, dep_rate_deviation))

    # settings['total_MO_purge'] = settings['ALD_purge_time'] + settings['precursor_purge_time']
    settings['Initial_thickness'] = thickness_start
    settings['Temperature'] = temperature
    settings['dep_rate_fit'] = dep_rate_fit
    settings['dep_rate_mean'] = dep_rate_mean
    settings['dep_rate_direct'] = gpc_easy
    settings['dep_rate_deviation'] = dep_rate_deviation
    settings['fit_diff_variation'] = fit_diff_variation


    settings_to_write = pd.DataFrame(settings, index=[settings['run_id']])

    return settings_to_write
