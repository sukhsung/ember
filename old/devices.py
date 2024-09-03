import pyvisa
import time

def get_port_list():    
    rm = pyvisa.ResourceManager()
    port_list = [ p for p in rm.list_resources()]
    return port_list

class XPD_1830:
    addr = None
    connected = False
    MAX_CURRENT = 6
    MAX_VOLTAGE = 1.9
    
    def connect(self, addr):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource( addr )

        # Check if device is correct
        if not self.dev_check():
            print( 'Device query is not matching XPD-1830, closing connection')
            self.device.close()
            self.connected = False
        else:
            print( 'Connected to XPD-1830')
            self.addr = addr
            self.connected = True
            self.reset()


    def dev_check(self):
        id = self.device.query( 'ID?').split(' ')
        print( id )
        return  id[1].startswith( 'XPD18-30' )
    
    def set_current( self, current):
        if current > self.MAX_CURRENT:
            current = self.MAX_CURRENT
        elif current < 0:
            current = 0

        self.current = current
        self.device.write( f'ISET %f' % current)

    def set_voltage( self, voltage):
        if voltage > self.MAX_VOLTAGE:
            voltage = self.MAX_VOLTAGE
        elif voltage < 0:
            voltage = 0
        print( voltage )
        self.voltage = voltage
        time.sleep(0.5)
        # self.device.write( f'VSET %f' % voltage)

    def set_enabled( self, output):
        self.enabled = output
        self.device.write( f'OUT %d' % int(output))

    def test_func( self ):
        print( "pause!")
        time.sleep(0.5)

    def say_hi( self ):
        print('Heater: ' + self.addr)

    def reset( self ):
        print("Heater: Reset")
        self.device.write( 'RST' )
        self.device.write( f'FOLD 1')
        self.set_enabled( False )

    def close( self ):
        self.reset()
        self.connected = False
        self.device.close()


class HP_66312A:
    addr = None
    connected = False
    MAX_CURRENT = 6
    MAX_VOLTAGE = 1.9
    
    def connect(self, addr):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource( addr )

        # Check if device is correct
        if not self.dev_check():
            print( 'Device query is not matching HP-66312A, closing connection')
            self.device.close()
            self.connected = False
        else:
            print( 'Connected to HP-66312A')
            self.addr = addr
            self.connected = True
            self.reset()


    def dev_check(self):
        id = self.device.query( '*IDN?').split(',')
        return  id[0].startswith( 'HEWLETT-PACKARD' ) and id[1] == '66312A'
    
    def set_current( self, current):
        if current > self.MAX_CURRENT:
            current = self.MAX_CURRENT
        elif current < 0:
            current = 0

        self.current = current
        self.device.write( f'CURR %f' % current)

    def set_voltage( self, voltage):
        if voltage > self.MAX_VOLTAGE:
            voltage = self.MAX_VOLTAGE
        elif voltage < 0:
            voltage = 0

        self.voltage = voltage
        self.device.write( f'VOLT %f' % voltage)

    def set_enabled( self, output):
        self.enabled = output
        if output is True:
            self.device.write( 'OUTP ON')
        else:
            self.device.write( 'OUTP OFF')

    def say_hi( self ):
        print('Heater: ' + self.addr)

    def reset( self ):
        print("Heater: Reset")
        self.set_enabled( False )
        self.set_current( 0 )
        self.set_voltage( 0 )

    def close( self ):
        self.reset()
        self.connected = False
        self.device.close()

class thermistor_20K:
    addr = None
    connected = False

    def connect(self,addr):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource( addr )

        # Check if device is correct
        if not self.dev_check():
            print( 'Device query is not matching Thermistor, closing connection')
            self.device.close()
            self.connected = False
        else:
            print( 'Connected to 20K Ohm Thermistor' )
            self.addr = addr
            self.connected = True

    def dev_check(self):
        id = self.device.query( '*' )
        return  id.startswith( '20K Ohm Thermistor' )
    
    def get_temp( self ):
        self.temp =  float(self.device.query('t'))
        return self.temp    

    def say_hi( self ):
        print('Sensor: ' + self.addr)

    def close( self ):
        self.connected = False
        self.addr = None
        self.temp = None
        self.device.close()

    