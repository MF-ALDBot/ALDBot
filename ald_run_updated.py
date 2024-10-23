from ScopeFoundry import Measurement
import time


class AldRunMeasure2(Measurement):
    
    name = 'ald_run_upd'
    
    def setup(self):
        
        self.settings.New('substrate_temp', dtype = int, unit='C', initial = 20)
        self.settings.New('process_pressure', dtype = int, unit  = 'mTorr', initial = 100, vmin = 0, vmax = 1500)
        self.settings.New('plasma_pressure', dtype = int, unit = 'mTorr', initial = 50, vmin = 0, vmax = 1500)
        self.settings.New('plasma_duration', dtype = int, unit = 'ms', initial = 1000)
        self.settings.New('precursor_dose_time', dtype = int, unit = 'ms', initial = 100, vmin = 0, vmax = 100)
        self.settings.New('ald_valves_delay', dtype = int, unit = 'ms', initial = 100)
        self.settings.New('precursor_purge_time', dtype = int, unit = 'ms', initial = 1000)
        self.settings.New('H2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('N2_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 86)
        self.settings.New('Ar_plasma_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('Ar_process_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('ALD_purge_flow_rate', dtype = int, unit = 'sccm', initial = 0, vmin = 0, vmax = 100)
        self.settings.New('plasma_purge_time', dtype = int, unit='s', initial = 10)
        self.settings.New('RF_power_setpoint', dtype=int, unit='Watt', initial = 100, vmin = 0, vmax = 300)
        self.settings.New('Number_of_ALD_cycles', dtype = int, vmin=1, initial = 100)
        
        self.maxigauge = self.app.hardware['Pfeiffer_MaxiGauge']
        self.vat = self.app.hardware['VAT_Valve']
        self.plc = self.app.hardware['productivity_plc']
        self.seren_ps = self.app.hardware['Seren_Power_Supply']
        self.seren_mc2 = self.app.hardware['Seren_Match_Box']
        
    def run(self):
        
        S = self.settings
        
        try:
            #Set ALD valve timings
            self.plc.settings['t1_Preset'] = S['precursor_dose_time']
            self.plc.settings['t_delay_Preset'] = S['ald_valves_delay']
            self.plc.settings['t2_Preset'] = S['precursor_purge_time']
            
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
            
            #Open the Ar plasma valve for pressure stabilization
            print('Opening the Ar valve for pressure stabilization...')
            self.plc.settings['Valve6_plasma_argon_open'] = True            
            
            #Set process pressure
            print('Trying to set process pressure...')
            if self.set_process_pressure(S['process_pressure'], timeout=10, tolerance = 4, stabilization_time=2.0):
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
            t0 = time.monotonic()
            tolerance = 4
            time.sleep(1)
            while True:
                current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
                if abs(current_pressure-S['plasma_pressure']) <= 0.5*tolerance:
                    break
                if time.monotonic() - t0 > 10.0:
                    raise ValueError("Error: Plasma pressure did not reach setpoint")
                time.sleep(0.1)
                        
            stabilization_start = time.monotonic()
            stabilization_time = 2.0
            while time.monotonic() - stabilization_start < stabilization_time:
                current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
                if not (S['plasma_pressure'] - tolerance <= current_pressure <= S['plasma_pressure'] + tolerance):
                    raise ValueError('Plasma pressure failed to stabilize')
                time.sleep(0.050)
                
            print(f"Plasma pressure stable for {stabilization_time} seconds. Proceeding...")
            
            #Strike plasma
            self.seren_ps.settings['RF_enable'] = True
        
            # TODO This should be a loop, things to check for: 
            t0 = time.monotonic()
            # plasma duration is in milliseconds
            plasma_duration_sec = S['plasma_duration']/1000.
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
            
            """
            self.seren_mc2.settings['set_lc_preset_position'] = plasma_lc_position
            self.seren_mc2.settings['set_tc_preset_position'] = plasma_tc_position
            self.seren_mc2.goto()
            """
                        
            self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
            self.plc.settings['MFC1_H2_SP_sccm'] = 0
            self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
            self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0                         
            
            #Open the ALD purge flow
            self.plc.settings['Valve7_ald_pneumatic_purge_open'] = True
            self.plc.settings['MFC4_ALD_purge_SP_sccm'] = S['ALD_purge_flow_rate']
            
            #The ALD Loop
            print('Starting the ALD loop...')
            for i in range(S['Number_of_ALD_cycles']):
                print("ALD Cycle", i+1, 'of', S['Number_of_ALD_cycles'])
                
                if self.interrupt_measurement_called:
                    break
                
                """
                #Open window purges
                print('Opening the window purge valve...')
                self.plc.settings['Valve8_window_purge_open'] = True
                """
                #Open flow, set the position of the VAT valve
                self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
                self.vat.settings.target_position.update_value(process_vat_position)
                self.vat.settings.target_position.write_to_hardware()
                
                #Time to stabilize
                time.sleep(1)
                
                ## MO Dose phase
                #ALD Valves Sequence
                print('Starting the ALD valve sequence...')
                self.plc.settings['start_ALD_Valve1_dose'] = True
                     
                while self.plc.settings['start_ALD_Valve1_dose']:
                    if self.interrupt_measurement_called:
                        break
                    #===============================================================
                    # Add a timeout here? YES
                    #===============================================================                
                
                ## Plasma Prep Phase
                
                #Set plasma VAT position
                self.vat.settings.target_position.update_value(plasma_vat_position)
                self.vat.settings.target_position.write_to_hardware()
                
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

                #Time to stabilize
                time.sleep(1)
                
                if self.interrupt_measurement_called:
                    break
                
                #Strike plasma
                self.seren_ps.settings['RF_enable'] = True
        
                # TODO This should be a loop, things to check for: 
                t0 = time.monotonic()
                # plasma duration is in milliseconds
                plasma_duration_sec = S['plasma_duration']/1000.
                while (time.monotonic() - t0) < plasma_duration_sec:
                    if self.interrupt_measurement_called:
                        break
                    time.sleep(0.010)
                # plasma done
                self.seren_ps.settings['RF_enable'] = False
                
                if self.interrupt_measurement_called:
                    break
                
                
                self.plc.settings['Valve4_plasma_process_gas_open'] = False # MFC1 pre-valve close
                self.plc.settings['MFC1_H2_SP_sccm'] = 0
                self.plc.settings['Valve5_plasma_nitrogen_open'] = False # MFC2 pre-valve close
                self.plc.settings['MFC2_N2_plasma_SP_sccm'] = 0            
                # Note we leave Ar valve and MFC open for purge throughout ALD run
                
                
                # #Plasma purge (needle valve)
                # self.plc.settings['Valve3_plasma_purge_open'] = True
                #
                # t0 = time.monotonic()
                # while (time.monotonic() - t0) < S['plasma_purge_time']:
                #     # do stuff
                #     time.sleep(0.010)
                #
                # self.plc.settings['Valve3_plasma_purge_open'] = False
                
                                
        except Exception as err:
            print("Process Stopped because of error:", err)
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
            
    def set_process_pressure(self, target_pressure, timeout, tolerance=2., interval=0.100, stabilization_time = 5):    
        
        #self.vat.settings['target_pressure'] = target_pressure
        self.vat.settings.target_pressure.update_value(target_pressure, update_hardware=True)
        self.vat.settings.target_pressure.write_to_hardware()
        self.plc.settings['MFC3_Ar_plasma_SP_sccm'] = self.settings['Ar_process_flow_rate']
        
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
        while time.monotonic() - stabilization_start < stabilization_time:
            current_pressure = self.vat.settings.actual_pressure.read_from_hardware()
            if not (target_pressure - tolerance <= current_pressure <= target_pressure + tolerance):
                print('Process pressure failed to stabilize')
                return False
            time.sleep(interval)
            
        print(f"Process pressure stable for {stabilization_time} seconds. Proceeding...")
        return True
            
                
        

        
            