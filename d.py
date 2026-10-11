#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import websocket
import json
import threading
import time
import numpy as np
from scipy.spatial.transform import Rotation as R
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys

# Shared data
accel_data = []
gyro_data = []
rotation_vector_data = []
synchronized_data = []
time_data = []
robot_orientation_matrix = np.eye(3)  # Initialize with identity matrix
robot_linear_velocity_x = []
robot_linear_velocity_y = []
robot_linear_velocity_z = []
robot_angular_velocity_x = []
robot_angular_velocity_y = []
robot_angular_velocity_z = []


# For graph
accel_x_data = []
accel_y_data = []
accel_z_data = []
gyro_x_data = []
gyro_y_data = []
gyro_z_data = []

accel_x_data_color = "#d32f2f"  # Red
accel_y_data_color = "#7cb342"  # Green
accel_z_data_color = "#0288d1"  # Blue
gyro_x_data_color = "#ffeb3b"  # Yellow
gyro_y_data_color = "#ff9800"  # Orange
gyro_z_data_color = "#9c27b0"  # Purple

background_color = "#fafafa"  # White (material)

# Velocity states
linear_velocity_x = 0.0
linear_velocity_y = 0.0
linear_velocity_z = 0.0

# WebSocket callbacks for accelerometer
def on_message_accel(ws, message):
    data = json.loads(message)
    current_time = time.time()
    if 'values' in data and len(data['values']) == 3:
        accel_x = data['values'][0]
        accel_y = data['values'][1]
        accel_z = data['values'][2]
        accel_data.append((current_time, accel_x, accel_y, accel_z))
        synchronize_data()

def on_error_accel(ws, error):
    print(f"Accelerometer WebSocket error: {error}")

def on_close_accel(ws, close_status_code, close_msg):
    print(f"Accelerometer WebSocket closed: {close_status_code}, {close_msg}")

def on_open_accel(ws):
    print("Accelerometer WebSocket connection opened")

# WebSocket callbacks for gyroscope
def on_message_gyro(ws, message):
    data = json.loads(message)
    current_time = time.time()
    if 'values' in data and len(data['values']) == 3:
        gyro_x = data['values'][0]
        gyro_y = data['values'][1]
        gyro_z = data['values'][2]
        gyro_data.append((current_time, gyro_x, gyro_y, gyro_z))
        synchronize_data()

def on_error_gyro(ws, error):
    print(f"Gyroscope WebSocket error: {error}")

def on_close_gyro(ws, close_status_code, close_msg):
    print(f"Gyroscope WebSocket closed: {close_status_code}, {close_msg}")

def on_open_gyro(ws):
    print("Gyroscope WebSocket connection opened")

# WebSocket callbacks for rotation vector
def on_message_rotation_vector(ws, message):
    data = json.loads(message)
    current_time = time.time()
    if 'values' in data and len(data['values']) >= 4:
        rotation_vector = data['values'][:4]  # Taking first 4 elements (quaternion)
        rotation_matrix = quaternion_to_rotation_matrix(rotation_vector)
        rotation_vector_data.append((current_time, rotation_matrix))
        synchronize_data()

def on_error_rotation_vector(ws, error):
    print(f"Rotation Vector WebSocket error: {error}")

def on_close_rotation_vector(ws, close_status_code, close_msg):
    print(f"Rotation Vector WebSocket closed: {close_status_code}, {close_msg}")

def on_open_rotation_vector(ws):
    print("Rotation Vector WebSocket connection opened")

def quaternion_to_rotation_matrix(quaternion):
    r = R.from_quat(quaternion)
    return r.as_matrix()

def synchronize_data():
    global synchronized_data
    while accel_data and gyro_data and rotation_vector_data:
        accel_time, accel_x, accel_y, accel_z = accel_data[0]
        gyro_time, gyro_x, gyro_y, gyro_z = gyro_data[0]
        rotation_vector_time, rotation_matrix = rotation_vector_data[0]

        if abs(accel_time - gyro_time) < 0.05 and abs(accel_time - rotation_vector_time) < 0.05:
            synchronized_data.append((accel_time, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, rotation_matrix))
            
            # For graph
            time_data.append(float(accel_time))
            accel_x_data.append(accel_x)
            accel_y_data.append(accel_y)
            accel_z_data.append(accel_z)
            gyro_x_data.append(gyro_x)
            gyro_y_data.append(gyro_y)
            gyro_z_data.append(gyro_z)
            
            accel_data.pop(0)
            gyro_data.pop(0)
            rotation_vector_data.pop(0)
        elif accel_time < gyro_time or accel_time < rotation_vector_time:
            accel_data.pop(0)
        elif gyro_time < rotation_vector_time:
            gyro_data.pop(0)
        else:
            rotation_vector_data.pop(0)

def run_websocket():
    #change the IP address according to the network that both the PC and Smartphone are connected to.
    #(This one is TP-Link_BFA4)
    #Connect your smartphone to the same network too before running the whole program.
    #Check the IP address of the phone using Wi-Fi settings and use that here.
    ws_accel = websocket.WebSocketApp("ws://192.168.0.193:8080/sensor/connect?type=android.sensor.linear_acceleration",
                                      on_message=on_message_accel,
                                      on_error=on_error_accel,
                                      on_close=on_close_accel)
    ws_accel.on_open = on_open_accel

    ws_gyro = websocket.WebSocketApp("ws://192.168.0.193:8080/sensor/connect?type=android.sensor.gyroscope",
                                     on_message=on_message_gyro,
                                     on_error=on_error_gyro,
                                     on_close=on_close_gyro)
    ws_gyro.on_open = on_open_gyro

    ws_rotation_vector = websocket.WebSocketApp("ws://192.168.0.193:8080/sensor/connect?type=android.sensor.rotation_vector",
                                                on_message=on_message_rotation_vector,
                                                on_error=on_error_rotation_vector,
                                                on_close=on_close_rotation_vector)
    ws_rotation_vector.on_open = on_open_rotation_vector

    threading.Thread(target=ws_accel.run_forever).start()
    threading.Thread(target=ws_gyro.run_forever).start()
    threading.Thread(target=ws_rotation_vector.run_forever).start()

def odom_callback(data):
    global robot_orientation_matrix
    quaternion = [data.pose.pose.orientation.x,
                  data.pose.pose.orientation.y,
                  data.pose.pose.orientation.z,
                  data.pose.pose.orientation.w]
    robot_orientation_matrix = quaternion_to_rotation_matrix(quaternion)

def publish_twist_commands():
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)  # Use /raspi_0/cmd_vel for using the code on a real raspi mouse. Changes with each case.
    rate = rospy.Rate(20)  # 20 Hz

    global linear_velocity_x, linear_velocity_y, linear_velocity_z
    last_time = time.time()

    while not rospy.is_shutdown():
        if synchronized_data:
            current_time, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, phone_rotation_matrix = synchronized_data.pop(0)
            dt = current_time - last_time
            last_time = current_time

            # Integrate acceleration to get velocity
            linear_velocity_x += accel_x * dt
            linear_velocity_y += accel_y * dt
            linear_velocity_z += accel_z * dt

            # Create velocity vectors
            linear_velocity_vector = np.array([linear_velocity_x, linear_velocity_y, linear_velocity_z])
            angular_velocity_vector = np.array([gyro_x, gyro_y, gyro_z])

            # Apply rotation matrices
            rotated_linear_velocity = np.dot(np.dot(robot_orientation_matrix.T, phone_rotation_matrix), linear_velocity_vector) / 5
            rotated_angular_velocity = np.dot(np.dot(robot_orientation_matrix.T, phone_rotation_matrix), angular_velocity_vector)

            # Store robot velocities for plotting
            robot_linear_velocity_x.append(rotated_linear_velocity[0])
            robot_linear_velocity_y.append(rotated_linear_velocity[1])
            robot_linear_velocity_z.append(rotated_linear_velocity[2])
            robot_angular_velocity_x.append(rotated_angular_velocity[0])
            robot_angular_velocity_y.append(rotated_angular_velocity[1])
            robot_angular_velocity_z.append(rotated_angular_velocity[2])

            # Create Twist message
            twist = Twist()
            twist.linear.x = rotated_linear_velocity[0]
            twist.linear.y = rotated_linear_velocity[1]
            twist.linear.z = rotated_linear_velocity[2]
            twist.angular.x = rotated_angular_velocity[0]
            twist.angular.y = rotated_angular_velocity[1]
            twist.angular.z = rotated_angular_velocity[2]
            print(twist.linear)
            pub.publish(twist)
            rate.sleep()


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.accel_graphWidget = pg.PlotWidget()
        self.gyro_graphWidget = pg.PlotWidget()
        self.robot_velocity_graphWidget = pg.PlotWidget()

        self.layout.addWidget(self.accel_graphWidget)
        self.layout.addWidget(self.gyro_graphWidget)
        self.layout.addWidget(self.robot_velocity_graphWidget)

        self.accel_graphWidget.setBackground(background_color)
        self.gyro_graphWidget.setBackground(background_color)
        self.robot_velocity_graphWidget.setBackground(background_color)

        self.accel_graphWidget.setTitle("Accelerometer Data Plot", color="#8d6e63", size="20pt")
        self.gyro_graphWidget.setTitle("Gyroscope Data Plot", color="#8d6e63", size="20pt")
        self.robot_velocity_graphWidget.setTitle("Robot Velocity Data Plot", color="#8d6e63", size="20pt")

        styles = {"color": "#f00", "font-size": "15px"}
        self.accel_graphWidget.setLabel("left", "Values", **styles)
        self.accel_graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)
        self.gyro_graphWidget.setLabel("left", "Values", **styles)
        self.gyro_graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)
        self.robot_velocity_graphWidget.setLabel("left", "Values", **styles)
        self.robot_velocity_graphWidget.setLabel("bottom", "Time (milliseconds)", **styles)

        self.accel_graphWidget.addLegend()
        self.gyro_graphWidget.addLegend()
        self.robot_velocity_graphWidget.addLegend()

        self.accel_x_data_line = self.accel_graphWidget.plot([], [], name="accel_x", pen=pg.mkPen(color=accel_x_data_color))
        self.accel_y_data_line = self.accel_graphWidget.plot([], [], name="accel_y", pen=pg.mkPen(color=accel_y_data_color))
        self.accel_z_data_line = self.accel_graphWidget.plot([], [], name="accel_z", pen=pg.mkPen(color=accel_z_data_color))
        self.gyro_x_data_line = self.gyro_graphWidget.plot([], [], name="gyro_x", pen=pg.mkPen(color=gyro_x_data_color))
        self.gyro_y_data_line = self.gyro_graphWidget.plot([], [], name="gyro_y", pen=pg.mkPen(color=gyro_y_data_color))
        self.gyro_z_data_line = self.gyro_graphWidget.plot([], [], name="gyro_z", pen=pg.mkPen(color=gyro_z_data_color))
        self.robot_linear_x_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_linear_x", pen=pg.mkPen(color=accel_x_data_color))
        self.robot_linear_y_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_linear_y", pen=pg.mkPen(color=accel_y_data_color))
        self.robot_linear_z_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_linear_z", pen=pg.mkPen(color=accel_z_data_color))
        self.robot_angular_x_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_angular_x", pen=pg.mkPen(color=gyro_x_data_color))
        self.robot_angular_y_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_angular_y", pen=pg.mkPen(color=gyro_y_data_color))
        self.robot_angular_z_data_line = self.robot_velocity_graphWidget.plot([], [], name="robot_angular_z", pen=pg.mkPen(color=gyro_z_data_color))

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        limit = -1000  # Only plot the last 1000 points

        self.accel_x_data_line.setData(time_data[limit:], accel_x_data[limit:])
        self.accel_y_data_line.setData(time_data[limit:], accel_y_data[limit:])
        self.accel_z_data_line.setData(time_data[limit:], accel_z_data[limit:])
        self.gyro_x_data_line.setData(time_data[limit:], gyro_x_data[limit:])
        self.gyro_y_data_line.setData(time_data[limit:], gyro_y_data[limit:])
        self.gyro_z_data_line.setData(time_data[limit:], gyro_z_data[limit:])
        self.robot_linear_x_data_line.setData(time_data[limit:], robot_linear_velocity_x[limit:])
        self.robot_linear_y_data_line.setData(time_data[limit:], robot_linear_velocity_y[limit:])
        self.robot_linear_z_data_line.setData(time_data[limit:], robot_linear_velocity_z[limit:])
        self.robot_angular_x_data_line.setData(time_data[limit:], robot_angular_velocity_x[limit:])
        self.robot_angular_y_data_line.setData(time_data[limit:], robot_angular_velocity_y[limit:])
        self.robot_angular_z_data_line.setData(time_data[limit:], robot_angular_velocity_z[limit:])

def main():
    # Initialize ROS node
    rospy.init_node('sensor_control_node', anonymous=True)

    # Start WebSocket threads for sensor data collection
    threading.Thread(target=run_websocket).start()

    # Subscribe to odometry data
    rospy.Subscriber('/odom', Odometry, odom_callback)

    # Start publishing Twist commands
    threading.Thread(target=publish_twist_commands).start()

    # Initialize Qt application
    app = QtWidgets.QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

