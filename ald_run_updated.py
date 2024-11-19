from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
from pyqtgraph import mkPen
from _datetime import datetime
import time


class AldRunMeasure2(Measurement):
    
    name = 'ald_run_upd'
    
    def setup(self):
        
        # self.settings.New('substrate_temp', dtype = int, unit='C', initial = 20)
        self.settings.New('process_pressure', dtype = int, unit  = 'mTorr', initial = 30, vmin = 0, vmax = 1500)
        self.settings.New('plasma_pressure', dtype = int, unit = 'mTorr', initial = 30, vmin = 0, vmax = 1500)
        self.settings.New('plasma_duration', dtype = int, unit = 'ms', initial = 1500)
        self.settings.New('precursor_dose_time', dtype = int, unit = 'ms', initial = 10, vmin = 0, vmax = 250)
        self.settings.New('ald_valves_delay', dtype = int, unit = 'ms', initial = 10)
        self.settings.New('precursor_purge_time', dtype = int, unit = 'ms', initial = 1000)
        self.settings.New('H2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('N2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 86)
        self.settings.New('Ar_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('Ar_process_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('ALD_purge_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('RF_power_setpoint', dtype=int, unit='Watt', initial = 100, vmin = 0, vmax = 300)
        
        self.settings.New('LC_preset', dtype=int, unit='%', initial = 40, vmin = 0, vmax = 100)
        self.settings.New('TC_preset', dtype=int, unit='%', initial = 40, vmin = 0, vmax = 100)
        
        self.settings.New('ALD_prep_time', dtype = int, unit='ms', initial = 1000)
        self.settings.New('ALD_purge_time', dtype = int, unit='ms', initial = 1000)
        self.settings.New('plasma_prep_time', dtype = int, unit='ms', initial = 1000)
        self.settings.New('plasma_purge_time', dtype = int, unit='ms', initial = 1000)
        
        self.settings.New('Number_of_ALD_cycles', dtype = int, vmin=1, initial = 10)
        self.settings.New('Sample_name', dtype=str, initial = 'ald_test_measurement')
        
        self.maxigauge = self.app.hardware['Pfeiffer_MaxiGauge']
        self.vat = self.app.hardware['VAT_Valve']
        self.plc = self.app.hardware['productivity_plc']
        self.seren_ps = self.app.hardware['Seren_Power_Supply']
        self.seren_mc2 = self.app.hardware['Seren_Match_Box']
        self.filmsense = self.app.hardware['filmsense_ellipsometer']
        
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__,"aldrun_ui_final.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)
        
        self.ui.run_pushButton.clicked.connect(self.start_process)
        
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt_process)
        
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
        
        self.vat.settings.connected.connect_to_widget(
            ui.vat_valve_connect_checkBox)
        
        self.maxigauge.settings.connected.connect_to_widget(
            ui.maxigauge_connect_checkBox)
        
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
        
                
    def start_process(self):
        self.start()
    
    def interrupt_process(self):
        self.interrupt()    
        
    
    
    def run(self):
        
        S = self.settings
        
        self.status = "Starting..."
        
        try:
            """
            #Set the temperature            
            self.plc.settings['PID_SetPoint'] = S['substrate_temp']
            """
            
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
            
            #Make sure the ALD Purge is closed
            print('Closing the ALD purge valve...')
            self.plc.settings['Valve2_ALD_purge_open'] = False

            #  close all valves
            print('Closing all the valves...')
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
            if self.set_process_pressure(S['process_pressure'], timeout=10, tolerance = 4, stabilization_time=10.0):
                print('Process pressure setpoint reached')
            else:
                raise RuntimeError("Error: Process pressure did not stabilize.")
            
            #Record the position of the VAT valve
            process_vat_position = self.vat.settings.actual_position.read_from_hardware()
            print(f"Process VAT position is {process_vat_position}")
            

            ## Get the plasma parameters
                        
            #Pre-tune the matching box
            print('Tuning the matching box...')       
            self.seren_mc2.settings['set_lc_preset_position'] = 50
            self.seren_mc2.settings['set_tc_preset_position'] = 50
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
            stabilization_time = 10.0
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
            # plasma duration is in milliseconds
            #plasma_duration_sec = S['plasma_duration']/1000.
            plasma_duration_sec = 8
            while (time.monotonic() - t0) < plasma_duration_sec:
                if self.interrupt_measurement_called:
                    break
                time.sleep(0.010)
            # plasma done, record parameters
            plasma_vat_position = self.vat.settings.actual_position.read_from_hardware()
            print(f"Plasma VAT position is {plasma_vat_position}")
            plasma_lc_position = self.seren_mc2.settings.LC_position.read_from_hardware()
            plasma_tc_position = self.seren_mc2.settings.TC_position.read_from_hardware()
            self.seren_ps.settings['RF_enable'] = False
            
            
            if self.interrupt_measurement_called:
                return
            self.perform_safety_checks()
            
            """
            self.seren_mc2.settings['set_lc_preset_position'] = plasma_lc_position
            self.seren_mc2.settings['set_tc_preset_position'] = plasma_tc_position
            self.seren_mc2.goto()
            """
                        
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
            
            # Start the ellipsometry
            self.status = "Collecting Ellipsometry Data for the Substrate..."
            #self.filmsense.start_dynamic_measurement_pause()
            folder_name = datetime.now().strftime("%Y_%m_%d")
            folder_name = folder_name + f"_{self.settings.Sample_name.val}"
            self.filmsense.single_measurement_collect()
            filename = self.settings.Sample_name.val
            filename = filename + '_substrate'
            self.filmsense.save_single_measurement(folder_name, filename)
            self.thickness_data = []
            self.cycles = []
            
            self.status = "Moving to the ALD loop..." 

            
            #The ALD Loop
            print('Starting the ALD loop...')
            for i in range(S['Number_of_ALD_cycles']):
                cycle_number = i+1
                print("ALD Cycle", cycle_number, 'of', S['Number_of_ALD_cycles'])          
                self.status = f"ALD cycle {cycle_number} out of {S['Number_of_ALD_cycles']}"
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                """
                #Open window purges
                print('Opening the window purge valve...')
                self.plc.settings['Valve8_window_purge_open'] = True
                """
                ## MO Prep Phase
                #Open the ALD purge flow
                self.plc.settings['MFC4_ALD_purge_SP_sccm'] = S['ALD_purge_flow_rate']
                self.plc.settings['Valve2_ALD_purge_open'] = True
                self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True    
                
                #Open flow, set the position of the VAT valve
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
                #self.vat.settings.target_position.update_value(process_vat_position)
                #self.vat.settings.target_position.write_to_hardware()
                self.vat.settings.target_pressure.update_value(S['process_pressure'], update_hardware=True)
                self.vat.settings.target_pressure.write_to_hardware()   
                
                #Time to stabilize/prep
                ald_prep_time_s = S['ALD_prep_time']/1000
                time.sleep(ald_prep_time_s)
                self.plc.settings['Valve2_ALD_purge_open'] = False
                
                ## MO Dose phase
                #ALD Valves Sequence
                print('Starting the ALD valve sequence...')
                self.plc.settings['start_ALD_Valve1_dose'] = True
                     
                while self.plc.settings['start_ALD_Valve1_dose']:
                    if self.interrupt_measurement_called:
                        break
                    self.perform_safety_checks()
                    #===============================================================
                    # Add a timeout here? YES
                    #===============================================================                
                
                ## MO Purge Phase                
                #Time to purge
                self.plc.settings['Valve2_ALD_purge_open'] = True
                ald_purge_time_s = S['ALD_purge_time']/1000
                time.sleep(ald_purge_time_s)
                self.plc.settings['Valve7_ald_pneumatic_purge_open'] = False 
                self.plc.settings['MFC4_ALD_purge_SP_sccm'] = 0
                self.plc.settings['Valve2_ALD_purge_open'] = False
                
                
                ## Plasma Prep Phase
                
                #Set plasma VAT position
                self.vat.settings.target_position.update_value(plasma_vat_position)
                self.vat.settings.target_position.write_to_hardware()
                self.seren_mc2.settings['set_lc_preset_position'] = self.settings['LC_preset']  #plasma_lc_position
                self.seren_mc2.settings['set_tc_preset_position'] = self.settings['TC_preset'] #plasma_tc_position
                self.seren_mc2.goto()
                
                #Close window purge
                self.plc.settings['Valve8_window_purge_open'] = False
                
                # set plasma valve mfc config
                if self.settings['H2_plasma_flow_rate'] > 1:
                    self.plc.settings['Valve4_plasma_process_gas_open'] = True # H2/O2 Plasma MFC valve
                    self.plc.settings['MFC1_H2_SP_sccm'] = self.settings['H2_plasma_flow_rate']
                if self.settings['N2_plasma_flow_rate'] > 1:
                    self.plc.settings['Valve5_plasma_nitrogen_open'] = True # N2 Plasma MFC valve
                    self.plc.settings['MFC2_N2_plasma_SP_sccm'] = self.settings['N2_plasma_flow_rate']
                #if self.settings['Ar_plasma_flow_rate'] > 1:
                #   self.plc.settings['Valve6_plasma_argon_open'] = True # valve before Ar plasma MFC (MFC3)
                # Note that the Valve6 is always open to set process pressure
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_plasma_flow_rate']             

                #Time to stabilize/prep
                plasma_prep_time_s = S['plasma_prep_time']/1000
                time.sleep(plasma_prep_time_s)
                
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
                    self.seren_mc2.settings.LC_position.read_from_hardware()
                    self.seren_mc2.settings.TC_position.read_from_hardware()
                    self.seren_ps.settings.forward_power_readout.read_from_hardware()
                    self.seren_ps.settings.reflected_power.read_from_hardware()
                    if self.interrupt_measurement_called:
                        break
                    self.perform_safety_checks()
                    time.sleep(0.010)
                # plasma done
                self.seren_ps.settings['RF_enable'] = False
                
                self.seren_mc2.settings.LC_position.read_from_hardware()
                self.seren_mc2.settings.TC_position.read_from_hardware()
                self.seren_ps.settings.forward_power_readout.read_from_hardware()
                self.seren_ps.settings.reflected_power.read_from_hardware()
                
                
                if self.interrupt_measurement_called:
                    break
                self.perform_safety_checks()
                
                ## Plasma Purge Prep
                '''
                self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
                self.plc.settings['MFC1_H2_SP_sccm'] = 0
                self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0          
                # Note we leave Ar valve and MFC open for purge throughout ALD run
                '''
                
                ## Plasma Purge Phase
                plasma_purge_time_s = S['plasma_purge_time']/1000
                time.sleep(plasma_purge_time_s)
                
                #Collect Ellipsometric Data
                self.status = 'Collecting Ellipsometric data...'
                self.filmsense.single_measurement_collect()
                params = self.filmsense.get_params()
                thickness_value = round(params["Thick(nm).1"],2)
                self.thickness_data.append(thickness_value)
                self.cycles.append(cycle_number)
                filename = self.settings.Sample_name.val
                filename = filename + f"_cycle_{cycle_number}"
                self.filmsense.save_single_measurement(folder_name, filename)
                #thickness_value_str = f'{thickness_value}'
                
                
                # Close Plasma gases  
                self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
                self.plc.settings['MFC1_H2_SP_sccm'] = 0
                self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0   
                
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
                #
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
            
            #Stop the ellipsometry and save the data
            #self.filmsense.stop_dynamic_measurement()
            #self.filmsense.save_dynam_meas()
            
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
            self.plotline.setData(self.cycles, self.thickness_data)
        
            
                
        

        
            