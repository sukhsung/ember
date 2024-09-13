from PyQt5.QtCore import QThread, Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QWidget,
    QGroupBox,
    QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtSvg import QSvgWidget

import pyqtgraph as pg

import sys, os, time
import numpy as np

from simple_pid import PID as PID_control
import devices as devices

from ember_ui import Ui_MainWindow
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ember_path = os.path.dirname(os.path.abspath(__file__))
        self.asset_path = os.path.join( ember_path, 'UI')

        self.setupUi(self)
        self.setWindowTitle("Ember")

        self.thread_main = QThread.currentThread() 
        self.sensor = devices.Sensor()
        self.sensor.signal_connected.connect( self.received_sensor_connected )
        self.heater = devices.Heater()
        self.heater.signal_connected.connect( self.received_heater_connected )

        self.pid_running = False
        self.pid_worker = pid_worker()
        
        self.make_panel_heater()
        self.make_panel_sensor()
        self.make_panel_pid()
        self.make_panel_graph()
        self.make_banner()

        self.update_sensor_list()
        self.update_heater_list()


    def make_panel_graph( self ):
        layout_graph = QHBoxLayout()
        self.group_graph.setLayout( layout_graph )

        self.PW_temp = pg.plot()
        
        layout_graph.addWidget( self.PW_temp )

        self.num_pt = 256
        self.Temps = np.zeros( self.num_pt )
        self.Times = np.arange( self.num_pt )*self.sensor.time_interval
        self.plot_temps = self.PW_temp.plot( self.Times, self.Temps )
        

    def make_panel_pid(self):
        self.pid_setpoint = 25
        self.pid_P = 0.1
        self.pid_I = 0.01
        self.pid_D = 0
        self.pid_MaxCurrent = 0

        self.LE_PID_setpoint.setText( str(self.pid_setpoint))
        self.LE_PID_P.setText( str(self.pid_P))
        self.LE_PID_I.setText( str(self.pid_I))
        self.LE_PID_D.setText( str(self.pid_D))
        self.LE_PID_MaxCurrent.setText( str(self.pid_MaxCurrent) )

        self.LE_PID_setpoint.returnPressed.connect( self.update_pid_setting )
        self.LE_PID_P.returnPressed.connect( self.update_pid_setting )
        self.LE_PID_I.returnPressed.connect( self.update_pid_setting )
        self.LE_PID_D.returnPressed.connect( self.update_pid_setting )
        self.LE_PID_MaxCurrent.returnPressed.connect( self.update_pid_setting )

        self.PB_PID_run.clicked.connect( self.on_click_PID_run )
        self.group_pid.setEnabled(False)


    def make_panel_heater(self):
        self.PB_heater_connect.clicked.connect( self.on_click_connect_heater )
        self.PB_heater_refresh.clicked.connect( self.update_heater_list )
        self.PB_heater_enable.clicked.connect( self.on_click_enable_heater )
        self.LE_Heater_MaxCurrent.returnPressed.connect( self.update_heater_setting )
        self.LE_Heater_MaxVoltage.returnPressed.connect( self.update_heater_setting )

        self.group_heater_control.setEnabled(False)
    
    def make_panel_sensor(self):
        self.PB_sensor_connect.clicked.connect( self.on_click_connect_sensor )
        self.PB_sensor_refresh.clicked.connect( self.update_sensor_list )
        self.group_temp.setEnabled(False)
        self.group_graph.setEnabled(False)

    def make_banner(self):
        self.svg_logo_right = QSvgWidget( os.path.join( self.asset_path,'ember-icon.svg'), parent=self.group_logo)
        self.svg_logo_right.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        # self.svg_logo_right.renderer().viewBox().setWidth( 50)
        self.svg_logo_right.setContentsMargins( 0,0,0,0 )
        # self.svg_logo_right.move(825, -175)
        self.svg_logo_right.resize(100,100)

    #### HEATER RELATED
    def update_heater_list(self):
        # Remove Current List
        for i in range(self.heater_list.count()):
            self.heater_list.removeItem(0)

        # Update Port List
        self.heater_port_list = devices.get_port_list()
        self.heater_list.addItems( self.heater_port_list )
        if len(self.heater_port_list) > 0:
            self.PB_heater_connect.setEnabled( True )
        elif len(self.heater_port_list) == 0:
            self.PB_heater_connect.setEnabled( False )

    def on_click_connect_heater(self):
        # Connect Push Button
        if self.PB_heater_connect.text() == "Connect":
            # Check if port list needs update:
            cur_port_list = self.heater_port_list
            new_port_list = devices.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_heater_list()
            else:
                self.connect_heater()
        elif self.PB_heater_connect.text() == "Disconnect":
            self.disconnect_heater()

        self.enable_pid()

    def connect_heater( self ):
        portname = self.heater_list.currentText()
        self.heater.connect(portname)

    def disconnect_heater( self ):
        if self.pid_running:
            self.stop_pid()
        self.heater.set_status( "DISCONNECT")
        t0 = time.time()
        while (time.time()-t0 < 1 and self.heater.connected):
            pass
        
    def received_heater_connected( self, val ):
        if val :
            self.group_heater_control.setEnabled(True)
            self.PB_heater_connect.setText("Disconnect")
            self.start_heater()
            self.LE_Heater_MaxCurrent.setText( str(self.heater.MAX_CURRENT) )
            self.LE_Heater_MaxVoltage.setText( str(0))
            self.update_heater_setting()
        else:
            self.group_heater_control.setEnabled(False)
            self.PB_heater_connect.setText("Connect")

    def start_heater( self ):
        self.heater.thread_main = self.thread_main
        self.heater.m_thread = QThread()
        self.heater.moveToThread(self.heater.m_thread)
        self.heater.m_thread.started.connect( self.heater.start_comm )
        self.heater.m_thread.start()

    def on_click_enable_heater(self):
        # Connect Push Button
        if self.PB_heater_enable.text() == "ENABLE":
            # Check if port list needs update:
            cur_port_list = self.heater_port_list
            new_port_list = devices.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_heater_list()
            else:
                self.heater.set_enabled(True)
                self.PB_heater_enable.setText( "DISABLE" )
        elif self.PB_heater_enable.text() == "DISABLE":
            self.heater.set_enabled(False)
            self.PB_heater_enable.setText( "ENABLE" )

    def update_heater_setting(self):
        curr = float( self.LE_Heater_MaxCurrent.text() )
        volt = float( self.LE_Heater_MaxVoltage.text() )

        if volt > self.heater.MAX_VOLTAGE:
            volt = self.heater.MAX_VOLTAGE
        elif volt < 0:
            volt = 0
        self.LE_Heater_MaxVoltage.setText(str(volt))

        if curr > self.heater.MAX_CURRENT:
            curr = self.heater.MAX_CURRENT
        elif curr < 0:
            curr = 0
        self.LE_Heater_MaxCurrent.setText(str(curr))

        self.heater.set_current( curr )
        self.heater.set_voltage( volt )

    def enable_pid( self ):
        if self.heater.connected and self.sensor.connected :
            self.group_pid.setEnabled(True)
        else:
            self.group_pid.setEnabled(False)




    #### SENSOR RELATED
    def update_sensor_list(self):
        # Remove Current List
        for i in range(self.sensor_list.count()):
            self.sensor_list.removeItem(0)

        # Update Port List
        self.sensor_port_list = devices.get_port_list()
        self.sensor_list.addItems( self.sensor_port_list )
        if len(self.sensor_port_list) > 0:
            self.PB_sensor_connect.setEnabled( True )
        elif len(self.sensor_port_list) == 0:
            self.PB_sensor_connect.setEnabled( False )
    
    def on_click_connect_sensor(self):
        # Connect Push Button
        if self.PB_sensor_connect.text() == "Connect":
            # Check if port list needs update:
            cur_port_list = self.sensor_port_list
            new_port_list = devices.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_sensor_list()
            else:
                self.connect_sensor()
        elif self.PB_sensor_connect.text() == "Disconnect":
            self.disconnect_sensor()
        
        self.enable_pid()

    def connect_sensor( self ):
        portname = self.sensor_list.currentText()
        self.sensor.connect(portname)

    def disconnect_sensor( self ):
        if self.pid_running:
            self.stop_pid()            
        self.sensor.set_status( "DISCONNECT")
        t0 = time.time()
        while (time.time()-t0 < 1 and self.heater.connected):
            pass

    def received_sensor_connected( self, val ):
        if val :
            self.PB_sensor_connect.setText("Disconnect")
            self.group_temp.setEnabled(True)
            self.group_graph.setEnabled(True)
            self.start_sensor()
        else:
            self.LE_temperature.setText("NA")
            self.group_temp.setEnabled(False)
            self.group_graph.setEnabled(False)
            self.PB_sensor_connect.setText("Connect")

    def start_sensor( self ):
        self.sensor.thread_main = self.thread_main
        self.sensor.m_thread = QThread()
        self.sensor.moveToThread(self.sensor.m_thread)
        self.sensor.m_thread.started.connect( self.sensor.start_comm )
        self.sensor.signal_temp.connect( self.update_temperature )
        self.sensor.m_thread.start()

    def update_temperature( self,val ):
        # self.cur_temp = self.sensor.get_temp()
        self.cur_temp = val
        self.LE_temperature.setText( "%.2f °C" % self.cur_temp )

        self.Temps = np.roll( self.Temps, -1 )
        self.Temps[-1] = self.cur_temp
        
        self.plot_temps.setData( self.Times, self.Temps )


    ##### PID RELATED

    def pid_get_temp( self ):
        self.pid_worker.cur_temp = self.cur_temp

    def pid_set_volt( self, value ):
        self.LE_Heater_MaxVoltage.setText( str(value) )
        self.heater.set_voltage( value )

    def update_pid_setting( self ):
        P = float(self.LE_PID_P.text())
        I = float(self.LE_PID_I.text())
        D = float(self.LE_PID_D.text())
        setpoint = float(self.LE_PID_setpoint.text())

        self.pid_MaxCurrent = float(self.LE_PID_MaxCurrent.text())
        if self.pid_MaxCurrent > self.heater.MAX_CURRENT:
            self.pid_MaxCurrent = self.heater.MAX_CURRENT
        elif self.pid_MaxCurrent < 0:
            self.pid_MaxCurrent = 0
        self.LE_PID_MaxCurrent.setText(str(self.pid_MaxCurrent))


        self.pid_worker.PID_value = (P,I,D)
        self.pid_worker.setpoint = setpoint

    def on_click_PID_run( self ):
        if self.PB_PID_run.text() == "Run PID":
            self.start_pid()
        else :
            self.stop_pid()

    def start_pid( self ):
        self.update_pid_setting()
        
        self.LE_Heater_MaxCurrent.setText( str(self.pid_MaxCurrent) )
        self.pid_running = True
        self.heater.set_voltage( 0 )
        self.heater.set_current( self.pid_MaxCurrent )
        self.heater.set_enabled( True )
        # Step 2: Create a QThread object
        self.thread_pid = QThread()
        # Step 3: Create a worker object
        self.pid_worker = pid_worker()
        self.update_pid_setting()
        # Step 4: Move worker to the thread
        self.pid_worker.moveToThread(self.thread_pid)

        # Step 5: Connect signals and slots
        self.thread_pid.started.connect(self.pid_worker.start_pid)
        self.pid_worker.signal_get_temp.connect( self.pid_get_temp )
        self.pid_worker.finished.connect(self.thread_pid.quit)
        self.pid_worker.signal_set_volt.connect( self.pid_set_volt)

        # Step 6: Start the thread
        self.thread_pid.start()
        self.PB_PID_run.setText( "Stop PID") 
        self.group_heater_control.setEnabled(False)
        self.PB_heater_enable.setText( "PID\nRunning")        

    def stop_pid( self ):
        self.pid_running = False
        self.pid_worker.stop = True
        self.heater.set_enabled( False )
        self.PB_PID_run.setText( "Run PID") 
        self.group_heater_control.setEnabled(True)
        self.PB_heater_enable.setText( "ENABLE")

    def on_quit( self ):
        print("Exiting Ember")
        if self.heater.connected:
            self.disconnect_heater()

        if self.sensor.connected:
            self.disconnect_sensor()

class pid_worker( QObject ):
    finished = pyqtSignal()
    PID_value = (1,0,0)
    setpoint = 25
    pid_sample_time = 0.1
    stop = False
    cur_temp = 0
    signal_get_temp = pyqtSignal()
    signal_set_volt = pyqtSignal(float)

    def start_pid( self ):
        self.pid = PID_control( *self.PID_value, setpoint=self.setpoint)
        self.pid.output_limits = (0, 1.9)

        while True:
            self.pid.tunings = self.PID_value
            self.pid.setpoint = self.setpoint
            # self.update_temperature()
            self.signal_get_temp.emit()

            # # Calculate new heater output
            new_volt = self.pid( self.cur_temp )
            new_volt = round( new_volt,3 )
            # # Feed the PID output to the system and get its current value
            self.signal_set_volt.emit( new_volt )

            if self.stop:
                self.finished.emit()
                break

            time.sleep( self.pid_sample_time )




if __name__ == "__main__":

    ember_path = os.path.dirname(os.path.abspath(__file__))
    asset_path = os.path.join( ember_path, 'UI')

    app = QApplication(sys.argv)
    app.setApplicationName("Ember")
    app.setWindowIcon(QIcon(os.path.join(asset_path,"ember-icon.png")))

    window = MainWindow()
    window.show()
    app.aboutToQuit.connect( window.on_quit )
    app.exec()