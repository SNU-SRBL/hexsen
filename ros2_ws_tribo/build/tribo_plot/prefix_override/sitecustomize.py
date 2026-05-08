import sys
if sys.prefix == '/home/kang/miniconda3/envs/tribo':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/kang/Documents/tribo-slide/ros2_ws/install/tribo_plot'
