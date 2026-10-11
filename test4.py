#to check if integration works using sin or e or cos.
#linear_velocity_x += accel_x * dt
#linear_velocity_y += accel_y * dt
#linear_velocity_z += accel_z * dt
import numpy as np
import matplotlib.pyplot as plt

dt = 0.01
total_time = 10
time_steps = np.arange(0, total_time, dt)

accel_x = np.sin(time_steps)
accel_y = np.exp(time_steps)
accel_z = np.cos(time_steps)

linear_velocity_x = np.zeros_like(time_steps)
linear_velocity_y = np.zeros_like(time_steps)
linear_velocity_z = np.zeros_like(time_steps)

for i in range(1, len(time_steps)):
    linear_velocity_x[i] = linear_velocity_x[i-1] + accel_x[i] * dt
    linear_velocity_y[i] = linear_velocity_y[i-1] + accel_y[i] * dt
    linear_velocity_z[i] = linear_velocity_z[i-1] + accel_z[i] * dt


plt.figure(figsize=(12, 8))

plt.subplot(3, 2, 1)
plt.plot(time_steps, accel_x, label='accel_x (sin)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration')
plt.legend()

plt.subplot(3, 2, 3)
plt.plot(time_steps, accel_y, label='accel_y (exp)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration')
plt.legend()

plt.subplot(3, 2, 5)
plt.plot(time_steps, accel_z, label='accel_z (cos)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration')
plt.legend()

plt.subplot(3, 2, 2)
plt.plot(time_steps, linear_velocity_x, label='linear_velocity_x')
plt.xlabel('Time (s)')
plt.ylabel('Linear Velocity')
plt.legend()

plt.subplot(3, 2, 4)
plt.plot(time_steps, linear_velocity_y, label='linear_velocity_y')
plt.xlabel('Time (s)')
plt.ylabel('Linear Velocity')
plt.legend()

plt.subplot(3, 2, 6)
plt.plot(time_steps, linear_velocity_z, label='linear_velocity_z')
plt.xlabel('Time (s)')
plt.ylabel('Linear Velocity')
plt.legend()

plt.tight_layout()
plt.show()
