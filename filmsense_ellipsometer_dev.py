'''
Created on Nov 1, 2024

@author: Sasha Razumtcev    <arazumtcev@lbl.gov>
'''
import socket
import struct
import select
import time


class FilmSense_Ellipsometer(object):
    
    name = 'FS_ellipsometer'
    
    def __init__(self, ip='192.168.1.68', port=4000):
        
        self.ip = ip
        self.port = port
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ip, self.port))
        
    
    def send_command(self, cmd_id, params = None):
                
        command = bytearray([3, 2, 1], cmd_id)
        if params:
            command.extend(params)
                       
        self.s.sendall(command)
        #print(f'Sent command ID {comm_id} with data {data_bytes}')
        
    
    def receive_resp(self, timeout=5):
        
        t0 = time.monotonic()
        while True:
            ready = select.select([self.s], [], [], 1)
            if ready[0]:
                response = self.s.recv(1024)
                #print('Received response:', response)
                return response
            if time.monotonic() - t0 > timeout:
                print("Timeout reached: no response received from the ellipsometer")
                return None
            time.sleep(0.1)
        
        
    def communication_check(self):
        
        self.send_command(28)
        response  = self.receive_resp()
        if response == b'\x00':
            print('Communication check successful')
        else:
            print('Communication check failed with error', response)
            
            
    def get_version(self):
        
        self.send_command(27)
        response  = self.receive_resp()
        
        ver_len = response[0]
        ver = response[1:ver_len+1].decode()
        print(f"{ver=}")
        
        ser_len = response[ver_len+1]
        serial_num = response[ver_len+2:ver_len+2+ser_len].decode()
        print(f"{serial_num=}")
    
    def get_models(self):
        
        self.send_command(11)
        response = self.receive_resp()  

        num_models = response[0]  #The first byte is the number of models
        models = []
        idx = 1
        for _ in range(num_models):
            name_length = response[idx]
            idx += 1
            model_name = response[idx:idx + name_length].decode("ascii")
            models.append(model_name)
            idx += name_length
        print("Available models:", models)
        return models
    
    def set_model_number(self, model_numb):
        
        self.send_command(12, model_numb)
        response = self.receive_resp()  

        if response == b'\x00':
            print(f"Model {model_numb} selected successfully")
        elif response == b'\x01':
            print('Error: model number out of range')
    
    
    def set_acquisition_time(self, acq_time):

        acq_time_bytes = struct.pack("<f", acq_time)
        self.send_command(18, acq_time_bytes)
        response = self.receive_resp()  
        if response == b'\x00':
            print(f"Acquisition time set to {acq_time} seconds.")
        else:
            print("Failed to set acquisition time with error:", response)
            
    def single_measurement(self, current_acq_time):
        
        self.send_command(13)
        response = self.receive_resp(timeout = current_acq_time*2)
        
        if response == b'\x00':
            print('Single measurement successful')
        elif response == b'\x01':
            print('Error: Continuous or Dynamic Measurement modes are active')
        
    def single_measurement_async(self):
        
        self.send_command(38)
        response = self.receive_resp()
        
        if response == b'\x00':
            print('Async single measurement started')
        elif response == b'\x01':
            print('Error: Continuous or Dynamic Measurement modes are active')
            
    def single_measurement_status(self):
        
        self.send_command(39)
        response = self.receive_resp()
        
        if response == b'\x00':
            print('Single measurement complete')
        elif response == b'\x01':
            print('Single measurement still in progress')
            
            
    def start_dynamic_measurement(self):
        
        self.send_command(17)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement started')
        elif response == b'\x01':
            print('Error: Continuous Measurement mode is active')
            
    
    def start_dynamic_measurement_pause(self):
        
        self.send_command(25)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement started in pause mode')
        elif response == b'\x01':
            print('Error: Continuous Measurement mode is active')
            
    def stop_dynamic_measurement(self):
        
        self.send_command(21)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement stopped')
        elif response == b'\x01':
            print('Error: Dynamic Measurement mode is not active')
            
    def pause_dynamic_measurement(self):
        
        self.send_command(22)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement paused')
        elif response == b'\x01':
            print('Error: Dynamic Measurement mode is not active')
            
    def resume_dynamic_measurement(self):
        
        self.send_command(23)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement resumed')
        elif response == b'\x01':
            print('Error: Dynamic Measurement mode is not active')
            
    def trigger_dynamic_measurement(self):
        
        self.send_command(24)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Dynamic measurement trigerred')
        elif response == b'\x01':
            print('Error: Dynamic Measurement mode is not active or not paused')
            
    def get_dynamic_measurement_status(self):
        
        self.send_command(56)
        response  = self.receive_resp()
        
        if response:
            acquiring_data = response[0]
            n_dyn_pts = struct.unpack('<I', response[1:5])[0]
            status = "acquiring" if acquiring_data == 1 else "not acquiring"
            print(f"Dynamic Measurements Status: {status}, Number of Points: {n_dyn_pts}")
        else:
            print("Error: No response received for dynamic measurements status.")
            
    def reanalyze_dynamic_measurement(self):
        
        self.send_command(57)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Reanalyze Dynamic Measurement - success')
        elif response == b'\x01':
            print('Error: No Dynamic Data')
            
    def reanalyze_dynamic_measurement_status(self):
        
        self.send_command(58)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Reanalysis complete')
        elif response == b'\x01':
            print('Reanalysis is still in progress')
            
    def next_layer(self):
        
        self.send_command(26)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Next layer - success')
        elif response == b'\x01':
            print('Error: Dynamic Measurement mode is not active')
            
    def get_params(self):
        """
        Returns a list of parameter names and values from the most recent ellipsometric data acquisition and model
        analysis. The first return byte is the number of parameters. The names and values of each parameter are encoded in the
        rest of the return byte stream: the next byte is the number of characters in the first parameter name, followed by bytes
        representing the ASCII characters in the first parameter name, the next 4 bytes are the single precision floating point value
        for the first parameter in little endian format, and so on for each parameter.
        In addition to the model fit parameters, the Fit_Diff, AlignX, AlignY, and AveInt parameters are also returned. If the
        Dynamic Measurements mode is active, the current Time parameter is returned. In Dynamic Measurements mode, the
        current “instantaneous” value for the returned model parameters is extrapolated from the preceding 2 measurements,
        which allows for improved precision in film thickness control (assuming that the polling rate of the “Get Parms”
        command is faster than the ellipsometric data acquisition rate). If the selected model is set to “(none)”, then the
        ellipsometric Psi and Delta values for each wavelength are returned as parameters.
        """
        
        self.send_command(14)
        response = self.receive_resp()
        
        num_params = response[0]
        params = {}
        idx = 1
        
        for _ in range(num_params):
            name_length = response[idx]
            idx += 1
            param_name = response[idx:idx + name_length].decode("ascii")
            idx += name_length
            
            param_value_bytes = response[idx:idx+4]
            param_value = struct.unpack('<f', param_value_bytes)[0]
            idx += 4
            
            params[param_name] = param_value
            print(f"Paramater: {param_name}, Value: {param_value}")
            
        return params
        
    def save_single_measurement(self, folder, file):
        """
        Saves the ellipsometric data and model results from the most recent Single Measurement.
        Args:
            folder_name (str): The name of the folder to save the data. Use "Default" for default folder.
            file_name (str): The name of the file to save the data.
        """
        cmd_id = 19
        params = bytearray()
        
        params.append(len(folder))
        params.extend(folder.encode('ascii'))
        params.append(len(file))
        params.extend(file.encode('ascii'))
        
        self.send_command(cmd_id, params)
        response = self.receive_resp()
        
        if response == b'\x00':
            print('Single measurement saved successfully')
        elif response == b'\x01':
            print('Error: Data File Could not be Saved')
            
    def save_dynamic_measurement(self, folder, file):
        """
        Saves the ellipsometric data and model results from the most recent Dynamic Measurements. Both the
        folder and filename to save the data are specified by this command, by sending a byte with the length of the folder name,
        the ASCII characters in the folder name, a byte with the length of the filename, and the ASCII characters in the filename.
        Specify a folder name of “Default” if it is desired to save all the files in the same folder.
        """
        cmd_id = 20
        params = bytearray()
        
        params.append(len(folder))
        params.extend(folder.encode('ascii'))
        params.append(len(file))
        params.extend(file.encode('ascii'))
        
        self.send_command(cmd_id, params)
        response = self.receive_resp()
        
        if response == b'\x00':
            print('Single measurement saved successfully')
        elif response == b'\x01':
            print('Error: Data File Could not be Saved')
            
    def reanalyze_data(self):
        
        self.send_command(29)
        response  = self.receive_resp()
        
        if response == b'\x00':
            print('Next layer - success')
        elif response == b'\x01':
            print('Error')
            
    
        
        
            
            
    
        
        
        
        
        
        
