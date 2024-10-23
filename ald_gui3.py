from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class ALDBot_UI3(Measurement):
    
    name = 'ald_ui3'
    
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__,"aldbot_gui3.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)

        self.vat = self.app.hardware['VAT_Valve']
        
        self.vat.settings.connected.connect_to_widget(
            ui.vat_valve_connect_checkBox)
        
        self.vat.settings.actual_position.connect_to_widget(
            ui.vat_read_position_doubleSpinBox)
        
        self.vat.settings.target_position.connect_to_widget(
            ui.vat_set_position_doubleSpinBox)
        
        self.vat.settings.target_pressure.connect_to_widget(
            ui.vat_set_pressure_doubleSpinBox)
        
        self.vat.settings.actual_pressure.connect_to_widget(
            ui.vat_read_pressure_doubleSpinBox)
                
        
        self.gauge = self.app.hardware['Pfeiffer_MaxiGauge']
        
        self.gauge.settings.connected.connect_to_widget(
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
            pressure_value = self.gauge.settings['ch1_pressure_scaled']
            formatted_value = si_format(pressure_value, unit='torr')
            ui.gauge1_label.setText(formatted_value)
        
        self.gauge.settings.ch1_pressure_scaled.add_listener(update_gauge1_display)
        
        def update_gauge2_display():
            pressure_value = self.gauge.settings['ch2_pressure_scaled']
            formatted_value = si_format(pressure_value, unit='torr')
            ui.gauge2_label.setText(formatted_value)
        
        self.gauge.settings.ch2_pressure_scaled.add_listener(update_gauge2_display)
        
        def update_gauge3_display():
            pressure_value = self.gauge.settings['ch3_pressure_scaled']
            formatted_value = si_format(pressure_value, unit='torr')
            ui.gauge3_label.setText(formatted_value)
        
        self.gauge.settings.ch3_pressure_scaled.add_listener(update_gauge3_display)
        
        self.seren_power = self.app.hardware['Seren_Power_Supply']
        
        self.seren_power.settings.connected.connect_to_widget(
            ui.seren_power_supply_connect_checkBox)
        
        self.seren_power.settings.set_forward_power.connect_to_widget(
            ui.set_rf_power_doubleSpinBox)
        
        self.seren_power.settings.RF_enable.connect_to_widget(
            ui.RF_enable_checkBox)
        
        
        self.seren_mc2 = self.app.hardware['Seren_Match_Box']
        
        self.seren_mc2.settings.connected.connect_to_widget(
            ui.seren_mc2_connect_checkBox)
        
        self.seren_mc2.settings.set_lc_preset_position.connect_to_widget(
            ui.lc_preset_doubleSpinBox)
        
        self.seren_mc2.settings.set_tc_preset_position.connect_to_widget(
            ui.tc_preset_doubleSpinBox)
        
        self.seren_mc2.settings.LC_auto.connect_to_widget(
            ui.lc_auto_checkBox)
        
        self.seren_mc2.settings.TC_auto.connect_to_widget(
            ui.tc_auto_checkBox)
        
        ui.mc2_goto_preset_pushButton.clicked.connect(
            self.seren_mc2.goto)
        
        
        self.plc = self.app.hardware['productivity_plc']
        
        self.plc.settings.connected.connect_to_widget(
            ui.plc_connect_checkBox)
        
        self.plc.settings.MFC1_H2_PV_sccm.connect_to_widget(
            ui.mfc1_h2_flow_doubleSpinBox)
        
        self.plc.settings.MFC2_N2_plasma_PV_sccm.connect_to_widget(
            ui.mfc2_n2_plasma_flow_doubleSpinBox)
        
        self.plc.settings.MFC3_Ar_plasma_PV_sccm.connect_to_widget(
            ui.mfc3_Ar_plasma_flow_doubleSpinBox)
        
        self.plc.settings.MFC4_ALD_purge_PV_sccm.connect_to_widget(
            ui.mfc4_ald_purge_flow_doubleSpinBox)
        
        self.plc.settings.MFC1_H2_SP_sccm.connect_to_widget(
            ui.mfc1_h2_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC2_N2_plasma_SP_sccm.connect_to_widget(
            ui.mfc2_n2_plasma_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC3_Ar_plasma_SP_sccm.connect_to_widget(
            ui.mfc3_Ar_plasma_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC4_ALD_purge_SP_sccm.connect_to_widget(
            ui.mfc4_ald_purge_setpoint_doubleSpinBox)
        
        self.plc.settings.BNC1_baritron_gauge_mTorr.connect_to_widget(
            ui.baritron_gauge_label)
        
        #=======================================================================
        # self.plc.settings.BNC2_mV.connect_to_widget(
        #     ui.bnc2_read_doubleSpinBox)
        # 
        # self.plc.settings.BNC3_mV.connect_to_widget(
        #     ui.bnc3_read_doubleSpinBox)
        # 
        # self.plc.settings.BNC4_mV.connect_to_widget(
        #     ui.bnc4_read_doubleSpinBox)
        #=======================================================================
        
        #=======================================================================
        # self.plc.settings.t1_Preset.connect_to_widget(
        #     ui.ald1_time_doubleSpinBox)
        # 
        # self.plc.settings.t2_Preset.connect_to_widget(
        #     ui.ald2_time_doubleSpinBox)
        # 
        # self.plc.settings.t3_Preset.connect_to_widget(
        #     ui.ald3_time_doubleSpinBox)
        #=======================================================================
        
        def open_valve1():
            self.plc.settings['start_ALD_Valve1_dose'] = True
        ui.ald_valves_pushButton.clicked.connect(
            open_valve1)
        
        #=======================================================================
        # ui.ald2_pushButton.clicked.connect(
        #     self.open_valve2)
        # 
        # ui.ald3_pushButton.clicked.connect(
        #     self.open_valve3)
        #=======================================================================
        self.plc.settings.Valve2_ALD_purge_open.connect_to_widget(ui.valve_ald_purge_checkBox)
        self.plc.settings.Valve3_plasma_purge_open.connect_to_widget(ui.valve_plasma_purge_checkBox)
        self.plc.settings.Valve4_plasma_process_gas_open.connect_to_widget(ui.valve_h2_checkBox)
        self.plc.settings.Valve5_plasma_nitrogen_open.connect_to_widget(ui.valve_n2_plasma_checkBox)
        self.plc.settings.Valve6_plasma_argon_open.connect_to_widget(ui.valve_ar_plasma_checkBox)           
        self.plc.settings.Valve7_ald_pneumatic_purge_open.connect_to_widget(ui.valve_ald_purge_pneumatic_checkBox)
        self.plc.settings.Valve8_window_purge_open.connect_to_widget(ui.valve_window_purge_checkBox)
        
        