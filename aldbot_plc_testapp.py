from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.productivity_plc.productivity_plc import ProductivityPLC


class TestApp(BaseMicroscopeApp):
    def setup(self):
        self.add_hardware(ProductivityPLC(self, tags_csv_filename="ald_test_extended.csv"))
       
app = TestApp()
app.exec_()