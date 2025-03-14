from ScopeFoundry import Measurement
from ScopeFoundry.cb32_uuid import cb32_uuid
import pandas as pd
import json
from bayesian_optimizer import Get_New_Points_With_GP
from ald_data_processing import process_ald
import glob


class ALDRobot(Measurement):
    
    name = 'ald_robot'
    
    def setup(self):
        self.settings.New('campaign_config_file', dtype='file',initial='campaign_config.json')
        
    def setup_figure(self):
        # build UI
        # UI should include: config (readonly?), load_config button, runs_df, diagnostics plot for the current GP
        pass

    def run(self):
        
        # load config
        with open(self.settings['campaign_config_file'], "r") as file:
            config = C = json.load(file)

        campaign_mfid, campaign_uuid = cb32_uuid()
        # config should have the following:
        #    list of prior runs (dataset_ids? or filenames?)
        #    number of runs
        #    preprocessor args
        #    GP hyperparameter info
        #        output_param to optimize (eg thickness)
        #        list of modeled params
        #        list of variable params
        #        limits of params
        #
        
        # create data object
        

        # TODO use self.runs_df for live access to table
        self.runs_df = pd.DataFrame()
        # | Run ID | sample_id | raw_param1 | ... | raw_param N | prior (bool) | output_param_1 | output_param_2 |
        
        
        # Load prior datasets and preprocess
        # look for prior datasets in directory:
        for fname in glob.glob(C['prior_datasets_dir']+"/*/*.h5"):
            print(fname)
            result = process_ald(fname)
            #append result to dataframe, add column in DF of "prior" True
            result['is_prior'] = [True]
            self.runs_df = pd.concat([self.runs_df, result], ignore_index=True)   

        optimizer_results = []
        
        try:
            print(C['num_runs'])
            for i in range(C['num_runs']):
                print(f"ald_robot run {i} of {C['num_runs']}. Runs DF: {len(self.runs_df)} rows", "="*30)
                if self.interrupt_measurement_called:
                    break
                
                parameter_space_limits = []
                for param in C['modeled_params']:
                    parameter_space_limits.append(C['param_limits'][param])
                
                
                # GP = gp_results = Get_New_Points_With_GP(df=self.runs_df, 
                #                        input_names=C['modeled_params'], 
                #                        output_name=C['model_output_param'],
                #                        parameter_space_limits=parameter_space_limits,
                #                        num_new_points=1,
                #                        num_RMSE_trials=C['num_RMSE_trials'])#, prev_trained_GP_hps)
                
                GP = gp_results = self.submit_zmq_job_and_wait(
                                       "Get_New_Points_With_GP",
                                       df=self.runs_df.to_dict(), 
                                       input_names=C['modeled_params'], 
                                       output_name=C['model_output_param'],
                                       parameter_space_limits=parameter_space_limits,
                                       num_new_points=1,
                                       num_RMSE_trials=C['num_RMSE_trials'])
                    
                optimizer_results.append(gp_results)
                import numpy as np
                new_point_dict = {name:np.array(GP['new_points'])[0,:][i] for i,name in enumerate(C['modeled_params'])}

                def subset_dict(original_dict, keys):
                    return {k: original_dict[k] for k in keys if k in original_dict}

                new_exploration_params = subset_dict(new_point_dict,keys=C['exploration_params'])

                all_params = C['params'].copy()
                all_params.update(new_exploration_params)

                new_dataset_fname = self.ald_run(all_params)
                
                result = process_ald(new_dataset_fname)
                #append result to dataframe, add column in DF of "prior" True
                result['is_prior'] = [False]
                result['from_recommendation_id'] = [gp_results['recommendation_id']]
                self.runs_df = pd.concat([self.runs_df, result], ignore_index=True)   
        finally:
            CI = self.campaign_info = {}
            CI['config'] = config
            CI['runs'] = self.runs_df.to_dict(orient='dict')
            CI['optimizer'] = optimizer_results
            with open(f"{campaign_mfid}_aldbot_campaign_output.json", 'w') as fp:
                import numpy as np
                class NumpyArrayEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, np.ndarray):
                            return obj.tolist()
                        return json.JSONEncoder.default(self, obj)

                json.dump(CI,fp, cls=NumpyArrayEncoder, indent=2 )
            # save data
            #    include campaign id
            #    timestamps of runs
            #    runs_df
            #    suggested_params
            #    GP diagnostics
            #    GP model?
    
    def ald_run(self,params):
        """blocking run of ald_run measurement with new parameters
            takes in suggested params dictionary to update for the new run
        """
        ald_runM = self.app.measurements['ald_run']
        
        # make sure ald_run is not currently running
        assert 'stop' in ald_runM.settings['run_state'] 

        corrected_params = params.copy()
        # # deal with special cases
        # corrected_params['precursor_purge_time'] = 0.5*params['total_MO_purge']
        # corrected_params['ALD_purge_time'] = 0.5*params['total_MO_purge']
        # del corrected_params['total_MO_purge']
        
        # set parameters
        for param_name, val in corrected_params.items():
            ald_runM.settings[param_name] = val

        # run experiement
        self.run_measurement_and_wait(ald_runM)
        
        # if experiment interupted of failed, interrupt myself
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
        while( M.is_measuring()):
            if self.interrupt_measurement_called:
                print("Interrupting!(2)")
                M.interrupt()
            time.sleep(0.1)
        self.log.info('Measurement complete {}'.format(M.name))



    def submit_zmq_job_and_wait(self, job_name, **kwargs):
        print("submit_zmq_job_and_wait")
        import zmq
        import zmq.auth
        import json
        import os
        import sys

        # Load client + server keys
        certs_dir = "zmq_certs"
        client_public_file = os.path.join(certs_dir, "client.pub")
        client_secret_file = os.path.join(certs_dir, "client.key_secret")
        server_public_file = os.path.join(certs_dir, "server.pub")
    
        server_public_file = os.path.join(certs_dir, "server.key")
        server_public, _ = zmq.auth.load_certificate(server_public_file)
    
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    
        context = zmq.Context.instance()
    
        # 1) REQ socket => connect to server for job submission
        req_socket = context.socket(zmq.REQ)
        # req_socket.setsockopt(zmq.CURVE_SECRETKEY, client_secret)
        # req_socket.setsockopt(zmq.CURVE_PUBLICKEY, client_public)
        # req_socket.setsockopt(zmq.CURVE_SERVERKEY, server_public)    
        req_socket.setsockopt(zmq.RCVTIMEO, 1000)
        req_socket.connect("tcp://esbstudio.dhcp.lbl.gov:5555")
            
        # 2) SUB socket => subscribe to status updates
        sub_socket = context.socket(zmq.SUB)
        # sub_socket.setsockopt(zmq.CURVE_SECRETKEY, client_secret)
        # sub_socket.setsockopt(zmq.CURVE_PUBLICKEY, client_public)
        # sub_socket.setsockopt(zmq.CURVE_SERVERKEY, server_public)
        sub_socket.connect("tcp://esbstudio.dhcp.lbl.gov:5556")
    
        # We subscribe to everything, then filter the job_id in code.
        # Alternatively, you can use a topic-based scheme.
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
        print("submit_zmq_job_and_2")

        # Submit a job
        request = {
            "method": job_name,
            "params": kwargs
        }
        print(f"REQ {request}")
        req_socket.send_string(json.dumps(request))
        reply_raw = req_socket.recv_string()
        reply = json.loads(reply_raw)
        print("reply")
    
        if reply["status"] != "ok":
            raise IOError(f"ERROR: {reply.get('error')}")
    
        job_id = reply["job_id"]
        print(f"[Client] Submitted job. job_id = {job_id}")
    
        poller = zmq.Poller()
        poller.register(sub_socket, zmq.POLLIN)

        # Listen for PUB updates until job is done
        print("[Client] Waiting for status updates...")
        while True:
            if self.interrupt_measurement_called:
                break
            
            #print("Poll",  poller.poll(timeout=10))
            
            def msg_avail():
                socks = dict(poller.poll(timeout=10))
                if sub_socket in socks and socks[sub_socket] == zmq.POLLIN:
                    return True
                else: return False

            # skip rest of no message ready
            if not msg_avail():
                if self.interrupt_measurement_called:
                    break
                continue
            
            # if there is a message, receive it and return response
            msg = sub_socket.recv_string()
            update = json.loads(msg)
    
            # If you're receiving many updates, you might filter by job_id here
            if update["job_id"] == job_id:
                print(f"[Status] job_id={update['job_id']} ", end="")
                print(f"progress={update['progress']} ", end="")
                print(f"done={update['done']}")
    
                if update["done"]:
                    print("[Client] Job is complete. Exiting.")
                    return update['response']

        
            