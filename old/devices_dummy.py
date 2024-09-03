def get_port_list():
    port_list = [ "HEATER", "SENSOR" ]
    return port_list


class HP_66312A:
    addr = None
    connected = False

    def connect(self, addr):
        if addr == "HEATER":
            self.addr = addr
            self.connected = True
            self.reset()

    def set_current( self, current):
        self.current = current
        print("Heater: Current " + str(current))

    def set_voltage( self, voltage):
        self.voltage = voltage
        print("Heater: Voltage " + str(voltage))

    def say_hi( self ):
        print('Heater: ' + self.addr)

    def set_enabled( self, val ):
        self.enabled = val
        print("Heater: Enabled " + str(val))

    def reset( self ):
        print("Heater: Reset")
        self.set_enabled( False )
        self.set_current( 0 )
        self.set_voltage( 0 )

    def close( self ):
        self.reset()
        self.connected = False

from numpy.random import randn as randn
class thermistor_20K:
    addr = None
    connected = False

    def connect(self, addr):
        if addr == "SENSOR":
            self.addr = addr
            self.temp = 20
            self.connected = True

    def say_hi( self ):
        print('Sensor: ' + self.addr)

    def get_temp( self ):
        return self.temp + randn()

    def close( self ):
        self.connected = False
        self.addr = None
        self.temp = None