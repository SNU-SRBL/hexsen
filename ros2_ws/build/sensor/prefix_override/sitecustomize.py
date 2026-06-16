import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/seunghoon/Documents/BYJ-hexsen/ros2_ws/install/sensor'
