from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.productivity_plc.productivity_plc import ProductivityPLC


class ALDBotApp(BaseMicroscopeApp):
    
    name = 'ALDBot'
    
    def setup(self):
        
        from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_hw import VAT_Throttle_HW
        self.add_hardware(VAT_Throttle_HW(self, name='VAT_Valve'))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
        self.add_hardware(Pfeiffer_VGC_Hardware(self, name='Pfeiffer_MaxiGauge'))
        #
        #
        # from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_measure import Pfeiffer_VGC_Measure
        # self.add_measurement(Pfeiffer_VGC_Measure(self))
        
        self.add_hardware(ProductivityPLC(self, tags_csv_filename="ald_test_extended.csv"))
        
        from ald_gui2 import ALDBot_UI2
        self.add_measurement(ALDBot_UI2(self))
        
        from aldbot_logger_measure import ALDBotLoggerMeaure
        self.add_measurement(ALDBotLoggerMeaure(self)) 
        
        
if __name__ == '__main__':
    import sys
    app = ALDBotApp(sys.argv)
    app.exec_()
