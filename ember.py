from PyQt5.QtCore import QSize, QThread, Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QLineEdit,
    QWidget,
    QGroupBox,
    QComboBox,
    QTextEdit,
    QFileDialog,
    QCheckBox,
    QProgressBar
)
from PyQt5.QtGui import QFont, QFontDatabase,QIcon
from PyQt5.QtSvg import QSvgWidget

import sys, os, time, json, glob
import numpy as np
from functools import partial
from datetime import datetime
import serial.tools.list_ports

from simple_pid import PID as PID_control


import devices_dummy as devices

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ember")
        self.resize( 500,500 )
        self.setMinimumSize( 500, 500)
        # self.minheight = self.minimumHeight()
        # self.minwidth = self.minimumWidth()

        self.main_widget = QWidget()
        self.main_widget.setObjectName( "main_widget")
        layout_main = QVBoxLayout()
        self.main_widget.setLayout(layout_main)
        self.heater = None
        self.sensor = None

        self.make_panel_heater()
        self.make_panel_sensor()
        self.make_panel_pid()

        self.update_port_list()
        # self.make_panel_viewer()
        # self.make_panel_banner()

        layout_UI = QHBoxLayout()
        layout_UI.addWidget( self.group_sensor )
        layout_UI.addWidget( self.group_heater )
        # layout_UI.addWidget( self.group_viviewer )

        # layout_graph = QHBoxLayout()
        group_graph = QGroupBox("Graph")
        layout_main.addLayout( layout_UI )
        layout_main.addWidget( self.group_pid )
        layout_main.addWidget( group_graph )
        # layout_main.addWidget( self.group_logo )

        self.setCentralWidget( self.main_widget )

    def make_panel_pid(self):
        self.pid_setpoint = 25
        self.pid_P = 0.5
        self.pid_I = 0.05
        self.pid_D = 0

        self.group_pid = QGroupBox("PID")
        layout_PID = QHBoxLayout()
        self.group_pid.setLayout( layout_PID )

        self.pid_worker = pid_worker()
        label_SetPoint = QLabel("Set Point: ")
        self.LE_PID_setpoint = QLineEdit( str(self.pid_setpoint))
        self.LE_PID_setpoint.returnPressed.connect( self.update_pid_setting )
        label_celsius = QLabel(" C")

        label_P = QLabel("P: ")
        self.LE_PID_P = QLineEdit( str(self.pid_P))
        self.LE_PID_P.returnPressed.connect( self.update_pid_setting )
        label_I = QLabel("I: ")
        self.LE_PID_I = QLineEdit( str(self.pid_I))
        self.LE_PID_I.returnPressed.connect( self.update_pid_setting )
        label_D = QLabel("D: ")
        self.LE_PID_D = QLineEdit( str(self.pid_D))
        self.LE_PID_D.returnPressed.connect( self.update_pid_setting )

        self.PB_PID_run = QPushButton( "Run PID")
        self.PB_PID_run.clicked.connect( self.on_click_PID_run )

        layout_PID.addWidget( label_SetPoint )
        layout_PID.addWidget( self.LE_PID_setpoint )
        layout_PID.addWidget( label_celsius )
        layout_PID.addWidget( label_P )
        layout_PID.addWidget( self.LE_PID_P )
        layout_PID.addWidget( label_I)
        layout_PID.addWidget( self.LE_PID_I )
        layout_PID.addWidget( label_D )
        layout_PID.addWidget( self.LE_PID_D )
        layout_PID.addWidget( self.PB_PID_run )
        


    def make_panel_heater(self):
        # Device Manager Panel
        self.group_heater = QGroupBox("Heater")
        # self.group_heater.setFixedSize(QSize(450, 680))
        layout_heater = QVBoxLayout()
        self.group_heater.setLayout( layout_heater )

        # Serial Port Manager
        layout_device = QHBoxLayout()
        layout_device.setContentsMargins( 0,0,0,0 )
        self.heater_list = QComboBox(  )
        # self.dev_list.activated.connect( self.on_dev_selected )
        # self.dev_list.setFixedWidth( 100)
        self.PB_heater_connect = QPushButton( "Connect" )
        self.PB_heater_connect.clicked.connect( self.on_click_connect_heater )
        self.PB_heater_refresh = QPushButton( "Refresh" )
        self.PB_heater_refresh.clicked.connect( self.update_port_list )
        layout_device.addWidget( self.heater_list )
        layout_device.addWidget( self.PB_heater_connect )
        layout_device.addWidget( self.PB_heater_refresh )

        # Control
        layout_control = QVBoxLayout()
        layout_control.setContentsMargins( 0,0,0,0 )
        
        layout_heater_current = QHBoxLayout()
        layout_heater_current.setContentsMargins( 0,0,0,0 )
        layout_heater_voltage = QHBoxLayout()
        layout_heater_voltage.setContentsMargins( 0,0,0,0 )

        self.PB_heater_enable = QPushButton( "ENABLE" )
        self.PB_heater_enable.clicked.connect( self.on_click_enable_heater )

        label_MaxCurrent = QLabel("Current: ")
        self.LE_Heater_MaxCurrent = QLineEdit("2")
        label_amp = QLabel("A")
        label_MaxVoltage = QLabel("Voltage: ")
        self.LE_Heater_MaxVoltage = QLineEdit("1.1")
        label_volt = QLabel("V")
        layout_heater_current.addWidget( label_MaxCurrent )
        layout_heater_current.addWidget( self.LE_Heater_MaxCurrent )
        layout_heater_current.addWidget( label_amp )
        layout_heater_voltage.addWidget( label_MaxVoltage )
        layout_heater_voltage.addWidget( self.LE_Heater_MaxVoltage )
        layout_heater_voltage.addWidget( label_volt )
        layout_control.addLayout( layout_heater_current)
        layout_control.addLayout( layout_heater_voltage)
        layout_control.addWidget( self.PB_heater_enable )
        
        self.group_heater_control = QGroupBox("")
        self.group_heater_control.setLayout( layout_control )

        layout_heater.addLayout( layout_device )
        layout_heater.addWidget( self.group_heater_control )
        # layout_heater.addWidget( self.group_device_setting)
        layout_heater.setSpacing( 0 )

        self.group_heater_control.setEnabled(False)
    
    def make_panel_sensor(self):
        # Device Manager Panel
        self.group_sensor = QGroupBox("Sensor")
        # self.group_sensor.setFixedSize(QSize(450, 680))
        layout_sensor = QVBoxLayout()
        self.group_sensor.setLayout( layout_sensor )

        # Serial Port Manager
        layout_device = QHBoxLayout()
        layout_device.setContentsMargins( 0,0,0,0 )
        self.sensor_list = QComboBox(  )
        # self.dev_list.activated.connect( self.on_dev_selected )
        # self.dev_list.setFixedWidth( 100)
        self.PB_sensor_connect = QPushButton( "Connect" )
        self.PB_sensor_connect.clicked.connect( self.on_click_connect_sensor )
        self.PB_sensor_refresh = QPushButton( "Refresh" )
        self.PB_sensor_refresh.clicked.connect( self.update_port_list )
        layout_device.addWidget( self.sensor_list )
        layout_device.addWidget( self.PB_sensor_connect )
        layout_device.addWidget( self.PB_sensor_refresh )

        ## Display
        self.group_temp = QGroupBox("")
        layout_temp = QHBoxLayout()
        label_temp = QLabel("Temperature: ")
        self.LE_temperature = QLineEdit("")
        label_celsius = QLabel(" C")

        self.LE_temperature.setReadOnly( True )
        self.LE_temperature.setFixedWidth(40)
        layout_temp.addWidget(label_temp)
        layout_temp.addWidget(self.LE_temperature)
        layout_temp.addWidget(label_celsius)
        self.group_temp.setLayout( layout_temp )

        layout_sensor.addLayout( layout_device )
        layout_sensor.addWidget( self.group_temp)
        layout_sensor.setSpacing( 0 )

        self.group_temp.setEnabled(False)

    def on_click_enable_heater(self):
        # Connect Push Button
        if self.PB_heater_enable.text() == "ENABLE":
            # Check if port list needs update:
            cur_port_list = self.port_list
            new_port_list = self.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_port_list()
            else:
                self.heater.set_enabled(True)
                self.PB_heater_enable.setText( "DISABLE" )
        elif self.PB_heater_enable.text() == "DISABLE":
            self.heater.set_enabled(False)
            self.PB_heater_enable.setText( "ENABLE" )

            

    def update_port_list(self):
        # Remove Current List
        for i in range(self.heater_list.count()):
            self.heater_list.removeItem(0)
            self.sensor_list.removeItem(0)

        # Update Port List
        self.port_list = self.get_port_list()
        self.heater_list.addItems( self.port_list )
        self.sensor_list.addItems( self.port_list )
        if len(self.port_list) > 0:
            self.PB_heater_connect.setEnabled( True )
            self.PB_sensor_connect.setEnabled( True )
        elif len(self.port_list) == 0:
            self.PB_heater_connect.setEnabled( False )
            self.PB_sensor_connect.setEnabled( True )


    def get_port_list(self):
        """\
        Return a list of USB serial port devices.

        Entries in the list are ListPortInfo objects from the
        serial.tools.list_ports module.  Fields of interest include:

            device:  The device's full path name.
            vid:     The device's USB vendor ID value.
            pid:     The device's USB product ID value.
        """
        #port_list = [p.device for p in serial.tools.list_ports.comports() if p.vid]
        port_list = ["HEATER", "SENSOR"]
        return port_list

    def on_click_connect_heater(self):
        # Connect Push Button
        if self.PB_heater_connect.text() == "Connect":
            # Check if port list needs update:
            cur_port_list = self.port_list
            new_port_list = self.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_port_list()
            else:
                self.connect_heater()
        elif self.PB_heater_connect.text() == "Disconnect":
            self.disconnect_heater()

    def on_click_connect_sensor(self):
        # Connect Push Button
        if self.PB_sensor_connect.text() == "Connect":
            # Check if port list needs update:
            cur_port_list = self.port_list
            new_port_list = self.get_port_list()
            if not cur_port_list == new_port_list:
                self.update_port_list()
            else:
                self.connect_sensor()
        elif self.PB_sensor_connect.text() == "Disconnect":
            self.disconnect_sensor()

    def connect_heater( self ):
        portname = self.heater_list.currentText()
        self.heater = devices.HP_66312A(portname)
        self.heater.say_hi()

        self.group_heater_control.setEnabled(True)
        self.PB_heater_connect.setText("Disconnect")

    def disconnect_heater( self ):
        self.heater.close()
        self.group_heater_control.setEnabled(False)
        self.PB_heater_connect.setText("Connect")

    def connect_sensor( self ):
        portname = self.sensor_list.currentText()
        self.sensor = devices.thermistor_20K(portname)
        self.sensor.say_hi()
        self.PB_sensor_connect.setText("Disconnect")

        self.group_temp.setEnabled(True)
        self.update_temperature()

    def disconnect_sensor( self ):
        self.sensor.close()
        self.LE_temperature.setText("")
        self.group_temp.setEnabled(False)
        self.PB_sensor_connect.setText("Connect")

    def update_temperature( self ):
        self.cur_temp = self.sensor.get_temp()
        self.LE_temperature.setText( "%.1f" % self.cur_temp )

    def pid_get_temp( self ):
        self.update_temperature()
        self.pid_worker.cur_temp = self.cur_temp

    def pid_set_volt( self, value ):
        print( value )

    def update_pid_setting( self ):
        P = float(self.LE_PID_P.text())
        I = float(self.LE_PID_I.text())
        D = float(self.LE_PID_D.text())
        setpoint = float(self.LE_PID_setpoint.text())
        self.pid_worker.PID_value = (P,I,D)
        self.pid_worker.setpoint = setpoint

    def on_click_PID_run( self ):
        if self.PB_PID_run.text() == "Run PID":

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
        else :
            self.pid_continue = False
            self.PB_PID_run.setText( "Run PID") 
            self.pid_worker.stop = True

class pid_worker( QObject ):
    finished = pyqtSignal()
    PID_value = (1,0,0)
    setpoint = 25
    pid_sample_time = 0.1
    
    stop = False
    cur_temp = 0
    signal_get_temp = pyqtSignal()

    signal_set_volt = pyqtSignal(float)

    # def __init__( self ):
    #     super(pid_worker, self).__init__()
    #     self.setpoint = 25

    def start_pid( self ):
        self.pid = PID_control( *self.PID_value, setpoint=self.setpoint)
        # self.pid.sample_time = 11
        # print(self.pid)
        while True:
            self.pid.tunings = self.PID_value
            self.pid.setpoint = self.setpoint
            # self.update_temperature()
            self.signal_get_temp.emit()

            # # Calculate new heater output
            new_volt = self.pid( self.cur_temp )
            # # Feed the PID output to the system and get its current value
            self.signal_set_volt.emit( new_volt )

            if self.stop:
                self.finished.emit()
                break

            time.sleep( self.pid_sample_time )




if __name__ == "__main__":
    app = QApplication(sys.argv)

    vivi_path = os.path.dirname(os.path.abspath(__file__))
    asset_path = os.path.join( vivi_path, 'assets')

    # with open( os.path.join( asset_path,"style.css"),"r") as fh:
    #     app.setStyleSheet(fh.read())


    # app.setWindowIcon(QIcon(os.path.join(asset_path,"vivi-icon.png")))
    app.setApplicationName("Ember")
    
    window = MainWindow()
    # window.setWindowIcon(QIcon(os.path.join(asset_path,"vivi-icon.png")))
    window.show()

    # app.aboutToQuit.connect( window.on_quit )


    app.exec()