# hexsen

Control and data-logging stack for a UR5e robot arm fitted with a 6-axis (hexadecant) force/tactile sensor and an IMU sensor. UR motion is driven directly over RTDE from a Python/conda environment, while sensor acquisition and logging run as ROS 2 nodes.

## 1. Hardware Setup

1. Power on the UR5e robot.
2. Confirm the robot-side IP on the teach pendant: `192.168.10.2`.
3. Set the computer's network interface to the same subnet, then verify connectivity:
   ```bash
   ping 192.168.10.2
   ```
4. On the pendant, open **Installation** and adjust the TCP pose to match the mounted tool.
5. On the pendant, switch control from **Local** to **Remote** so the computer can drive the robot.
6. The hex sensor connects over Bluetooth (BLE), so it has no USB/tty number to worry about. The IMU sensor connects over USB serial, so check which `/dev/ttyUSB*` (or similar) port it enumerates as.
   - USB enumeration order depends on plug-in order, so if you plug in other USB devices as well, be careful that they don't shift which port the IMU sensor lands on — verify its assigned port before running the sensor node.

## 2. Software Setup

The UR control script is run outside of ROS 2, in a conda environment:

```bash
conda activate guest
```

Before moving the robot, jog it to your desired starting pose with [ur_test.py](ur_test.py) — edit the target pose/joint values in the script for your experiment, then run it.

## 3. Repository Layout

| Path | Description |
| --- | --- |
| [data/](data/) | Experiment data logs, plotting utilities, and path/trajectory generators |
| [walk/](walk/) | Walking-trajectory CSV data |
| [ros2_ws/](ros2_ws/) | ROS 2 workspace (build with `colcon`) |
| [ros2_ws/src/sensor/](ros2_ws/src/sensor/) | Hex sensor driver (Python, BLE via `bleak`) — node `sensor_hex` |
| [ros2_ws/src/sensorcpp/](ros2_ws/src/sensorcpp/) | IMU sensor driver (C++, serial) — node `imu_pub` |
| [ros2_ws/src/writer/](ros2_ws/src/writer/) | UR RTDE receiver and data logger (C++) — nodes `ur_rtde_r`, `writer_v4` |
| [ur_test.py](ur_test.py) | Jog the UR to an initial/desired pose (conda, no ROS dependency) |
| [ur_test_orie_0603.py](ur_test_orie_0603.py) | Main UR control script — runs standalone via conda, independent of ROS 2 |

## 4. Running the ROS 2 Nodes

### 4.1 Build

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --packages-select sensor sensorcpp writer
source install/setup.bash
```

Re-run `colcon build` (from `ros2_ws/`) whenever node source changes, then re-source `install/setup.bash`.

### 4.2 Per-terminal setup

Every node runs as its own process, so each is normally started in its own terminal. In **each** terminal, `cd` into `ros2_ws/` and source both setup files once before any `ros2 run` command:

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

`ros2 run` itself is then always run from `ros2_ws/`, in a terminal that has already sourced both files.

### 4.3 Hex sensor node (needs conda's Python)

`sensor_hex` depends on packages installed in the conda environment, so point ROS at that Python **before** sourcing ROS in this terminal:

```bash
cd ros2_ws
conda activate guest
export PYTHONPATH=$CONDA_PREFIX/lib/python3.10/site-packages:$PYTHONPATH
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run sensor sensor_hex
```

### 4.4 IMU sensor node

```bash
ros2 run sensorcpp imu_pub
```

### 4.5 UR RTDE receiver and logger

```bash
ros2 run writer ur_rtde_r    # RTDE receiver
ros2 run writer writer_v4    # data logger
```

### 4.6 Running everything together

Running five terminals by hand (hex sensor, IMU, RTDE receiver, logger, UR control script) is tedious, and the hex sensor node needs time to scan for and connect to its Bluetooth device before it starts publishing. Prefer one of:

- **tmux** (recommended) — lets you stagger each program's start time, e.g. start `sensor_hex` first and wait for the Bluetooth connection before starting the others.
- A ROS 2 launch file, if you want a single command once startup ordering isn't an issue.

## 5. UR Control Script

[ur_test_orie_0603.py](ur_test_orie_0603.py) is the main UR control program. It talks to the robot directly over RTDE and runs independently of ROS 2, in the conda environment:

```bash
conda activate guest
python ur_test_orie_0603.py
```

## 6. Git Quick Reference

```bash
git commit   # record local changes
git push     # upload to remote

git fetch    # check remote changes
git pull     # download remote changes
```
