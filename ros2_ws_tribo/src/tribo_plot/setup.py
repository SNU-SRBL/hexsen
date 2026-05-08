from setuptools import find_packages, setup

package_name = 'tribo_plot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kang',
    maintainer_email='kang@todo.todo',
    description='Real-time plotting for sensor data using PyQtGraph',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'sensorT_fake = tribo_plot.sensorT_fake:main',
            'plot_sensor = tribo_plot.plot_sensor:main',
            'models = tribo_plot.models:main',
            'app1 = tribo_plot.app1:main',
            'state_manager = tribo_plot.state_manager_node:main',
            'inference = tribo_plot.inference_node:main',
            'app_node = tribo_plot.app_node:main',
            'app2 = tribo_plot.app2:main',
            'app2_old = tribo_plot.app2_old:main',
            'sensorT_large = tribo_plot.sensorT_large:main',
        ],
    },
)
