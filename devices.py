import time,sys
from PyQt5.QtCore import (pyqtSignal, QObject, QThread)

if '-verbose' in sys.argv:
    verbose = True
else:
    verbose = False

if '-dev' in sys.argv:
    print( 'DEV MODE: Dummy Devices' )
    verbose = True
    from dummy_stuff import ResourceManager
else:
    from pyvisa import ResourceManager


rm = ResourceManager()
    
def get_port_list():   
    port_list = rm.list_resources()
    return port_list

class Device(QObject):
    m_thread = None
    address = None
    connected = False
    dev_type = None
    status = 'NOT-READY'
    time_interval = 0

    signal_connected = pyqtSignal( bool )
    signal_status = pyqtSignal( str)

    finished = pyqtSignal()

    def __init__(self):
        # Inherit QObject
        super().__init__()

    ## Abstract Methods
    def dev_check(self):
        print('ERROR: dev_check NOT IMPLEMENTED')
        pass

    def while_listening(self):
        print('ERROR: while_listening NOT IMPLEMENTED')
        pass

    def reset(self):
        print('ERROR: reset NOT IMPLEMENTED')

    ## Common Concrete Method
    def start_comm( self ):
        while True:
            cur_status = self.status
            try:
                if cur_status == "LISTENING":
                    self.while_listening()
            except Exception as e:
                print(e)
                self.run_emergency()
                return
                        
            if cur_status == "DISCONNECT":
                print( "DISCONNECTING " +self.dev_type)
                self.disconnect()
                break

            if self.time_interval>0:
                time.sleep(self.time_interval)
        
        self.set_status( "NOT-READY" )
        # Return Board to main thread before finishing
        self.moveToThread( self.thread_main )
        QThread.currentThread().quit()

    def connect( self, addr ):
        self.device = rm.open_resource( addr )
        if not self.dev_check():
            print( 'Invalid Device, closing')
            self.device.close()
        else:
            self.addr = addr
            self.set_connected( True )
            self.set_status( 'LISTENING' )
            self.reset()

    def disconnect( self ):
        self.reset()
        self.set_connected(False)
        self.device.close()
        self.address = None
        self.dev_type = None
        self.status = 'NOT-READY'
        self.device = None


    def returnThreadToMain( self, main_thread ):
        self.moveToThread( main_thread )

    def set_connected( self, val ):
        self.connected = val
        self.signal_connected.emit( val )

    def run_emergency( self ):
        self.disconnect()
        self.set_status( "NOT-READY" )
        self.moveToThread( self.thread_main )
        QThread.currentThread().quit()
        
    def set_status( self, value ):
        self.status = value
        self.signal_status.emit( value )

    def write( self, val ):
        if verbose:
            print("SENDING: "+ val)
        self.device.write( val )

    def close( self ):
        self.set_status( "DISCONNECT")
        while self.status == "DISCONNECT":
            time.sleep(0.01)
        self.device.close()


class Heater(Device):

    changed_enabled = False
    changed_current = False
    changed_voltage = False

    def __init__(self):
        super().__init__() #Inherit QObject

    def dev_check(self):
        # Check if XPD_1830
        id = self.device.query( 'ID?').split(' ')
        if len(id) > 1 and id[1].startswith( 'XPD18-30' ):
            self.dev_type = "XPD_1830"
            self.MAX_CURRENT = 6
            self.MAX_VOLTAGE = 1.9
            self.get_msg_voltage = lambda V: f'VSET %f' %V
            self.get_msg_current = lambda I: f'ISET %f' %I
            self.get_msg_enabled = lambda E: f'FOLD 1; OUT %d' % E
            return True
        
        # Check if HP66312_A
        id = self.device.query( '*IDN?').split(',')
        print(id)
        if  len(id) > 1 and id[0].startswith( 'HEWLETT-PACKARD' ) and id[1] == '66312A':
            self.dev_type = "HP66312A"
            self.MAX_CURRENT = 2
            self.MAX_VOLTAGE = 1.9
            self.get_msg_voltage = lambda V: f'VOUT %f' %V
            self.get_msg_current = lambda I: f'CURR %f' %I
            self.get_msg_enabled = lambda E: f'OUTP %d' %E
            return True
        
        # Otherwise return False
        return False

    def while_listening(self):
        if self.changed_voltage:
            self.write( self.get_msg_voltage(self.voltage) )
            self.changed_voltage = False
        if self.changed_current:
            self.write( self.get_msg_current(self.current) )
            self.changed_current = False
        if self.changed_enabled:
            self.write( self.get_msg_enabled(self.enabled) )
            self.changed_enabled = False

    def set_enabled( self, val ):
        self.enabled = val
        self.changed_enabled = True
    def set_current( self, val ):
        self.current = val
        self.changed_current = True
    def set_voltage( self, val ):
        self.voltage = val
        self.changed_voltage = True

    def reset( self ):
        self.write("ERR?")
        self.write("SRQ?")
        self.write("RST")
        self.write( self.get_msg_enabled(0) )
        self.set_voltage( 0 )


class Sensor(Device):
    signal_temp = pyqtSignal( float )
    time_interval = 0.1
    def __init__(self):
        super().__init__() #Inherit QObject

    def dev_check(self):
        # Check if Correct Device
        id = self.device.query( '*' ).split(' ')
        if id[0] == 'Thermistor':
            if id[1].startswith( '20kOhm' ):
                self.dev_type = 'Thermistor 20kOhm'
                return True
        print( id )
        return False

    def while_listening(self):
        self.signal_temp.emit( self.get_temp() )

    def get_temp( self ):
        self.temp =  float(self.device.query('t'))
        return self.temp    
    
    def reset(self):
        pass

