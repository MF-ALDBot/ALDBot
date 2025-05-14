from ScopeFoundry import Measurement
from ScopeFoundry.cb32_uuid import cb32_uuid
import pandas as pd
import json
import numpy as np
from ald_data_processing import process_ald

class ALDRobotRNG(Measurement):
    
    name = 'ald_robot_rng'
    
    def setup(self):
        self.settings.New('campaign_config_file', dtype='file', initial='campaign_config_rng.json')
        
    def setup_figure(self):
        # build UI
        # UI should include: config (readonly?), load_config button, runs_df, diagnostics plot for the current GP
        pass

    def run(self):
        
        # load config
        with open(self.settings['campaign_config_file'], "r") as file:
            config = json.load(file)

        campaign_mfid, campaign_uuid = cb32_uuid()
        
        # Initialize data object
        self.runs_df = pd.DataFrame()

        try:
            print(config['num_runs'])
            campaign_params = self.generate_rng(config)

            for i in range(config['num_runs']):
                print(f"ald_robot run {i} of {config['num_runs']}. Runs DF: {len(self.runs_df)} rows", "="*30)
                if self.interrupt_measurement_called:
                    break
                
                exploration_params = campaign_params.iloc[i].to_dict()
                all_params = config['params'].copy()
                all_params.update(exploration_params)

                new_dataset_fname = self.ald_run(all_params)
                
                result = process_ald(new_dataset_fname)
                # Append result to dataframe, add column in DF of "prior" True
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
        # # deal with special cases
        corrected_params['precursor_purge_time'] = params['ALD_purge_time']
        
        # set parameters
        for param_name, val in corrected_params.items():
            ald_runM.settings[param_name] = val

        # run experiment
        self.run_measurement_and_wait(ald_runM)
        
        # if experiment interrupted or failed, interrupt myself
        '''
        if ald_runM.interrupt_measurement_called:
            print("Interrupting!")
            self.interrupt_measurement_called = True
        '''
        
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

    def generate_rng(self, config):
        num_of_experiments = config['num_runs']
        param_limits_and_step = config['param_limits_and_step']
        experiments = []

        for _ in range(num_of_experiments):
            experiment = {}
            for param_name, (min_val, max_val, step) in param_limits_and_step.items():
                possible_values = np.arange(min_val, max_val + step, step)
                experiment[param_name] = np.random.choice(possible_values)
            
            experiments.append(experiment)

        experiments = pd.DataFrame(experiments)

        return experiments