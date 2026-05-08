## Tribo Project

This repository contains all components of the Tribo touch sensing project:

- `ros2_ws/`: ROS2 packages for real-time data collection and model inference.
- `data_collection/`: Trajectory generation tools using SVG and Python.
- `MLSTM-FCN-1/`: Original TensorFlow1 implementation of the MLSTM-FCN model.
- `MLSTM-FCN-torch/`: Rewritten PyTorch implementation adapted for Tribo data.

### Prerequisites
Create the Environment
```sh
conda env create -f environment.yml
conda activate tribo
pip install -r requirements.txt
```
