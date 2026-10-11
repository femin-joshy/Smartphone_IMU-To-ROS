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
x_data = []
y_data = []
z_data = []
time_data = []

x_data_color = "#d32f2f"  # Red
y_data_color = "#7cb342"  # Green
z_data_color = "#0288d1"  # Blue

background_color = "#fafafa"  # White (material)

class SensorControl:
    def __init__(self, address):
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.last_time = time.time()
        self.linear_velocity_x = 0.0
        self.linear_velocity_y = 0.0
        self.linear_velocity_z = 0.0
        self.angular_velocity = 0.0
        self.address = address

    def on_message(self, ws, message):
        data = json.loads(message)
        rospy.loginfo(f"Received data: {data}")  # Log the received data to inspect its structure
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Check if the necessary keys are in the data
        if 'values' in data and len(data['values']) == 3:
            accel_x = data['values'][0]
            accel_y = data['values'][1]
            accel_z = data['values'][2]
        else:
            rospy.logerr("Acceleration data missing")
            return

        # Append data for plotting
        x_data.append(accel_x)
        y_data.append(accel_y)
        z_data.append(accel_z)
        time_data.append(float(current_time))

        accel_threshold = 2.5  # Threshold for acceleration sensitivity

        # Integrate acceleration to get linear velocity
        self.linear_velocity_x += accel_x * dt
        self.linear_velocity_y += accel_y * dt
        self.linear_velocity_z += accel_z * dt

        twist = Twist()

        # Apply the threshold condition for linear velocity
        if abs(accel_x) > 5:
            twist.linear.x = abs(self.linear_velocity_x)
        else:
            twist.linear.x = 0.0

        if abs(accel_y) > 16.5:
            twist.angular.z =  (self.linear_velocity_y - 14.5) # Directly using angular velocity from y acceleration
        else:
            twist.linear.y = 0.0

        if abs(accel_z) > 10:
            twist.linear.z =  self.linear_velocity_z # Directly using angular velocity from y acceleration
        else:
            twist.linear.z = 0.0

        print(twist)
        self.pub.publish(twist)

    def on_error(self, ws, error):
        rospy.logerr(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        rospy.loginfo(f"WebSocket closed with status: {close_status_code}, message: {close_msg}")

    def on_open(self, ws):
        rospy.loginfo("WebSocket connection opened")

    def run(self):
        ws = websocket.WebSocketApp(f"ws://{self.address}/sensor/connect?type=android.sensor.linear_acceleration",
                                     on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever()

# Integrate the plotting functionality
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.graphWidget.setBackground(background_color)

        self.graphWidget.setTitle("Accelerometer Plot", color="#8d6e63", size="20pt")
        
        # Add Axis Labels
        styles = {"color": "#f00", "font-size": "15px"}
        self.graphWidget.setLabel("left", "m/s^2", **styles)
        self.graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)
        self.graphWidget.addLegend()

        self.x_data_line = self.graphWidget.plot([], [], name="x", pen=pg.mkPen(color=x_data_color))
        self.y_data_line = self.graphWidget.plot([], [], name="y", pen=pg.mkPen(color=y_data_color))
        self.z_data_line = self.graphWidget.plot([], [], name="z", pen=pg.mkPen(color=z_data_color))
      
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)  # call update_plot_data function every 50 milliseconds
        self.timer.start()

    def update_plot_data(self):
        
        # limit lists data to 1000 items 
        limit = -1000 

        # Update the data.
        self.x_data_line.setData(time_data[limit:], x_data[limit:])  
        self.y_data_line.setData(time_data[limit:], y_data[limit:])
        self.z_data_line.setData(time_data[limit:], z_data[limit:])

if __name__ == "__main__":
    rospy.init_node('sensor_control_node')  # Initialize ROS in the main thread

    sensor_control = SensorControl(address="192.168.0.193:8080")  # Replace with your actual address
    sensor_control_thread = threading.Thread(target=sensor_control.run)
    sensor_control_thread.start()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
