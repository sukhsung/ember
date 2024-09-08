

class ResourceManager:
    def list_resources(self):
        return ['XPD_1830', 'HP66312A', 'SENSOR']
    

    def open_resource(self, addr):
        if addr == 'XPD_1830':
            return XPD_1830()
        elif addr == 'HP66312A':
            return HP66312A()
        elif addr == 'SENSOR':
            return SENSOR()

class device_faux:
    def __init__(self):
        pass
    
    def write(self, msg):
        print( "RECEIVED: "+msg)
    def close(self):
        print('CLOSED')

class XPD_1830( device_faux):
    def __init__(self):
        super().__init__()

    def query(self,msg):
        if msg == 'ID?':
            return 'XANTREX XPD18-30'
        else:
            return ''
        
class HP66312A( device_faux):
    def __init__(self):
        super().__init__()

    def query(self,msg):
        if msg == '*IDN?':
            return 'HEWLETT-PACKARD,66312A'
        else:
            return ''

import numpy as np
class SENSOR( device_faux):
    def __init__(self):
        super().__init__()
        self.temp = 20
    def query(self,msg):
        if msg == '*':
            return 'Thermistor 20kOhm '
        elif msg == 't':
            # self.temp += np.random.randn()
            return str( self.temp + np.random.randn())
        else:
            return ''