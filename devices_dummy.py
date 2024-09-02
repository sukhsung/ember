class HP_66312A:
    def __init__(self, addr):
        self.addr = addr
        self.connected = True
        self.enabled = False
        self.set_current( 0 )
        self.set_voltage( 0 )

    def set_output( self, output):
        self.output = output

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
        self.enabled = False
        self.set_current( 0 )
        self.set_voltage( 0 )

    def close( self ):
        self.set_current( 0 )
        self.set_voltage( 0 )
        self.set_output( False )
        self.connected = False

class thermistor_20K:
    def __init__(self, addr):
        self.addr = addr
        self.temp = 20
        self.connected = True

    def say_hi( self ):
        print('Sensor: ' + self.addr)

    def get_temp( self ):
        return self.temp

    def close( self ):
        self.connected = False