from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
import time


class ALDBot_UI2(Measurement):
    
    name = 'ald_ui2'
    
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__,"aldbot_gui2.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)

        self.vat = self.app.hardware['VAT_Valve']
        
        self.vat.settings.connected.connect_to_widget(
            ui.vat_valve_connect_checkBox)
        
        self.vat.settings.read_position.connect_to_widget(
            ui.vat_read_position_doubleSpinBox)
        
        self.vat.settings.write_position.connect_to_widget(
            ui.vat_set_position_doubleSpinBox)
        
        # self.vat.settings.status.connect_to_widget(
        #     ui.statusbar_label)
        
        self.gauge = self.app.hardware['Pfeiffer_MaxiGauge']
        
        self.gauge.settings.connected.connect_to_widget(
            ui.maxigauge_connect_checkBox)
        
        self.gauge.settings.ch1_pressure_scaled.connect_to_widget(
            ui.maxi_gauge1_doubleSpinBox)
        
        self.gauge.settings.ch2_pressure_scaled.connect_to_widget(
            ui.maxi_gauge2_doubleSpinBox)
        
        self.gauge.settings.ch3_pressure_scaled.connect_to_widget(
            ui.maxi_gauge3_doubleSpinBox)
        
        self.plc = self.app.hardware['productivity_plc']
        
        self.plc.settings.connected.connect_to_widget(
            ui.plc_connect_checkBox)
        
        self.plc.settings.MFC1_H2_PV_sccm.connect_to_widget(
            ui.mfc1_flow_doubleSpinBox)
        
        self.plc.settings.MFC2_Ar_PV_sccm.connect_to_widget(
            ui.mfc2_flow_doubleSpinBox)
        
        self.plc.settings.MFC3_N2_plasma_PV_sccm.connect_to_widget(
            ui.mfc3_flow_doubleSpinBox)
        
        self.plc.settings.MFC4_N2_ALD_PV_sccm.connect_to_widget(
            ui.mfc4_flow_doubleSpinBox)
        
        self.plc.settings.MFC1_H2_SP_sccm.connect_to_widget(
            ui.mfc1_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC2_Ar_SP_sccm.connect_to_widget(
            ui.mfc2_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC3_N2_plasma_SP_sccm.connect_to_widget(
            ui.mfc3_setpoint_doubleSpinBox)
        
        self.plc.settings.MFC4_N2_ALD_SP_sccm.connect_to_widget(
            ui.mfc4_setpoint_doubleSpinBox)
        
        self.plc.settings.BNC1_baritron_gauge_mV.connect_to_widget(
            ui.baritron_gauge_doubleSpinBox)
        
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
        
        ui.ald_valves_pushButton.clicked.connect(
            self.open_valve1)
        
        #=======================================================================
        # ui.ald2_pushButton.clicked.connect(
        #     self.open_valve2)
        # 
        # ui.ald3_pushButton.clicked.connect(
        #     self.open_valve3)
        #=======================================================================
        
        ui.valve_plasma_purge_checkBox.stateChanged.connect(self.toggle_valve3)
        ui.valve_h2_checkBox.stateChanged.connect(self.toggle_valve4)
        ui.valve_ar_checkBox.stateChanged.connect(self.toggle_valve5)
        ui.valve_n2_plasma_checkBox.stateChanged.connect(self.toggle_valve6)
        ui.valve_n2_ald_checkBox.stateChanged.connect(self.toggle_valve7)
        ui.valve_window_purge_checkBox.stateChanged.connect(self.toggle_valve8)
        
        
        
    def open_valve1(self):
        self.plc.settings['Valve1_open'] = True
            
    #===========================================================================
    # def open_valve2(self):
    #     self.plc.settings['Valve2_open'] = True
    #         
    # def open_valve3(self):
    #     self.plc.settings['Valve1_open'] = True
    #===========================================================================
        
    def toggle_valve3(self, state):
        if state == 2:  # Checked
            self.plc.settings['Valve3_close'] = False
            self.plc.settings['Valve3_open'] = True
        else:  # Unchecked
            self.plc.settings['Valve3_open'] = False
            self.plc.settings['Valve3_close'] = True
    
    def toggle_valve4(self, state):
        if state == 2:  # Checked
            self.plc.settings['Valve4_close'] = False
            self.plc.settings['Valve4_open'] = True
        else:  # Unchecked
            self.plc.settings['Valve4_open'] = False
            self.plc.settings['Valve4_close'] = True
    
    def toggle_valve5(self, state):
        if state == 2:
            self.plc.settings['Valve5_close'] = False
            self.plc.settings['Valve5_open'] = True
        else:
            self.plc.settings['Valve5_open'] = False
            self.plc.settings['Valve5_close'] = True
    
    def toggle_valve6(self, state):
        if state == 2:
            self.plc.settings['Valve6_close'] = False
            self.plc.settings['Valve6_open'] = True
        else:
            self.plc.settings['Valve6_open'] = False
            self.plc.settings['Valve6_close'] = True
    
    def toggle_valve7(self, state):
        if state == 2:
            self.plc.settings['Valve7_close'] = False
            self.plc.settings['Valve7_open'] = True
        else:
            self.plc.settings['Valve7_open'] = False
            self.plc.settings['Valve7_close'] = True
    
    def toggle_valve8(self, state):
        if state == 2:
            self.plc.settings['Valve8_close'] = False
            self.plc.settings['Valve8_open'] = True
        else:
            self.plc.settings['Valve8_open'] = False
            self.plc.settings['Valve8_close'] = True
                    