from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.ALD.Seren_matching_box.seren_mc2_hw import Seren_MC2_HW
from ScopeFoundryHW.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
from ScopeFoundryHW.pfeiffer_vgc.pfeiffer_mpt200_hw import PfeifferVacuumMPT200MultiHW
from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_hw import VAT_Throttle_HW
from ScopeFoundryHW.ALD.Seren.seren_hw import Seren_HW
from ScopeFoundryHW.filmsense_ellipsometer.filmsense_ellipsometer_hw import Filmsense_Ellipsometer_HW
from ScopeFoundryHW.productivity_plc.productivity_plc import ProductivityPLC
from ScopeFoundryHW.data_streamer.influxdb_lq_data_streamer_hw import InfluxDB_LQ_StreamerHW
from ScopeFoundryHW.oceanoptics_spec.oo_spec_odirect_hw import OceanOpticsSpectrometerODirectHW
from ScopeFoundryHW.oceanoptics_spec.oo_spec_measure import OOSpecLive
from ScopeFoundryHW.mf_crucible.mf_crucible_hw import MFCrucibleHW
from ScopeFoundryHW.mf_crucible.mf_crucible_controlpanel import MFCrucibleControlPanel
from aldbot_logger_measure import ALDBotLoggerMeaure
from ald_run_measure import AldRunMeasure
from ald_gui import ALDBot_UI
from ald_robot_measure import ALDRobot
from ald_robot_random_exps import ALDRobotRNG
from ald_robot_fixedParams_exps import ALDRobotFIX
from ald_param_sweep_measure import ALDRobotSweep
from ScopeFoundryHW.pico_tc08 import pico_tc08_hw

class ALDBotApp(BaseMicroscopeApp):
    
    name = 'ALDBot'
    
    def setup(self):
        
        
        self.add_hardware(VAT_Throttle_HW(self, name='VAT_Valve'))        
        self.add_hardware(Pfeiffer_VGC_Hardware(self, name='Pfeiffer_MaxiGauge'))
        self.add_hardware(PfeifferVacuumMPT200MultiHW(self, name='Pfeiffer_Chamber_Gauge'))        
        self.add_hardware(Seren_HW(self, name='Seren_Power_Supply'))        
        self.add_hardware(Seren_MC2_HW(self, name='Seren_Match_Box'))
        self.add_hardware(ProductivityPLC(self, tags_csv_filename="aldbot_plc_firmware_Extended.csv"))       
        self.add_hardware(InfluxDB_LQ_StreamerHW(self))
        self.add_hardware(Filmsense_Ellipsometer_HW(self, name='filmsense_ellipsometer'))        
        spec_hw = self.add_hardware(OceanOpticsSpectrometerODirectHW(self))
        
        self.add_measurement(OOSpecLive(self))
        
        self.add_hardware(MFCrucibleHW(self))
        self.add_measurement(MFCrucibleControlPanel(self, 'mf_crucible'))
        self.add_measurement(ALDBotLoggerMeaure(self))
        self.add_measurement(AldRunMeasure(self, 'ald_run'))       
        self.add_measurement(ALDBot_UI(self))
        self.add_measurement(ALDRobot(self))
        self.add_measurement(ALDRobotRNG(self))
        self.add_measurement(ALDRobotFIX(self))
        self.add_measurement(ALDRobotSweep(self))
        
        self.add_hardware(pico_tc08_hw.PicoTC08_HW(self, 
            chan_names=["_", "_",
                        "_", "precursor1_backup",
                        "precursor1", "_", "_", "_"]))#"012_____8"))
        
        
        
        self.settings_load_ini("aldbot_defaults.ini")
        
        
if __name__ == '__main__':
    import sys
    app = ALDBotApp(sys.argv)
    app.exec_()
