import rospy
from geometry_msgs.msg import Twist
import websocket
import json
import threading
import time

# Shared data
accel_data = []
gyro_data = []
synchronized_data = []

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

def synchronize_data():
    global synchronized_data
    while accel_data and gyro_data:
        accel_time, accel_x, accel_y, accel_z = accel_data[0]
        gyro_time, gyro_x, gyro_y, gyro_z = gyro_data[0]

        if abs(accel_time - gyro_time) < 0.05:  # 50 ms threshold for synchronization
            synchronized_data.append((accel_time, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z))
            accel_data.pop(0)
            gyro_data.pop(0)
        elif accel_time < gyro_time:
            accel_data.pop(0)
        else:
            gyro_data.pop(0)

def run_websocket():
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

    threading.Thread(target=ws_accel.run_forever).start()
    threading.Thread(target=ws_gyro.run_forever).start()

def publish_twist_commands():
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    rate = rospy.Rate(10)  # 10 Hz

    global linear_velocity_x, linear_velocity_y, linear_velocity_z
    last_time = time.time()

    while not rospy.is_shutdown():
        if synchronized_data:
            current_time, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = synchronized_data.pop(0)
            dt = current_time - last_time
            last_time = current_time

            # Integrate acceleration to get velocity
            linear_velocity_x += accel_x * dt
            linear_velocity_y += accel_y * dt
            linear_velocity_z += accel_z * dt

            twist = Twist()
            twist.linear.x = linear_velocity_x
            twist.linear.y = linear_velocity_y
            twist.linear.z = linear_velocity_z
            twist.angular.x = gyro_x
            twist.angular.y = gyro_y
            twist.angular.z = gyro_z
            
            pub.publish(twist)
            rate.sleep()

if __name__ == "__main__":
    rospy.init_node('sensor_control_node')  # Initialize ROS in the main thread
    threading.Thread(target=run_websocket).start()
    threading.Thread(target=publish_twist_commands).start()
