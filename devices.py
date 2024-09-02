
import pyvisa
# import re, time



def get_port_list():
    """\
    Return a list of USB serial port devices.

    Entries in the list are ListPortInfo objects from the
    serial.tools.list_ports module.  Fields of interest include:

        device:  The device's full path name.
        vid:     The device's USB vendor ID value.
        pid:     The device's USB product ID value.
    """
    
    rm = pyvisa.ResourceManager()
    # port_list = [p.device for p in serial.tools.list_ports.comports() if p.vid]
    port_list = [ p for p in rm.list_resources()]
    
    # print(port_list)
    # print(visa_list)
    # port_list.append( visa_list)
    # port_list = ["HEATER", "SENSOR"]
    return port_list

class thermistor_20K:
    def __init__(self,addr):
        self.addr = addr
        # self.device = serial.Serial(addr)
        
        if addr == '':
            self.device = None
            self.connected = False
        else:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource( addr )
            
            # Check if device is correct
            if not self.dev_check():
                print( 'Device query is not matching Thermistor, closing connection')
                self.device.close()
                self.connected = False
            else:
                self.connected = True
                print( 'Connected to Thermistor')
                # self.setup_default()

    def dev_check(self):
        id = self.device.query( '*')
        return  id.startswith( '20K Ohm Thermistor')
    
    def get_temp( self ):
        self.temp =  float(self.device.query( 't'))
        return self.temp    

    def say_hi( self ):
        print('Sensor: ' + self.addr)

    
    def close( self ):
        self.device.close()
        self.connected = False

    
class HP_66312A:
    
    def __init__(self, addr):
        self.addr = addr
        
        if addr == '':
            self.device = None
            self.connected = False
        else:

            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource( addr )

            # Check if device is correct
            if not self.dev_check():
                print( 'Device query is not matching Keithley 6220, closing connection')
                self.device.close()
                self.connected = False
            else:
                print( 'Connected to Keithley 6220')
                self.connected = True
                # self.setup_default()


    def dev_check(self):
        id = self.device.query( '*IDN?').split(',')
        return  id[0].startswith( 'HEWLETT-PACKARD' ) and id[1] == '66312A'
    
    def set_current( self, current):
        if current > 6:
            current = 6
        elif current < 0:
            current = 0

        self.current = current
        self.device.write( f'CURR %f' % current)

    def set_voltage( self, voltage):
        if voltage > 1.9:
            voltage = 1.9
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
        self.set_current( 0 )
        self.set_voltage( 0 )
        self.set_enabled( False )
        self.device.close()