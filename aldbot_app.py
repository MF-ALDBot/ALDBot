from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.productivity_plc.productivity_plc import ProductivityPLC
from ScopeFoundryHW.data_streamer.influxdb_lq_data_streamer_hw import InfluxDB_LQ_StreamerHW
from ScopeFoundryHW.oceanoptics_spec.oo_spec_odirect_hw import OceanOpticsSpectrometerODirectHW
from ScopeFoundryHW.oceanoptics_spec.oo_spec_measure import OOSpecLive

class ALDBotApp(BaseMicroscopeApp):
    
    name = 'ALDBot'
    
    def setup(self):
        
        from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_hw import VAT_Throttle_HW
        self.add_hardware(VAT_Throttle_HW(self, name='VAT_Valve'))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
        self.add_hardware(Pfeiffer_VGC_Hardware(self, name='Pfeiffer_MaxiGauge'))
        
        from ScopeFoundryHW.ALD.Seren.seren_hw import Seren_HW
        self.add_hardware(Seren_HW(self, name='Seren_Power_Supply'))
        
        from ScopeFoundryHW.ALD.Seren_matching_box.seren_mc2_hw import Seren_MC2_HW
        self.add_hardware(Seren_MC2_HW(self, name='Seren_Match_Box'))
        #
        #
        # from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_measure import Pfeiffer_VGC_Measure
        # self.add_measurement(Pfeiffer_VGC_Measure(self))
        
        self.add_hardware(ProductivityPLC(self, tags_csv_filename="ald_test_extended.csv"))
        
        self.add_hardware(InfluxDB_LQ_StreamerHW(self))
        
        spec_hw = self.add_hardware(OceanOpticsSpectrometerODirectHW(self))
        self.add_measurement(OOSpecLive(self))

        
        from aldbot_logger_measure import ALDBotLoggerMeaure
        self.add_measurement(ALDBotLoggerMeaure(self))
        
        from ald_run import AldRunMeasure
        self.add_measurement(AldRunMeasure(self))
        
        from ald_run_updated import AldRunMeasure2
        self.add_measurement(AldRunMeasure2(self))
        
        
        from ald_gui3 import ALDBot_UI3
        self.add_measurement(ALDBot_UI3(self))
        
        
        self.settings_load_ini("aldbot_defaults.ini")
        
        
if __name__ == '__main__':
    import sys
    app = ALDBotApp(sys.argv)
    app.exec_()
