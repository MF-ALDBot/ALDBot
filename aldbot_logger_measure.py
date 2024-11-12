from ScopeFoundry import Measurement
import pyqtgraph as pg
import time

class ALDBotLoggerMeaure(Measurement):
    
    name = 'ald_logger'
    
    def setup(self):
        
        pass
    

    def setup_figure(self):
                    
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        self.graph_layout.clear()
        self.first_display = True


    def update_display(self):

        if self.first_display:

            self.graph_layout.clear()


            self.plot_gauge1 = self.graph_layout.addPlot(0,0)
            self.plot_gauge2 = self.graph_layout.addPlot(1,0)
            self.plot_gauge3 = self.graph_layout.addPlot(2,0)


            self.gauge_plotlines = {}
            self.gauge_plotdata = {}
            
            self.gauge_plotlines['ch1_pressure_scaled'] = self.plot_gauge1.plot()
            self.gauge_plotdata['ch1_pressure_scaled'] = []
            
            self.gauge_plotlines['ch2_pressure_scaled'] = self.plot_gauge2.plot()
            self.gauge_plotdata['ch2_pressure_scaled'] = [] 
            
            self.gauge_plotlines['ch3_pressure_scaled'] = self.plot_gauge3.plot()
            self.gauge_plotdata['ch3_pressure_scaled'] = []     
 
            self.first_display = False
        
        for name in ['ch1_pressure_scaled', 'ch2_pressure_scaled', 'ch3_pressure_scaled']:
            self.gauge_plotlines[name].setData(self.gauge_plotdata[name])
    
    
    def run(self):
        self.first_display = True

        while not self.interrupt_measurement_called:
            
            pressure_gauge = self.app.hardware['Pfeiffer_MaxiGauge']
            
            for ch in ['ch1_pressure', 'ch2_pressure', 'ch3_pressure']:
                pressure_gauge.settings.get_lq(ch).read_from_hardware()
                dat = pressure_gauge.settings.get_lq(ch + "_scaled").value
                self.gauge_plotdata[ch + "_scaled"].append(dat)
                
                time.sleep(0.1)