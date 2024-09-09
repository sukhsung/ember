import pyvisa
import time
from PyQt5.QtCore import (pyqtSignal, QObject)


def get_port_list():    
    rm = pyvisa.ResourceManager()
    port_list = [ p for p in rm.list_resources()]
    return port_list


class Heater(QObject):
    addr = None
    connected = False
    ID = None
    status = 'NOT-READY'
    msg = ""

    signal_connected = pyqtSignal( bool )
    signal_status = pyqtSignal( str)

    changed_enabled = False
    changed_current = False
    changed_voltage = False

    def __init__(self):
        super().__init__() #Inherit QObject


    def connect( self, addr ):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource( addr )
        if not self.dev_check():
            print( 'Invalid Heater Device, closing')
            self.device.close()
        else:
            self.addr = addr
            self.set_connected( True )
            self.set_status( 'LISTENING' )

            if self.ID == 'XPD_1830':
                self.MAX_CURRENT = 6
                self.MAX_VOLTAGE = 1.9
                self.get_msg_voltage = XDP_1830.get_msg_voltage
                self.get_msg_current = XDP_1830.get_msg_current
                self.get_msg_enabled = XDP_1830.get_msg_enabled
                self.get_msg_reset   = XDP_1830.get_msg_reset
            elif self.ID == 'HP66312A':
                self.MAX_CURRENT = 2
                self.MAX_VOLTAGE = 1.9
                self.get_msg_voltage = HP_66312A.get_msg_voltage
                self.get_msg_current = HP_66312A.get_msg_current
                self.get_msg_enabled = HP_66312A.get_msg_enabled
                self.get_msg_reset   = HP_66312A.get_msg_reset

                
            self.reset()


    def set_connected( self, val ):
        self.connected = val
        self.signal_connected.emit( val )

    def set_heater_type(self):
        if self.ID == "XPD_1830":
            self.MAX_CURRENT = 6
            self.MAX_VOLTAGE = 1.9
        elif self.ID == "HP_66312A":
            self.MAX_CURRENT = 2
            self.MAX_VOLTAGE = 1.9

    def dev_check(self):
        # Check if XPD_1830
        id = self.device.query( 'ID?').split(' ')
        if id[1].startswith( 'XPD18-30' ):
            self.ID = "XPD_1830"
            return True
        
        # Check if HP66312_A
        id = self.device.query( '*IDN?').split(',')
        if  id[0].startswith( 'HEWLETT-PACKARD' ) and id[1] == '66312A':
            self.ID = "HP66312A"
            return True
        
        # Otherwise return False
        return False
    
    def returnThreadToMain( self, main_thread ):
        self.moveToThread( main_thread )

    def run_emergency( self ):
        self.reset()
        self.device.close()
        self.set_status( "NOT-READY" )
        
    def set_status( self, value ):
        self.status = value
        self.signal_status.emit( value )

    def start_comm( self ):
        counter = 0
        while True:
            counter += 1
            cur_status = self.status
            try:
                if cur_status == "LISTENING":
                    if self.changed_voltage:
                        self.apply_voltage(self.voltage)
                    
                    if self.changed_current:
                        self.apply_current(self.current)
                        
                    if self.changed_enabled:
                        self.apply_enabled(self.enabled)

            except Exception as e:
                print(e)
                self.run_emergency()
                return
                        
            if cur_status == "DISCONNECT":
                print( "Disconnecting Heater")
                break
        
        self.set_status( "NOT-READY" )
        # Return Board to main thread before finishing
        self.moveToThread( self.thread_main )

    def apply_voltage( self,val ):
        self.write( self.get_msg_voltage(val) )
        self.changed_voltage = False
    def apply_current( self,val ):
        self.write( self.get_msg_current(val) )
        self.changed_current = False
    def apply_enabled( self,val ):
        self.write( 'FOLD 1')
        self.write( self.get_msg_enabled(val) )
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


    def write( self, val ):
        print(val)
        self.device.write( val )

    def set_msg( self, msg ):
        print(msg)
        self.msg = msg

    def reset(self):
        self.write( self.get_msg_reset() )
        # self.apply_enabled( 0 )
        # self.apply_current( 0 )
        # self.set_voltage( 0 )
        print( "Resetting Heater")

    def close( self ):
        self.set_status( "DISCONNECT")
        while self.status == "DISCONNECT":
            time.sleep(0.01)
        self.device.close()

class XDP_1830():
    def get_msg_voltage( val ):
        return f'VSET %f' % val
    def get_msg_current( val ):
        return f'ISET %f' % val
    def get_msg_enabled( val ):
        return f'OUT %d' % int(val)
    def get_msg_reset( ):
        return 'FOLD 1; OUT 0'


class HP_66312A() :
    def get_msg_voltage( val ):
        return f'VOLT %f' % val
    def get_msg_current( val ):
        return f'CURR %f' % val
    def get_msg_enabled( val ):
        return f'OUTP %d' % int(val)
    def get_msg_reset( ):
        return 'OUTP 0'


class Sensor(QObject):
    addr = None
    connected = False
    ID = None
    status = 'NOT-READY'
    msg = ""
    time_interval = 0.05

    signal_connected = pyqtSignal( bool )
    signal_status = pyqtSignal( str)
    signal_temp = pyqtSignal( float )


    def __init__(self):
        super().__init__() #Inherit QObject


    def connect( self, addr ):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource( addr )
        if not self.dev_check():
            print( 'Invalid Sensor Device, closing')
            self.device.close()
        else:
            self.addr = addr
            self.set_connected( True )
            self.set_status( 'LISTENING' )
            self.reset()

    def set_connected( self, val ):
        self.connected = val
        self.signal_connected.emit( val )

    def dev_check(self):
        # Check if Correct Device
        id = self.device.query( '*' )
        return  id.startswith( '20K Ohm Thermistor' )
    
    def returnThreadToMain( self, main_thread ):
        self.moveToThread( main_thread )

    def run_emergency( self ):
        self.reset()
        self.device.close()
        self.set_status( "NOT-READY" )
        
    def set_status( self, value ):
        self.status = value
        self.signal_status.emit( value )

    def start_comm( self ):
        counter = 0
        while True:
            counter += 1
            cur_status = self.status
            try:
                if cur_status == "LISTENING":
                    self.signal_temp.emit( self.get_temp() )
            except Exception as e:
                print(e)
                self.run_emergency()
                return
                        
            if cur_status == "DISCONNECT":
                print( "Disconnecting Sensor")
                break
            time.sleep(self.time_interval)
        
        self.set_status( "NOT-READY" )
        # Return Board to main thread before finishing
        self.moveToThread( self.thread_main )


    def get_temp( self ):
        self.temp =  float(self.device.query('t'))
        return self.temp    

    def write( self, val ):
        print(val)
        self.device.write( val )

    def set_msg( self, msg ):
        print(msg)
        self.msg = msg

    def reset(self):
        print( "Resetting Sensor: Nothing to do")

    def close( self ):
        self.set_status( "DISCONNECT")
        while self.status == "DISCONNECT":
            time.sleep(0.01)
        self.device.close()
