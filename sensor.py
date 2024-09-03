import pyvisa
import time
from PyQt5.QtCore import (pyqtSignal, QObject)


def get_port_list():    
    rm = pyvisa.ResourceManager()
    port_list = [ p for p in rm.list_resources()]
    return port_list


class Sensor(QObject):
    addr = None
    connected = False
    ID = None
    status = 'NOT-READY'
    msg = ""

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
