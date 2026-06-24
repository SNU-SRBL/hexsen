import matplotlib
matplotlib.use('QtAgg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Read the IMU data
imu_data = pd.read_csv('/home/seunghoon/Documents/BYJ-hexsen/data/Log_Sensor_IMU_.txt', header=0)

# Extract time column
time = imu_data.iloc[:, 0]

# Extract IMU sensor 0 (columns 1-10)
# z, y, x, w, angvel_x, angvel_y, angvel_z, acc_x, acc_y, acc_z
imu0_z = imu_data.iloc[:, 1]
imu0_y = imu_data.iloc[:, 2]
imu0_x = imu_data.iloc[:, 3]
imu0_w = imu_data.iloc[:, 4]
imu0_angvel_x = imu_data.iloc[:, 5]
imu0_angvel_y = imu_data.iloc[:, 6]
imu0_angvel_z = imu_data.iloc[:, 7]
imu0_acc_x = imu_data.iloc[:, 8]
imu0_acc_y = imu_data.iloc[:, 9]
imu0_acc_z = imu_data.iloc[:, 10]

# Extract IMU sensor 1 (columns 11-20)
# z, y, x, w, angvel_x, angvel_y, angvel_z, acc_x, acc_y, acc_z
imu1_z = imu_data.iloc[:, 11]
imu1_y = imu_data.iloc[:, 12]
imu1_x = imu_data.iloc[:, 13]
imu1_w = imu_data.iloc[:, 14]
imu1_angvel_x = imu_data.iloc[:, 15]
imu1_angvel_y = imu_data.iloc[:, 16]
imu1_angvel_z = imu_data.iloc[:, 17]
imu1_acc_x = imu_data.iloc[:, 18]
imu1_acc_y = imu_data.iloc[:, 19]
imu1_acc_z = imu_data.iloc[:, 20]

# Create Figure 1: IMU Sensor 0
fig1, axes1 = plt.subplots(3, 3, figsize=(15, 12))
fig1.suptitle('IMU Sensor 0 Data', fontsize=16, fontweight='bold')

imu0_data = [imu0_z, imu0_y, imu0_x, imu0_w, imu0_angvel_x, imu0_angvel_y, imu0_angvel_z, imu0_acc_x, imu0_acc_y, imu0_acc_z]
imu0_labels = ['Z (Quat)', 'Y (Quat)', 'X (Quat)', 'W (Quat)', 'AngVel_X', 'AngVel_Y', 'AngVel_Z', 'Acc_X', 'Acc_Y', 'Acc_Z']
colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'orange', 'purple', 'brown', 'pink', 'gray']

for idx, (ax, data, label, color) in enumerate(zip(axes1.flat, imu0_data, imu0_labels, colors)):
    ax.plot(time, data, color=color, linewidth=1, alpha=0.8)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel(label)
    ax.grid(True, alpha=0.3)
    ax.set_title(f'IMU0: {label} vs Time')

plt.tight_layout()
plt.savefig('/home/seunghoon/Documents/BYJ-hexsen/data/imu0_plot.png', dpi=300, bbox_inches='tight')
plt.show(block=False)

# Create Figure 2: IMU Sensor 1
fig2, axes2 = plt.subplots(3, 3, figsize=(15, 12))
fig2.suptitle('IMU Sensor 1 Data', fontsize=16, fontweight='bold')

imu1_data = [imu1_z, imu1_y, imu1_x, imu1_w, imu1_angvel_x, imu1_angvel_y, imu1_angvel_z, imu1_acc_x, imu1_acc_y, imu1_acc_z]
imu1_labels = ['Z (Quat)', 'Y (Quat)', 'X (Quat)', 'W (Quat)', 'AngVel_X', 'AngVel_Y', 'AngVel_Z', 'Acc_X', 'Acc_Y', 'Acc_Z']

for idx, (ax, data, label, color) in enumerate(zip(axes2.flat, imu1_data, imu1_labels, colors)):
    ax.plot(time, data, color=color, linewidth=1, alpha=0.8)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel(label)
    ax.grid(True, alpha=0.3)
    ax.set_title(f'IMU1: {label} vs Time')

plt.tight_layout()
plt.savefig('/home/seunghoon/Documents/BYJ-hexsen/data/imu1_plot.png', dpi=300, bbox_inches='tight')
plt.show()

print("IMU plots created successfully!")
print("IMU Sensor 0 plot saved: /home/seunghoon/Documents/BYJ-hexsen/data/imu0_plot.png")
print("IMU Sensor 1 plot saved: /home/seunghoon/Documents/BYJ-hexsen/data/imu1_plot.png")