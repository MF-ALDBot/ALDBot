from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import numpy as np
import pyqtgraph as pg
from pyqtgraph import mkPen
from _datetime import datetime
import os
import time
from ScopeFoundry.cb32_uuid import cb32_uuid7


class AldRunMeasure(Measurement):
    
    name = 'ald_run_measure'
    
    def setup(self):
        
        # MO Step Parameters
        self.settings.New('process_pressure', dtype = int, unit  = 'mTorr', initial = 30, vmin = 0, vmax = 1500)
        self.settings.New('precursor_dose_time', dtype = int, unit = 'ms', initial = 10, vmin = 0, vmax = 250)
        self.settings.New('ald_valves_delay', dtype = int, unit = 'ms', initial = 10)
        self.settings.New('precursor_purge_time', dtype = int, unit = 'ms', initial = 1000)
        self.settings.New('H2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('Ar_process_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('ALD_purge_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('ALD_prep_time', dtype = int, unit='ms', initial = 1000)
        self.settings.New('ALD_purge_time', dtype = int, unit='ms', initial = 1000)
        
        # Plasma Step Parameters
        self.settings.New('plasma_pressure', dtype = int, unit = 'mTorr', initial = 30, vmin = 0, vmax = 1500)
        self.settings.New('plasma_duration', dtype = int, unit = 'ms', initial = 1500)
        self.settings.New('N2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 86)
        self.settings.New('Ar_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('ALD_purge_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('RF_power_setpoint', dtype=int, unit='Watt', initial = 100, vmin = 0, vmax = 300)
        self.settings.New('LC_preset', dtype=int, unit='%', initial = 40, vmin = 0, vmax = 100)
        self.settings.New('TC_preset', dtype=int, unit='%', initial = 40, vmin = 0, vmax = 100)
        self.settings.New('plasma_prep_time', dtype = int, unit='ms', initial = 1000)
        self.settings.New('plasma_purge_time', dtype = int, unit='ms', initial = 1000)
        
        # Global Parameters
        self.settings.New('Number_of_ALD_cycles', dtype = int, vmin=1, initial = 50)
        
        # Metadata
        self.settings.New('Sample_name', dtype=str, initial = 'Si Wafer')
        self.settings.New('run_description', dtype=str)
        self.settings.New('run_id', dtype=str, initial='NO_ID', ro=True)
        self.add_operation('Generate Sample ID', self.generate_sample_id)
        self.add_operation('Load last Sample ID', self.load_last_sample_id)
        
        # Hardware
        self.maxigauge = self.app.hardware['Pfeiffer_MaxiGauge']
        self.vat = self.app.hardware['VAT_Valve']
        self.plc = self.app.hardware['productivity_plc']
        self.seren_ps = self.app.hardware['Seren_Power_Supply']
        self.seren_mc2 = self.app.hardware['Seren_Match_Box']
        self.filmsense = self.app.hardware['filmsense_ellipsometer']
        self.spectrometer = self.app.hardware['ocean_optics_spec']
        
    def setup_figure(self):
        
        #UI File
        self.ui_filename = sibling_path(__file__,"aldrun_ui.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)
        
        self.ui.run_pushButton.clicked.connect(self.start)
        
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        self.ui.load_id_pushButton.clicked.connect(self.load_last_sample_id)
        
        self.ui.new_id_pushButton.clicked.connect(self.generate_sample_id)
        
        self.app.settings.sample.connect_to_widget(
            ui.wafer_ID_label)
        
        self.plc.settings.PID_SetPoint.connect_to_widget(
            ui.temp_setpoint_doubleSpinBox)
        
        self.settings.process_pressure.connect_to_widget(
            ui.process_pressure_doubleSpinBox)
        
        self.settings.plasma_pressure.connect_to_widget(
            ui.plasma_pressure_doubleSpinBox)
        
        self.settings.plasma_duration.connect_to_widget(
            ui.plasma_duration_doubleSpinBox)
        
        self.settings.precursor_dose_time.connect_to_widget(
            ui.precursor_dose_doubleSpinBox)
        
        self.settings.precursor_purge_time.connect_to_widget(
            ui.ald_purge_time_doubleSpinBox)
        
        self.settings.ald_valves_delay.connect_to_widget(
            ui.ald_delay_doubleSpinBox)
        
        self.settings.H2_plasma_flow_rate.connect_to_widget(
            ui.process_gas_mfc_doubleSpinBox)
        
        self.settings.N2_plasma_flow_rate.connect_to_widget(
            ui.n2_plasma_mfc_doubleSpinBox)
        
        self.settings.Ar_plasma_flow_rate.connect_to_widget(
            ui.ar_plasma_mfc_doubleSpinBox)
        
        self.settings.ALD_purge_flow_rate.connect_to_widget(
            ui.ald_purge_mfc_doubleSpinBox)
        
        self.settings.Ar_process_flow_rate.connect_to_widget(
            ui.ar_process_mfc_doubleSpinBox)
        
        self.settings.RF_power_setpoint.connect_to_widget(
            ui.rf_power_doubleSpinBox)
        
        self.settings.ALD_prep_time.connect_to_widget(
            ui.mo_prep_time_doubleSpinBox)
        
        self.settings.ALD_purge_time.connect_to_widget(
            ui.mo_purge_time_doubleSpinBox)
        
        self.settings.ALD_purge_plasma_flow_rate.connect_to_widget(
            ui.ald_purge_plasma_mfc_doubleSpinBox)
        
        self.settings.plasma_prep_time.connect_to_widget(
            ui.plasma_prep_time_doubleSpinBox)
        
        self.settings.plasma_purge_time.connect_to_widget(
            ui.plasma_purge_time_doubleSpinBox)
        
        self.settings.LC_preset.connect_to_widget(
            ui.lc_preset_doubleSpinBox)
        
        self.settings.TC_preset.connect_to_widget(
            ui.tc_preset_doubleSpinBox)
        
        self.settings.Number_of_ALD_cycles.connect_to_widget(
            ui.ald_cycles_doubleSpinBox)
        
        self.settings.Sample_name.connect_to_widget(
            ui.sample_name_lineEdit)
        
        self.settings.run_description.connect_to_widget(
            ui.run_description_plainTextEdit)
        
        self.vat.settings.connected.connect_to_widget(
            ui.vat_valve_connect_checkBox)
        
        self.maxigauge.settings.connected.connect_to_widget(
            ui.maxigauge_connect_checkBox)
        
        self.filmsense.settings.connected.connect_to_widget(
            ui.filmsense_connect_checkBox)
        
        self.spectrometer.settings.connected.connect_to_widget(
            ui.spectrometer_connect_checkBox)
        
        def si_format(value, unit='torr'):
            prefixes = [
                (1e-9, 'n'),
                (1e-6, 'µ'),
                (1e-3, 'm'),
                (1e0, ''),
            ]           
            for factor, prefix in reversed(prefixes):
                if abs(value) >= factor:
                    return f"{value / factor:.3f} {prefix}{unit}"
            return f"{value:.3e} {unit}" 
        
        def update_gauge1_display():
            pressure_value = self.maxigauge.settings['ch1_pressure_scaled']
            formatted_value = si_format(pressure_value, unit='torr')
            ui.pressure_pfeiffer_write_label.setText(formatted_value)
        
        self.maxigauge.settings.ch1_pressure_scaled.add_listener(update_gauge1_display)
        
        self.seren_ps.settings.connected.connect_to_widget(
            ui.seren_power_supply_connect_checkBox)
        
        self.seren_mc2.settings.connected.connect_to_widget(
            ui.seren_mc2_connect_checkBox)
        
        self.plc.settings.connected.connect_to_widget(
            ui.plc_connect_checkBox)
        
        self.plc.settings.BNC1_baritron_gauge_mTorr.connect_to_widget(
            ui.pressure_baratron_write_label)
        
        self.plc.settings.AIF32_substrate_temp.connect_to_widget(
            ui.current_temp_read_label)
        
        #Setup the Ellipsometry Plot
        self.plot = pg.PlotWidget()
        self.ui.ellipsometry_graph_groupBox.layout().addWidget(self.plot)
        self.plotline = self.plot.plot()
        self.plot.setTitle("Ellipsometry Graph", color='k', size = '14pt')
        self.plot.setBackground('w')
        self.plot.getAxis('left').setPen('k')
        self.plot.getAxis('bottom').setPen('k')
        self.plotline.setPen(mkPen(color='r', width=2))
        labelStyle = {'color': '#000', 'font-size': '12pt'}
        self.plot.setLabel('bottom', 'Cycle number', **labelStyle)
        self.plot.setLabel('left', 'Thickness (nm)', **labelStyle)
               
    #def start_process(self):
    #   self.start()   
    #def interrupt_process(self):
    #   self.interrupt()    
                   
    def run(self):
        
        S = self.settings
        
        #Create an H5 file to log all the settings
        # Generate a timestamped folder name
        folder_name = datetime.now().strftime("%Y_%m_%d_time_%H_%M_%S")
        folder_name = folder_name + f"_{self.settings.Sample_name.val}"
        folder_path = f"C:\\Users\\lab\\Documents\\ALDBot Data\\{folder_name}"
        filename = self.settings.Sample_name.val
        os.makedirs(folder_path, exist_ok=True)
        self.app.settings['save_dir'] = folder_path
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_filename = self.h5_file.filename
        self.run_id = self.h5_file.attrs['unique_id']
        self.settings['run_id'] = self.run_id
        self.t0 = time.time()
        self.h5_file.attrs['time_id'] = self.t0
        Hm = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
        Hm['cycle_start_time'] = np.zeros(S['Number_of_ALD_cycles'], dtype=np.float64)
        
        # H5 spectroscopy
        wls = self.app.hardware['ocean_optics_spec'].wavelengths
        Hm['oes_spec_wls'] = wls
        self.oes_specH5 = h5_io.create_extendable_h5_dataset(Hm, 'oes_spec', shape=(1, len(wls)), axis=0, dtype=np.float64)
        self.oes_spec_timeH5 = h5_io.create_extendable_h5_dataset(Hm, 'oes_spec_time', shape=(1,), 
                                                                  axis=0, dtype=np.float64, chunks=100)
        self.oes_spec_cycleH5 = h5_io.create_extendable_h5_dataset(Hm, 'oes_spec_cycle', shape=(1,), 
                                                                  axis=0, dtype=np.int16, chunks=100)
        
        # start the spectrometer
        speclive = self.app.measurements['oo_spec_live']
        speclive.settings['continuous'] = True
        speclive.settings['activation'] = True
        
        self.status = f"Starting Run {self.run_id}..."
        self.thickness_data = []
        self.cycles = []
        self.growth_rate = []
        
        try:
            """
            #Set the temperature            
            self.plc.settings['PID_SetPoint'] = S['substrate_temp']
            """
            #Start the Ellipsometry (dynamic)
            self.filmsense.start_dynamic_measurement()
            self.status = 'Collecting ellipsometry for the substrate'
            t0 =time.monotonic()
            while (time.monotonic() - t0) < 10:
                if self.interrupt_measurement_called:
                    break
                            
            
            #Set ALD valve timings
            self.plc.settings['t1_Preset'] = S['precursor_dose_time']
            self.plc.settings['t_delay_Preset'] = S['ald_valves_delay']
            self.plc.settings['t2_Preset'] = S['precursor_purge_time']
            
            self.status = "Closing all valves..."
            
            #Make sure all MFCs are closed
            print('Closing MFCs...')
            self.plc.settings['MFC1_H2_SP_sccm'] = 0
            self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0
            self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = 0
            self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 0

            #  close all valves
            print('Closing all the valves...')
            self.plc.settings['Valve2_ALD_purge_open'] = False
            self.plc.settings['Valve3_plasma_purge_open'] = False
            self.plc.settings['Valve4_plasma_process_gas_open'] = False
            self.plc.settings['Valve5_plasma_nitrogen_open'] = False
            self.plc.settings['Valve6_plasma_argon_open'] = False
            self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False
            self.plc.settings['Valve8_window_purge_open'] = False

            ## Get the process parameters   
            self.status = "Stabilizing pressure to get process parameters..."
            
            #Open the Ar plasma valve for pressure stabilization
            print('Opening the Ar valve for pressure stabilization...')
            self.plc.settings['Valve6_plasma_argon_open'] = True            
            
            #Set process pressure
            print('Trying to set process pressure...')
            if self.set_process_pressure(S['process_pressure'], timeout=10, tolerance = 4, stabilization_time=5.0):
                print('Process pressure setpoint reached')
            else:
                raise RuntimeError("Error: Process pressure did not stabilize.")
            
            #Record the position of the VAT valve
            process_vat_position = self.vat.settings.actual_position.read_from_hardware()
            print(f"Process VAT position is {process_vat_position}")
            

            ## Get the plasma parameters
            ## Skipping this part for now, because not using it
            
            """            
            #Pre-tune the matching box
            print('Tuning the matching box...')       
            self.seren_mc2.settings['set_lc_preset_position'] = 52
            self.seren_mc2.settings['set_tc_preset_position'] = 31
            self.seren_mc2.goto()
            self.seren_mc2.settings['LC_auto'] = True
            self.seren_mc2.settings['TC_auto'] = True
            
            #Set the RF setpoint
            self.seren_ps.settings['set_forward_power'] = S.RF_power_setpoint.value
            
            self.status = "Stabilizing pressure to get plasma parameters..."
            
            # set plasma valve mfc config
            if self.settings['H2_plasma_flow_rate'] > 1:
                self.plc.settings['Valve4_plasma_process_gas_open'] = True # H2/O2 Plasma MFC valve
                self.plc.settings['MFC1_H2_SP_sccm'] = self.settings['H2_plasma_flow_rate']
            if self.settings['N2_plasma_flow_rate'] > 1:
                self.plc.settings['Valve5_plasma_nitrogen_open'] = True # N2 Plasma MFC valve
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = self.settings['N2_plasma_flow_rate']
            if self.settings['ALD_purge_plasma_flow_rate'] > 1:
                self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True #Ar ALD Purge Pneumatic Valve
                self.plc.settings['Valve2_ALD_purge_open'] = True  #Ar ALD Purge Valve
                self.plc.settings['MFC4_ALD_purge_SP_sccm'] = self.settings['ALD_purge_plasma_flow_rate']
            #if self.settings['Ar_plasma_flow_rate'] > 1:
            #   self.plc.settings['Valve6_plasma_argon_open'] = True # valve before Ar plasma MFC (MFC3)
            # Note that the Valve6 is always open to set process pressure
            self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_plasma_flow_rate']
                    
            # wait for pressure to stabilize
            self.vat.settings.target_pressure.update_value(S['plasma_pressure'], update_hardware=True)
            self.vat.settings.target_pressure.write_to_hardware()
            t0 = time.monotonic()
            tolerance = 8
            time.sleep(3)
            while True:
                current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
                
                if abs(current_pressure-S['plasma_pressure']) <= 0.5*tolerance:
                    break
                if time.monotonic() - t0 > 10.0:
                    raise ValueError("Error: Plasma pressure did not reach setpoint")
                print(S['plasma_pressure'],current_pressure)
                time.sleep(0.1)
                        
            stabilization_start = time.monotonic()
            stabilization_time = 5.0
            while (time.monotonic() - stabilization_start) < stabilization_time:
                current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
                if not (S['plasma_pressure'] - tolerance <= current_pressure <= S['plasma_pressure'] + tolerance):
                    raise ValueError('Plasma pressure failed to stabilize')
                time.sleep(0.050)
                
            print(f"Plasma pressure stable for {stabilization_time} seconds. Proceeding...")
            
            self.status = "Striking plasma..."
            
            #Strike plasma
            self.seren_ps.settings['RF_enable'] = True
        
            t0 = time.monotonic()
            plasma_duration_sec = 3
            while (time.monotonic() - t0) < plasma_duration_sec:
                current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
                plasma_vat_position = self.vat.settings.actual_position.read_from_hardware()
                plasma_lc_position = self.seren_mc2.settings.LC_position.read_from_hardware()
                plasma_tc_position = self.seren_mc2.settings.TC_position.read_from_hardware()                
                if self.interrupt_measurement_called:
                    break
                time.sleep(0.010)
            # plasma done, record parameters
            plasma_vat_position = self.vat.settings.actual_position.read_from_hardware()
            print(f"Plasma VAT position is {plasma_vat_position}")
            self.seren_ps.settings['RF_enable'] = False  
            """
            
            if self.interrupt_measurement_called:
                return
            self.perform_safety_checks()
                        
            #Close the plasma supply valves
            self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
            self.plc.settings['MFC1_H2_SP_sccm'] = 0
            self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
            self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0
            
            #Check that temperature is in range
            tolerance = 10 #degrees C
            current_temp = self.plc.settings['AIF32_substrate_temp']
            setpoint_temp = self.plc.settings['PID_SetPoint']
            if not ((current_temp - tolerance) <  setpoint_temp < (current_temp + tolerance)):
                raise ValueError('Substrate temperature is far from setpoint', setpoint_temp, current_temp)
            
            # Start the ellipsometry (IF single measurements)
            #self.status = "Collecting Ellipsometry Data for the Substrate..."
            os.makedirs(folder_path, exist_ok=True)
            #self.filmsense.single_measurement_collect()
            #time.sleep(1)
            #filename = f"{self.settings.Sample_name.val}_substrate"
            #self.filmsense.external_save_single(filename, folder_path)
            
            
            self.status = "Moving to the ALD loop..." 
            
            #The ALD Loop
            print('Starting the ALD loop...')
            for i in range(S['Number_of_ALD_cycles']):
                
                Hm['cycle_start_time'][i] = time.time()
                cycle_number = i+1
                print("ALD Cycle", cycle_number, 'of', S['Number_of_ALD_cycles'])          
                self.status = f"ALD cycle {cycle_number} out of {S['Number_of_ALD_cycles']}"
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                #Pre-tune the matching box
                self.seren_mc2.settings['set_lc_preset_position'] = self.settings['LC_preset']  #plasma_lc_position
                self.seren_mc2.settings['set_tc_preset_position'] = self.settings['TC_preset'] #plasma_tc_position
                self.seren_mc2.goto()
                
                """
                #Open window purges
                print('Opening the window purge valve...')
                self.plc.settings['Valve8_window_purge_open'] = True
                """
                ## MO Prep Phase
                #Open the ALD purge flow, if closed
                self.plc.settings['MFC4_ALD_purge_SP_sccm'] = S['ALD_purge_flow_rate']
                self.plc.settings['Valve2_ALD_purge_open'] = True
                self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True    
                
                #Open Argon flow, set the position/pressure for the VAT valve
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
                #self.vat.settings.target_position.update_value(process_vat_position)
                #self.vat.settings.target_position.write_to_hardware()
                self.vat.settings.target_pressure.update_value(S['process_pressure'], update_hardware=True)
                self.vat.settings.target_pressure.write_to_hardware()   
                
                #Time to stabilize/prep
                ald_prep_time_s = S['ALD_prep_time']/1000
                t0 =time.monotonic()
                while (time.monotonic() - t0) < ald_prep_time_s:
                    if self.interrupt_measurement_called:
                        break
                    self.vat.settings.actual_pressure.read_from_hardware()
                #Close the ALD purge valve
                self.plc.settings['Valve2_ALD_purge_open'] = False
                
                ## MO Dose phase
                #ALD Valves Sequence
                print('Starting the ALD valve sequence...')
                self.plc.settings['start_ALD_Valve1_dose'] = True
                
                def read_ald_dose_state():
                    result =  self.plc.modbus_client.read_coils(self.plc.tag_db['start_ALD_Valve1_dose']['modbus_start'])
                    if result is not None and isinstance(result, list) and len(result) > 0:
                        return result[0]
                    return None
                
                #while self.plc.settings['start_ALD_Valve1_dose']:
                dose_state = True
                while dose_state:                    
                    dose_state = read_ald_dose_state()
                    if dose_state is None:
                        print("Warning: Failed to read ALD dose state, retrying...")
                        continue
                    self.vat.settings.actual_pressure.read_from_hardware()
                    if self.interrupt_measurement_called:
                        break
                    self.perform_safety_checks()
                
                ## MO Purge Phase                
                #Time to purge
                self.plc.settings['Valve2_ALD_purge_open'] = True
                ald_purge_time_s = S['ALD_purge_time']/1000
                t0 =time.monotonic()
                while (time.monotonic() - t0) < ald_purge_time_s:
                    self.vat.settings.actual_pressure.read_from_hardware()
                    if self.interrupt_measurement_called:
                        break
                
                # Close ALD Purge if not using during the plasma phase
                if self.settings['ALD_purge_plasma_flow_rate'] == 0:
                    self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False 
                    self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 0
                    self.plc.settings['Valve2_ALD_purge_open'] = False                
                
                if self.interrupt_measurement_called:
                    break

                ## Plasma Prep Phase
                
                #Set plasma VAT position
                #self.vat.settings.target_position.update_value(plasma_vat_position)
                #self.vat.settings.target_position.write_to_hardware()
                self.vat.settings.target_pressure.update_value(S['plasma_pressure'], update_hardware=True)
                self.vat.settings.target_pressure.write_to_hardware()   
                
                
                #Close window purge
                self.plc.settings['Valve8_window_purge_open'] = False
                
                # set plasma valve mfc config
                if self.settings['H2_plasma_flow_rate'] > 1:
                    self.plc.settings['Valve4_plasma_process_gas_open'] = True # H2/O2 Plasma MFC valve
                    self.plc.settings['MFC1_H2_SP_sccm'] = self.settings['H2_plasma_flow_rate']
                if self.settings['N2_plasma_flow_rate'] > 1:
                    self.plc.settings['Valve5_plasma_nitrogen_open'] = True # N2 Plasma MFC valve
                    self.plc.settings['MFC2_N2_plasma_SP_sccm'] = self.settings['N2_plasma_flow_rate']
                if self.settings['ALD_purge_plasma_flow_rate'] > 1:
                    self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True #Ar ALD Purge Pneumatic Valve
                    self.plc.settings['Valve2_ALD_purge_open'] = True  #Ar ALD Purge Valve
                    self.plc.settings['MFC4_ALD_purge_SP_sccm'] = self.settings['ALD_purge_plasma_flow_rate']
                #if self.settings['Ar_plasma_flow_rate'] > 1:
                #   self.plc.settings['Valve6_plasma_argon_open'] = True # valve before Ar plasma MFC (MFC3)
                # Note that the Valve6 is always open to set process pressure
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_plasma_flow_rate']             

                #Time to stabilize/prep
                plasma_prep_time_s = S['plasma_prep_time']/1000
                t0 =time.monotonic()
                while (time.monotonic() - t0) < plasma_prep_time_s:
                    self.vat.settings.actual_pressure.read_from_hardware()
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                ## Plasma dose Phase
                #Strike plasma
                self.seren_ps.settings['RF_enable'] = True
        
                # TODO This should be a loop, things to check for: 
                t0 = time.monotonic()
                # plasma duration is in milliseconds
                plasma_duration_sec = S['plasma_duration']/1000.
                while (time.monotonic() - t0) < plasma_duration_sec:
                    self.vat.settings.actual_pressure.read_from_hardware()

                    # Read state of plasma power supply and matching unit
                    self.seren_mc2.settings.LC_position.read_from_hardware()
                    self.seren_mc2.settings.TC_position.read_from_hardware()
                    self.seren_ps.settings.forward_power_readout.read_from_hardware()
                    self.seren_ps.settings.reflected_power.read_from_hardware()
                    # store OES spectrum
                    # get_spectrum returns last acquired spectrum, does not wait for new data,
                    # oo_spec_live must be running
                    h5_append(self.oes_specH5, self.app.hardware['ocean_optics_spec'].get_spectrum().reshape(1,-1))
                    h5_append(self.oes_spec_timeH5,np.array([time.time()]))
                    h5_append(self.oes_spec_cycleH5,np.array([i]))
                    if self.interrupt_measurement_called:
                        break
                    self.perform_safety_checks()
                    time.sleep(0.010)
                # plasma done
                self.seren_ps.settings['RF_enable'] = False
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                ## Plasma Purge Prep
                
                # Close Plasma gases  
                self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
                self.plc.settings['MFC1_H2_SP_sccm'] = 0
                self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0
                
                #Open Ar Purge
                
                self.plc.settings['MFC4_ALD_purge_SP_sccm'] = S['ALD_purge_flow_rate']
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
                self.plc.settings['Valve2_ALD_purge_open'] = True
                self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True      
                
                
                '''
                self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
                self.plc.settings['MFC1_H2_SP_sccm'] = 0
                self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0          
                # Note we leave Ar valve and MFC open for purge throughout ALD run
                '''                
                ## Plasma Purge Phase
                plasma_purge_time_s = S['plasma_purge_time']/1000
                t0 =time.monotonic()
                while (time.monotonic() - t0) < plasma_purge_time_s:
                    self.vat.settings.actual_pressure.read_from_hardware()
                    if self.interrupt_measurement_called:
                        break
                
                #Collect Ellipsometric Data
                
                #self.status = 'Collecting Ellipsometric data...'
                #self.filmsense.single_measurement_collect()
                #time.sleep(1.5)
                params = self.filmsense.get_params()
                thickness_value = round(params["Thick(nm).2"],2)
                self.thickness_data.append(thickness_value)
                self.cycles.append(cycle_number)
                if len(self.thickness_data)>2:
                    cycle_growth = self.thickness_data[-1] - self.thickness_data[-2]
                    print('Growth rate this cycle:', cycle_growth)
                    self.growth_rate.append(cycle_growth)
                #filename = self.settings.Sample_name.val
                #filename = filename + f"_cycle_{cycle_number}"
                #self.filmsense.external_save_single(filename, folder_path)
                #thickness_value_str = f'{thickness_value}'
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                
                # #Plasma purge (needle valve)
                # self.plc.settings['Valve3_plasma_purge_open'] = True
                #
                # t0 = time.monotonic()
                # while (time.monotonic() - t0) < S['plasma_purge_time']:
                #     # do stuff
                #     time.sleep(0.010)
                # self.plc.settings['Valve3_plasma_purge_open'] = False
                
            ##Final purging  after the process is done
            # close all valves
            self.plc.settings['Valve2_ALD_purge_open'] = True
            self.plc.settings['Valve3_plasma_purge_open'] = False
            self.plc.settings['Valve4_plasma_process_gas_open'] = False
            self.plc.settings['Valve5_plasma_nitrogen_open'] = False
            self.plc.settings['Valve6_plasma_argon_open'] = False
            self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False
            self.plc.settings['Valve8_window_purge_open'] = False
            #Open MFCs to purge the space between them and the shut off valves
            self.plc.settings['MFC1_H2_SP_sccm'] = 50
            self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 50
            self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = 50
            self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 50
            # Fully open Throttle Valve (VAT)
            self.vat.settings.target_position.update_value(100)
            self.vat.settings.target_position.write_to_hardware()
            self.status = 'System is purging to base pressure'
            
            #Stop the ellipsometry
            self.filmsense.stop_dynamic_measurement()
            #Purge all the lines
            t0 = time.monotonic()
            while (time.monotonic() - t0) < 120:
                if self.interrupt_measurement_called:
                    break
                time.sleep(1)            
                                
        except Exception as err:
            print("Process Stopped because of error:", err)
            self.status = "Error! Moving to the safe state"
            # do stuff to clean up on failure
            raise err
        finally:
            # do stuff to clean up on either success or failure
            # Turn off Plasma
            self.seren_ps.settings['RF_enable'] = False
            # close all valves
            self.plc.settings['Valve2_ALD_purge_open'] = False
            self.plc.settings['Valve3_plasma_purge_open'] = False
            self.plc.settings['Valve4_plasma_process_gas_open'] = False
            self.plc.settings['Valve5_plasma_nitrogen_open'] = False
            self.plc.settings['Valve6_plasma_argon_open'] = False
            self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False
            self.plc.settings['Valve8_window_purge_open'] = False
            # Zero all MFCs
            self.plc.settings['MFC1_H2_SP_sccm'] = 0
            self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0
            self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = 0
            self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 0
            # Fully open Throttle Valve (VAT)
            self.vat.settings.target_position.update_value(100)
            self.vat.settings.target_position.write_to_hardware()
            thickness_array = np.array(self.thickness_data)
            Hm['thickness_data'] = thickness_array
            gr_array = np.array(self.growth_rate)
            growth_rate_ave = np.mean(gr_array)
            print('Average Growth rate for the deposition:', growth_rate_ave)
            Hm['growth_rate'] = gr_array
            self.h5_file.close()
            
            #Stop the ellipsometry and save the data
            self.filmsense.stop_dynamic_measurement()
            self.filmsense.external_save_dynamic(filename,folder_path)
            
            self.status = 'System is in the safe state. The process is finished.'
            
    def set_process_pressure(self, target_pressure, timeout, tolerance=2., interval=0.100, stabilization_time = 5):    
        
        #self.vat.settings['target_pressure'] = target_pressure
        self.vat.settings.target_pressure.update_value(target_pressure, update_hardware=True)
        self.vat.settings.target_pressure.write_to_hardware()
        self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
        self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True
        self.plc.settings['MFC4_ALD_purge_SP_sccm'] = self.settings['ALD_purge_flow_rate']
        self.plc.settings['Valve2_ALD_purge_open'] = True
        
        t0 = time.monotonic()
        
        time.sleep(1)
        
        while True:
            current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
            if abs(current_pressure-target_pressure) <= 0.5*tolerance:
                print('Process pressure setpoint reached, stabilizing...')
                break
            if time.monotonic() - t0 > timeout:
                return False
            time.sleep(interval)
            
        stabilization_start = time.monotonic()
        print(f'Stablization start time: {stabilization_start}')
        while (time.monotonic() - stabilization_start) < stabilization_time:
            current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
            print( time.monotonic()-stabilization_start,
                   (target_pressure - tolerance),
                   current_pressure ,
                   (target_pressure + tolerance))
            if not ((target_pressure - tolerance) <= current_pressure <= (target_pressure + tolerance)):
                print('Process pressure failed to stabilize')
                return False
            time.sleep(interval)
            
        print(f"Process pressure stable for {stabilization_time} seconds. Proceeding...")
        self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False
        self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 0
        self.plc.settings['Valve2_ALD_purge_open'] = False
        return True
    
    def perform_safety_checks(self):
        
        if self.maxigauge.settings.ch1_pressure_scaled.value > 5.0:
            self.plc.settings['ScopeFoundry_high_pressure_alert'] = 1 # Trigger PLC safe mode
            raise ValueError('Error! Pressure is too high! Closing all valves...')

        if self.plc.settings['High_pressure_error']:
            raise ValueError('Error! Pressure is too high on PLC! Closing all valves...')
        
        if self.maxigauge.settings.ch1_pressure_scaled.value < 1e-4:
            raise ValueError('Error! Pressure is too low! Going to the safe state...')
        
    def update_display(self):
        
        self.ui.status_label.setText(self.status)
        #print("status:", self.status)
        
        if hasattr(self, 'thickness_data'):
            if len(self.thickness_data)>2:
                self.plotline.setData(self.cycles, self.thickness_data)
        
    def generate_sample_id(self):
        from ScopeFoundry.cb32_uuid import cb32_uuid
        s, _  = cb32_uuid()
        self.app.settings['sample'] = s

        import json
        with open('sample_id.json', 'r') as f:
            sample_ids = json.load(f)
        sdict = {'sample':s, 'time':time.time()}
        sample_ids.append(sdict)
        with open('sample_id.json', 'w') as f:
            json.dump(sample_ids,f,indent=2)

        self.print_barcode()

    def print_barcode(self):
        from image_print import make_qr, make_image, print_label
        unique_id = self.app.settings['sample']
        qr_img = make_qr(f"{unique_id}")
        make_image(qr_img,f"{unique_id}", "new.png")
        print_label("Brother PT-D610BT", "new.png")
    
    def load_last_sample_id(self):
        import json
        with open('sample_id.json', 'r') as f:
            sample_ids = json.load(f)
        self.app.settings['sample'] = sample_ids[-1]['sample']
        

def h5_append(ds, new_data, axis=0):
    
    h5_io.extend_h5_dataset_along_axis(ds, ds.shape[axis]+new_data.shape[axis], axis=axis)
    slice_list = [slice(None),]*len(ds.shape)
    slice_list[axis] = slice(-new_data.shape[axis]-1,-1)
    #print(slice_list)
    ds[tuple(slice_list)] = new_data

            