from ScopeFoundry import BaseMicroscopeApp

class ALDBotApp(BaseMicroscopeApp):
    
    name = 'ALDBot'
    
    def setup(self):
        
        from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_hw import VAT_Throttle_HW
        self.add_hardware(VAT_Throttle_HW(self, name='VAT_Valve'))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
        self.add_hardware(Pfeiffer_VGC_Hardware(self, name='Pfeiffer_MaxiGauge'))
        
        # from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_measure import VAT_Throttle_Measure
        # self.add_measurement(VAT_Throttle_Measure(self))  
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_measure import Pfeiffer_VGC_Measure
        self.add_measurement(Pfeiffer_VGC_Measure(self))
        
        from ALDbot.pressure_monitor import Pressure_monitor
        self.add_measurement(Pressure_monitor(self))  
        
        
if __name__ == '__main__':
    import sys
    app = ALDBotApp(sys.argv)
    app.exec_()
