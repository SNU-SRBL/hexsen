from setuptools import find_packages, setup

package_name = 'sensor'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'bleak'],
    zip_safe=True,
    maintainer='seunghoon',
    maintainer_email='littlekang97@gmail.com',
    description='6-axis sensor BLE publisher for ROS2',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'sensor_hex=sensor.sensor_hex:main',
        ],
    },
)
