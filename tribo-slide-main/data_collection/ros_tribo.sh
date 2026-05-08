#!/bin/bash
source /opt/ros/humble/setup.bash
conda activate tribo
export PYTHONPATH=/opt/ros/humble/lib/python3.10/site-packages:$PYTHONPATH
export PYTHONPATH=/home/kang/miniconda3/envs/tribo/lib/python3.10/site-packages:$PYTHONPATH
colcon build
source install/setup.bash