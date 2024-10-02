from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
import time


class ALDBot_UI(Measurement):
    
    name = 'ald_ui'
    
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__,"aldbot.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)

        self.vat = self.app.hardware['VAT_Valve']
        
        self.vat.settings.connected.connect_to_widget(
            ui.vat_valve_connect_checkBox)
        
        self.vat.settings.read_position.connect_to_widget(
            ui.vat_read_doubleSpinBox)
        
        self.vat.settings.write_position.connect_to_widget(
            ui.vat_set_doubleSpinBox)
        
        # self.vat.settings.status.connect_to_widget(
        #     ui.statusbar_label)
        
        self.gauge = self.app.hardware['Pfeiffer_MaxiGauge']
        
        self.gauge.settings.connected.connect_to_widget(
            ui.maxigauge_connect_checkBox)
        
        self.gauge.settings.ch1_pressure_scaled.connect_to_widget(
            ui.gauge1_doubleSpinBox)
        
        self.gauge.settings.ch2_pressure_scaled.connect_to_widget(
            ui.gauge2_doubleSpinBox)
        
        self.gauge.settings.ch3_pressure_scaled.connect_to_widget(
            ui.gauge3_doubleSpinBox)
        
        self.plc = self.app.hardware['productivity_plc']
        
        self.plc.settings.connected.connect_to_widget(
            ui.plc_connect_checkBox)
        
        self.plc.settings.MFC1_H2_PV_sccm.connect_to_widget(
            ui.mfc1_read_doubleSpinBox)
        
        self.plc.settings.MFC2_Ar_PV_sccm.connect_to_widget(
            ui.mfc2_read_doubleSpinBox)
        
        self.plc.settings.MFC3_N2_plasma_PV_sccm.connect_to_widget(
            ui.mfc3_read_doubleSpinBox)
        
        self.plc.settings.MFC4_N2_ALD_PV_sccm.connect_to_widget(
            ui.mfc4_read_doubleSpinBox)
        
        self.plc.settings.MFC1_H2_SP_sccm.connect_to_widget(
            ui.mfc1_set_doubleSpinBox)
        
        self.plc.settings.MFC2_Ar_SP_sccm.connect_to_widget(
            ui.mfc2_set_doubleSpinBox)
        
        self.plc.settings.MFC3_N2_plasma_SP_sccm.connect_to_widget(
            ui.mfc3_set_doubleSpinBox)
        
        self.plc.settings.MFC4_N2_ALD_SP_sccm.connect_to_widget(
            ui.mfc4_set_doubleSpinBox)
        
        self.plc.settings.BNC1_baritron_gauge_mV.connect_to_widget(
            ui.bnc1_read_doubleSpinBox)
        
        self.plc.settings.BNC2_mV.connect_to_widget(
            ui.bnc2_read_doubleSpinBox)
        
        self.plc.settings.BNC3_mV.connect_to_widget(
            ui.bnc3_read_doubleSpinBox)
        
        self.plc.settings.BNC4_mV.connect_to_widget(
            ui.bnc4_read_doubleSpinBox)
        
        self.plc.settings.t1_Preset.connect_to_widget(
            ui.ald1_time_doubleSpinBox)
        
        self.plc.settings.t2_Preset.connect_to_widget(
            ui.ald2_time_doubleSpinBox)
        
        self.plc.settings.t3_Preset.connect_to_widget(
            ui.ald3_time_doubleSpinBox)
        
        ui.ald1_pushButton.clicked.connect(
            self.open_valve1)
        
        ui.ald2_pushButton.clicked.connect(
            self.open_valve2)
        
        ui.ald3_pushButton.clicked.connect(
            self.open_valve3)
        
        ui.valve4open_pushButton.clicked.connect(
            self.open_valve4)
        
        ui.valve4close_pushButton.clicked.connect(
            self.close_valve4)
        
        ui.valve5open_pushButton.clicked.connect(
            self.open_valve5)
        
        ui.valve5close_pushButton.clicked.connect(
            self.close_valve5)
        
        ui.valve6open_pushButton.clicked.connect(
            self.open_valve6)
        
        ui.valve6close_pushButton.clicked.connect(
            self.close_valve6)
        
        ui.valve7open_pushButton.clicked.connect(
            self.open_valve7)
        
        ui.valve7close_pushButton.clicked.connect(
            self.close_valve7)
        
        ui.valve8open_pushButton.clicked.connect(
            self.open_valve8)
        
        ui.valve8close_pushButton.clicked.connect(
            self.close_valve8)
        
        
        
    def open_valve1(self):
        self.plc.settings['Valve1_open'] = True
            
    def open_valve2(self):
        self.plc.settings['Valve2_open'] = True
            
    def open_valve3(self):
        self.plc.settings['Valve1_open'] = True
        
    def open_valve4(self):
        self.plc.settings['Valve4_close'] = False
        self.plc.settings['Valve4_open'] = True
    
    def open_valve5(self):
        self.plc.settings['Valve5_close'] = False
        self.plc.settings['Valve5_open'] = True
        
    def open_valve6(self):
        self.plc.settings['Valve6_close'] = False
        self.plc.settings['Valve6_open'] = True
        
    def open_valve7(self):
        self.plc.settings['Valve7_close'] = False
        self.plc.settings['Valve7_open'] = True
        
    def open_valve8(self):
        self.plc.settings['Valve8_close'] = False
        self.plc.settings['Valve8_open'] = True
        
    def close_valve4(self):
        self.plc.settings['Valve4_open'] = False
        self.plc.settings['Valve4_close'] = True
        
    def close_valve5(self):
        self.plc.settings['Valve5_open'] = False
        self.plc.settings['Valve5_close'] = True
        
    def close_valve6(self):
        self.plc.settings['Valve6_open'] = False
        self.plc.settings['Valve6_close'] = True
        
    def close_valve7(self):
        self.plc.settings['Valve7_open'] = False
        self.plc.settings['Valve7_close'] = True
        
    def close_valve8(self):
        self.plc.settings['Valve8_open'] = False
        self.plc.settings['Valve8_close'] = True
                
       