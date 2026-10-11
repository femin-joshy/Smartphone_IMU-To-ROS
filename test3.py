import websocket
import json
import numpy as np
import time
import threading
from scipy.spatial.transform import Rotation as R

# Shared data
accel_data = []
gyro_data = []
mag_data = []
rotation_vector_data = [] 
time_data = []

def quaternion_to_rotation_matrix(quaternion):
    r = R.from_quat(quaternion) 
    return r.as_matrix()

def on_message_accel(ws, message):
    data = json.loads(message)
    if 'values' in data and len(data['values']) == 3:
        accel_data.append(data['values'])
        time_data.append(data['timestamp'])

def on_message_gyro(ws, message):
    data = json.loads(message)
    if 'values' in data and len(data['values']) == 3:
        gyro_data.append(data['values'])

def on_message_mag(ws, message):
    data = json.loads(message)
    if 'values' in data and len(data['values']) == 3:
        mag_data.append(data['values'])

def on_message_rotation_vector(ws, message):
    data = json.loads(message)
    if 'values' in data and len(data['values']) >= 4:
        rotation_vector_data.append(data['values'][:4])  # Taking first 4 elements (quaternion)

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed: {close_status_code}, {close_msg}")

def on_open(ws):
    print("WebSocket connection opened")

def collect_sensor_data():
    accel_ws = websocket.WebSocketApp(f"ws://192.168.0.193:8080/sensor/connect?type=android.sensor.linear_acceleration",
                                      on_message=on_message_accel,
                                      on_error=on_error,
                                      on_close=on_close)
    gyro_ws = websocket.WebSocketApp(f"ws://192.168.0.193:8080/sensor/connect?type=android.sensor.gyroscope",
                                     on_message=on_message_gyro,
                                     on_error=on_error,
                                     on_close=on_close)
    mag_ws = websocket.WebSocketApp(f"ws://192.168.0.193:8080/sensor/connect?type=android.sensor.magnetic_field",
                                    on_message=on_message_mag,
                                    on_error=on_error,
                                    on_close=on_close)
    rotation_vector_ws = websocket.WebSocketApp(f"ws://192.168.0.193:8080/sensor/connect?type=android.sensor.rotation_vector",
                                                on_message=on_message_rotation_vector,
                                                on_error=on_error,
                                                on_close=on_close)

    threading.Thread(target=accel_ws.run_forever).start()
    threading.Thread(target=gyro_ws.run_forever).start()
    threading.Thread(target=mag_ws.run_forever).start()
    threading.Thread(target=rotation_vector_ws.run_forever).start()

    # Collect data for 10 seconds
    for i in range(10, 0, -1):
        print(f"Collecting data... {i} seconds remaining")
        time.sleep(1)

    accel_ws.close()
    gyro_ws.close()
    mag_ws.close()
    rotation_vector_ws.close()

    print("Stopping data collection...")

    synchronized_data = []
    for t, a, g, m, rv in zip(time_data, accel_data, gyro_data, mag_data, rotation_vector_data):
        quaternion = R.from_euler('xyz', g, degrees=True).as_quat()
        rotation_matrix_computed = quaternion_to_rotation_matrix(quaternion)
        rotation_matrix_from_sensor = quaternion_to_rotation_matrix(rv)
        synchronized_data.append((t, a, g, m, rotation_matrix_computed, rotation_matrix_from_sensor))

    return synchronized_data

if __name__ == "__main__":
    data = collect_sensor_data()

    print("Synchronized Data:")
    for entry in data:
        t, a, g, m, rotation_matrix_computed, rotation_matrix_from_sensor = entry
        print(f"Time: {t}, Accel: {a}, Gyro: {g}, Mag: {m}")
        #print(f"Rotation Matrix from Sensor \n{rotation_matrix_computed}")
        print(f"Rotation Matrix from Sensor: \n{rotation_matrix_from_sensor}\n")
