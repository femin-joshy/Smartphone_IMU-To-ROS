import rospy
from geometry_msgs.msg import Twist
import websocket
import json
import threading
import time
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys

# Shared data
accel_x_data = []
accel_y_data = []
accel_z_data = []
gyro_x_data = []
gyro_y_data = []
gyro_z_data = []
time_data = []

accel_x_data_color = "#d32f2f"  # Red
accel_y_data_color = "#7cb342"  # Green
accel_z_data_color = "#0288d1"  # Blue
gyro_x_data_color = "#ffeb3b"  # Yellow
gyro_y_data_color = "#ff9800"  # Orange
gyro_z_data_color = "#9c27b0"  # Purple

background_color = "#fafafa"  # White (material)

class SensorControl:
    def __init__(self, address):
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.last_time = time.time()
        self.linear_velocity_x = 0.0
        self.linear_velocity_y = 0.0
        self.linear_velocity_z = 0.0
        self.angular_velocity_x = 0.0
        self.angular_velocity_y = 0.0
        self.angular_velocity_z = 0.0
        self.address = address

    def on_accel_message(self, ws, message):
        data = json.loads(message)
        rospy.loginfo(f"Received accelerometer data: {data}")  # Log the received data to inspect its structure
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        if 'values' in data and len(data['values']) == 3:
            accel_x = data['values'][0]
            accel_y = data['values'][1]
            accel_z = data['values'][2]

            accel_x_data.append(accel_x)
            accel_y_data.append(accel_y)
            accel_z_data.append(accel_z)
            time_data.append(float(current_time))

            #accel_threshold = 2.5  # Threshold for acceleration sensitivity

            self.linear_velocity_x += accel_x * dt
            self.linear_velocity_y += accel_y * dt
            self.linear_velocity_z += accel_z * dt

            twist = Twist()
            twist.linear.x = self.linear_velocity_x
            twist.linear.y = self.linear_velocity_y
            twist.linear.z = self.linear_velocity_z

            self.pub.publish(twist)
        else:
            rospy.logerr("Acceleration data missing")

    def on_gyro_message(self, ws, message):
        data = json.loads(message)
        rospy.loginfo(f"Received gyroscope data: {data}")  # Log the received data to inspect its structure
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        if 'values' in data and len(data['values']) == 3:
            gyro_x = data['values'][0]
            gyro_y = data['values'][1]
            gyro_z = data['values'][2]

            gyro_x_data.append(gyro_x)
            gyro_y_data.append(gyro_y)
            gyro_z_data.append(gyro_z)
            time_data.append(float(current_time))

            self.angular_velocity_x += gyro_x * dt
            self.angular_velocity_y += gyro_y * dt
            self.angular_velocity_z += gyro_z * dt

            twist = Twist()
            twist.angular.x = self.angular_velocity_x
            twist.angular.y = self.angular_velocity_y
            twist.angular.z = self.angular_velocity_z

            self.pub.publish(twist)
        else:
            rospy.logerr("Gyroscope data missing")

    def on_error(self, ws, error):
        rospy.logerr(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        rospy.loginfo(f"WebSocket closed with status: {close_status_code}, message: {close_msg}")

    def on_open(self, ws):
        rospy.loginfo("WebSocket connection opened")

    def run_accel(self):
        ws = websocket.WebSocketApp(f"ws://{self.address}/sensor/connect?type=android.sensor.linear_acceleration",
                                    on_message=self.on_accel_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever()

    def run_gyro(self):
        ws = websocket.WebSocketApp(f"ws://{self.address}/sensor/connect?type=android.sensor.gyroscope",
                                    on_message=self.on_gyro_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever()

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.accel_graphWidget = pg.PlotWidget()
        self.gyro_graphWidget = pg.PlotWidget()

        self.layout.addWidget(self.accel_graphWidget)
        self.layout.addWidget(self.gyro_graphWidget)

        self.accel_graphWidget.setBackground(background_color)
        self.gyro_graphWidget.setBackground(background_color)

        self.accel_graphWidget.setTitle("Accelerometer Data Plot", color="#8d6e63", size="20pt")
        self.gyro_graphWidget.setTitle("Gyroscope Data Plot", color="#8d6e63", size="20pt")

        styles = {"color": "#f00", "font-size": "15px"}
        self.accel_graphWidget.setLabel("left", "Values", **styles)
        self.accel_graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)
        self.gyro_graphWidget.setLabel("left", "Values", **styles)
        self.gyro_graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)
        self.accel_graphWidget.addLegend()
        self.gyro_graphWidget.addLegend()

        self.accel_x_data_line = self.accel_graphWidget.plot([], [], name="accel_x", pen=pg.mkPen(color=accel_x_data_color))
        self.accel_y_data_line = self.accel_graphWidget.plot([], [], name="accel_y", pen=pg.mkPen(color=accel_y_data_color))
        self.accel_z_data_line = self.accel_graphWidget.plot([], [], name="accel_z", pen=pg.mkPen(color=accel_z_data_color))
        self.gyro_x_data_line = self.gyro_graphWidget.plot([], [], name="gyro_x", pen=pg.mkPen(color=gyro_x_data_color))
        self.gyro_y_data_line = self.gyro_graphWidget.plot([], [], name="gyro_y", pen=pg.mkPen(color=gyro_y_data_color))
        self.gyro_z_data_line = self.gyro_graphWidget.plot([], [], name="gyro_z", pen=pg.mkPen(color=gyro_z_data_color))

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):

        limit = -1000

        self.accel_x_data_line.setData(time_data[limit:], accel_x_data[limit:])
        self.accel_y_data_line.setData(time_data[limit:], accel_y_data[limit:])
        self.accel_z_data_line.setData(time_data[limit:], accel_z_data[limit:])
        self.gyro_x_data_line.setData(time_data[limit:], gyro_x_data[limit:])
        self.gyro_y_data_line.setData(time_data[limit:], gyro_y_data[limit:])
        self.gyro_z_data_line.setData(time_data[limit:], gyro_z_data[limit:])

if __name__ == "__main__":
    rospy.init_node('sensor_control_node')  # Initialize ROS in the main thread

    accel_control = SensorControl(address="192.168.0.193:8080")
    gyro_control = SensorControl(address="192.168.0.193:8080")

    accel_thread = threading.Thread(target=accel_control.run_accel)
    gyro_thread = threading.Thread(target=gyro_control.run_gyro)

    accel_thread.start()
    gyro_thread.start()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
