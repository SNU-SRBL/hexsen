import matplotlib
matplotlib.use('QtAgg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

experiment_name = ""
# Read the data files
# sensor_data = pd.read_csv(f'/home/seunghoon/Documents/BYJ-6axis/data/data_{experiment_name}/Log_Sensor_Hex_.txt', header=None)
sensor_data = pd.read_csv(f'/home/seunghoon/Documents/BYJ-6axis/data/Log_Sensor_Hex_.txt', header=None)

# Extract columns for sensor data
time_sensor = sensor_data.iloc[:, 0]
v1 = sensor_data.iloc[:, 2]
v2 = sensor_data.iloc[:, 3]
v3 = sensor_data.iloc[:, 4]
v4 = sensor_data.iloc[:, 5]
v5 = sensor_data.iloc[:, 6]
v6 = sensor_data.iloc[:, 7]


# Create Figure 2: Sensor Data
fig2, axes2 = plt.subplots(2, 3, figsize=(15, 10))
fig2.suptitle('Sensor Data (Voltage)', fontsize=16, fontweight='bold')

# Sensor plots
colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'orange']
sensors = [v1, v2, v3, v4, v5, v6]
labels = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']

for idx, (ax, sensor, label, color) in enumerate(zip(axes2.flat, sensors, labels, colors)):
    ax.scatter(time_sensor, sensor, color=color, s=10)
    # ax.plot(time_sensor, sensor, color=color, linewidth=1.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel(f'{label} Voltage')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'{label} vs Time')
    # ax.set_xlim([25, 30])
    #ax.set_ylim([1.5, 1.55])

plt.tight_layout()
# plt.savefig('/home/seunghoon/Documents/BYJ-6axis/data/sensor_data_plot.png', dpi=300, bbox_inches='tight')
plt.show()

print("Plots saved successfully!")
# print("Robot position plot: /home/seunghoon/Documents/BYJ-6axis/data/robot_position_plot.png")
# print("Sensor data plot: /home/seunghoon/Documents/BYJ-6axis/data/sensor_data_plot.png")