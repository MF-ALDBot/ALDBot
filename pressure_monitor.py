from ScopeFoundry.measurement import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
import os


class Pressure_monitor(Measurement):
    
    name = 'pressure_monitor'
    
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__,"vat_maxigauge.ui")
        ui = self.ui = load_qt_ui_file(self.ui_filename)
        
        self.vat = self.app.hardware['VAT_Valve']
        
        self.vat.settings.connected.connect_to_widget(
            ui.VAThw_checkbox)
        
        self.vat.settings.read_position.connect_to_widget(
            ui.readpos_doubleSpinBox)
        
        self.vat.settings.write_position.connect_to_widget(
            ui.setpos_doubleSpinBox)
        
        self.vat.settings.status.connect_to_widget(
            ui.statusbar_label)
        
        self.gauge = self.app.hardware['Pfeiffer_MaxiGauge']
        
        self.gauge.settings.connected.connect_to_widget(
            ui.pfeifferhw_checkBox)
        
        self.gauge.settings.ch1_pressure_scaled.connect_to_widget(
            ui.pres1_doubleSpinBox)
        
        self.gauge.settings.ch2_pressure_scaled.connect_to_widget(
            ui.pres2_doubleSpinBox)
        
        self.gauge.settings.ch3_pressure_scaled.connect_to_widget(
            ui.pres3_doubleSpinBox)
        
        
        