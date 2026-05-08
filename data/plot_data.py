import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

experiment_name = "circle"
# Read the data files
robot_data = pd.read_csv(f'/home/seunghoon/Documents/BYJ-6axis/data/data_{experiment_name}/Log_Robot_Pos_.txt', header=None)
sensor_data = pd.read_csv(f'/home/seunghoon/Documents/BYJ-6axis/data/data_{experiment_name}/Log_Sensor_Hex_.txt', header=None)

# Extract columns for robot position data
time_robot = robot_data.iloc[:, 0]
x = robot_data.iloc[:, 1]
y = robot_data.iloc[:, 2]
z = robot_data.iloc[:, 3]
rx = robot_data.iloc[:, 4]
ry = robot_data.iloc[:, 5]
rz = robot_data.iloc[:, 6]

# Extract columns for sensor data
time_sensor = sensor_data.iloc[:, 0]
v1 = sensor_data.iloc[:, 1]
v2 = sensor_data.iloc[:, 2]
v3 = sensor_data.iloc[:, 3]
v4 = sensor_data.iloc[:, 4]
v5 = sensor_data.iloc[:, 5]
v6 = sensor_data.iloc[:, 6]

# Create Figure 1: Robot Position Data
fig1, axes1 = plt.subplots(2, 3, figsize=(15, 10))
fig1.suptitle('Robot Position Data', fontsize=16, fontweight='bold')

# Position plots
axes1[0, 0].plot(time_robot, x, 'b-', linewidth=1.5)
axes1[0, 0].set_xlabel('Time (s)')
axes1[0, 0].set_ylabel('X Position')
axes1[0, 0].grid(True, alpha=0.3)
axes1[0, 0].set_title('X Position vs Time')

axes1[0, 1].plot(time_robot, y, 'g-', linewidth=1.5)
axes1[0, 1].set_xlabel('Time (s)')
axes1[0, 1].set_ylabel('Y Position')
axes1[0, 1].grid(True, alpha=0.3)
axes1[0, 1].set_title('Y Position vs Time')

axes1[0, 2].plot(time_robot, z, 'r-', linewidth=1.5)
axes1[0, 2].set_xlabel('Time (s)')
axes1[0, 2].set_ylabel('Z Position')
axes1[0, 2].grid(True, alpha=0.3)
axes1[0, 2].set_title('Z Position vs Time')

# Rotation plots
axes1[1, 0].plot(time_robot, rx, 'c-', linewidth=1.5)
axes1[1, 0].set_xlabel('Time (s)')
axes1[1, 0].set_ylabel('RX Rotation')
axes1[1, 0].grid(True, alpha=0.3)
axes1[1, 0].set_title('RX Rotation vs Time')

axes1[1, 1].plot(time_robot, ry, 'm-', linewidth=1.5)
axes1[1, 1].set_xlabel('Time (s)')
axes1[1, 1].set_ylabel('RY Rotation')
axes1[1, 1].grid(True, alpha=0.3)
axes1[1, 1].set_title('RY Rotation vs Time')

axes1[1, 2].plot(time_robot, rz, 'orange', linewidth=1.5)
axes1[1, 2].set_xlabel('Time (s)')
axes1[1, 2].set_ylabel('RZ Rotation')
axes1[1, 2].grid(True, alpha=0.3)
axes1[1, 2].set_title('RZ Rotation vs Time')

plt.tight_layout()
# plt.savefig('/home/seunghoon/Documents/BYJ-6axis/data/robot_position_plot.png', dpi=300, bbox_inches='tight')
plt.show()

# Create Figure 2: Sensor Data
fig2, axes2 = plt.subplots(2, 3, figsize=(15, 10))
fig2.suptitle('Sensor Data (Voltage)', fontsize=16, fontweight='bold')

# Sensor plots
colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'orange']
sensors = [v1, v2, v3, v4, v5, v6]
labels = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']

for idx, (ax, sensor, label, color) in enumerate(zip(axes2.flat, sensors, labels, colors)):
    ax.plot(time_sensor, sensor, color=color, linewidth=1.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel(f'{label} Voltage')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'{label} vs Time')

plt.tight_layout()
# plt.savefig('/home/seunghoon/Documents/BYJ-6axis/data/sensor_data_plot.png', dpi=300, bbox_inches='tight')
plt.show()

print("Plots saved successfully!")
# print("Robot position plot: /home/seunghoon/Documents/BYJ-6axis/data/robot_position_plot.png")
# print("Sensor data plot: /home/seunghoon/Documents/BYJ-6axis/data/sensor_data_plot.png")