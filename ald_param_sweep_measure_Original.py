from ScopeFoundry import Measurement
from ScopeFoundry.cb32_uuid import cb32_uuid
import pandas as pd
import json
import numpy as np
from ald_data_processing import process_ald

class ALDRobotSweep(Measurement):
    
    name = 'ald_robot_sweep'
    
    def setup(self):
        self.settings.New('campaign_config_file', dtype='file', initial='campaign_config_sweep.json')
        
    def setup_figure(self):
        # build UI
        pass

    def run(self):
        
        # Load config
        with open(self.settings['campaign_config_file'], "r") as file:
            config = json.load(file)

        campaign_mfid, campaign_uuid = cb32_uuid()
        
        # Initialize data object
        self.runs_df = pd.DataFrame()

        try:
            sweep_param = config['sweep_param'][0]
            param_limits = config['param_limits'][sweep_param]
            num_points = config['num_points']
            
            sweep_values = np.linspace(param_limits[0], param_limits[1], num_points)

            # Reorder the sweep values to start from the middle and go outward
            middle_index = num_points // 2
            reordered_indices = []
        
            # If num_points is odd, start with the exact middle
            if num_points % 2 == 1:
                reordered_indices.append(middle_index)
                left = middle_index - 1
                right = middle_index + 1
            else:
                # If num_points is even, start with the two middle points
                left = middle_index - 1
                right = middle_index
            
            # Alternate between left and right sides until all points are covered
            while left >= 0 or right < num_points:
                if left >= 0:
                    reordered_indices.append(left)
                    left -= 1
                if right < num_points:
                    reordered_indices.append(right)
                    right += 1
            
            # Create the reordered sweep values
            reordered_sweep_values = [sweep_values[i] for i in reordered_indices]
            
            for i, value in enumerate(reordered_sweep_values):
                print(f"ald_robot run {i+1} of {num_points}. Runs DF: {len(self.runs_df)} rows", "="*30)
                if self.interrupt_measurement_called:
                    break
                
                all_params = config['params'].copy()
                all_params[sweep_param] = value
                
                new_dataset_fname = self.ald_run(all_params)
                
                result = process_ald(new_dataset_fname)
                result['prior'] = False
                self.runs_df = pd.concat([self.runs_df, result], ignore_index=True)   
        finally:
            CI = self.campaign_info = {}
            CI['config'] = config
            CI['runs'] = self.runs_df.to_dict(orient='dict')
            with open(f"{campaign_mfid}_aldbot_campaign_output.json", 'w') as fp:
                class NumpyArrayEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, np.ndarray):
                            return obj.tolist()
                        return json.JSONEncoder.default(self, obj)

                json.dump(CI, fp, cls=NumpyArrayEncoder, indent=2)

    def ald_run(self, params):
        """blocking run of ald_run measurement with new parameters
            takes in suggested params dictionary to update for the new run
        """
        ald_runM = self.app.measurements['ald_run']
        
        # make sure ald_run is not currently running
        assert 'stop' in ald_runM.settings['run_state'] 

        corrected_params = params.copy()
        # deal with special cases
        corrected_params['precursor_purge_time'] = params['ALD_purge_time']
        
        # set parameters
        for param_name, val in corrected_params.items():
            ald_runM.settings[param_name] = val
        
        # run experiment
        self.run_measurement_and_wait(ald_runM)
        
        # return filename of new dataset
        return ald_runM.h5_filename
    
    def run_measurement_and_wait(self, M):
        # start measurement
        M.interrupt_measurement_called = False
        M.start()
        import time
        time.sleep(0.1)
        self.log.info('Measurement started {}'.format(M.name))
        
        # wait till complete
        while M.is_measuring():
            if self.interrupt_measurement_called:
                print("Interrupting!(2)")
                M.interrupt()
            time.sleep(0.1)
        self.log.info('Measurement complete {}'.format(M.name))
