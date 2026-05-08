import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui
from scipy.interpolate import splprep, splev
import time
import os


class AppPlotter(QtWidgets.QMainWindow):
    def __init__(self, buffer_size=5000):
        super().__init__()

        self.setWindowTitle('Triboresistive Sliding Sensor Application')
        self.setFixedSize(QtCore.QSize(1600, 900)) # Ratio 16:9
        self.setStyleSheet("background-color: black;")
        
        layout = QtWidgets.QGridLayout()

        font=QtGui.QFont()
        styles1 = {"color": "white", "font-size": "16pt"}
        styles2 = {"color": "white", "font-size": "12pt"}

        # Widget 1: Trajectory (X-Y cumulative sum of velocities)
        self.w1 = pg.PlotWidget()
        self.w1.setTitle('Estimated Trajectory', bold=True, color='w', size='20pt')
        self.w1.setFixedSize(680, 680)
        self.w1.setXRange(0, 30, padding=0.1)
        self.w1.setYRange(0, 30, padding=0.1)
        font.setPixelSize(26)
        self.w1.getAxis("bottom").setStyle(tickFont = font)
        self.w1.getAxis("left").setStyle(tickFont = font)
        # tickTextOffset = 0..01
        self.w1.setLabel('bottom', 'X (mm)', **styles1)
        self.w1.setLabel('left', 'Y (mm)', **styles1)
        self.w1.showGrid(x=True, y=True, alpha=0.4)
        # 2D Gradient Scatter
        self.gradient_N = 400 # 200
        self.cmap = pg.colormap.get('plasma')
        self.trajectory_scatter = pg.ScatterPlotItem(
            x=np.array([0]),
            y=np.array([0]),
            size=8,
            pen=None,
            brush=None
        )
        self.w1.addItem(self.trajectory_scatter)

    
        # Widget 2: Velocity over time (two plots vertically)
        self.w2 = pg.GraphicsLayoutWidget()
        title = pg.LabelItem(
            text="ΔX and ΔY", 
            size="20pt", 
            bold=True, 
            color='w'   # white
        )
        self.w2.addItem(title, row=0, col=0, colspan=2)
        self.w2.nextRow()
        self.p_dx = self.w2.addPlot(row=1, col=0)
        self.p_dy = self.w2.addPlot(row=2, col=0)
        self.p_dx.setLabel('bottom', 'Time Steps', **styles1)
        self.p_dx.setLabel('left', 'ΔX (mm)', **styles1)
        self.p_dy.setLabel('bottom', 'Time Steps', **styles1)
        self.p_dy.setLabel('left', 'ΔY (mm)', **styles1)
        self.WINDOW_VEL = 30 # time steps
        self.p_dx.setXRange(0, self.WINDOW_VEL, padding=0)
        self.p_dy.setXRange(0, self.WINDOW_VEL, padding=0)
        self.p_dx.setYRange(-2.0, 2.0, padding=0.2)
        self.p_dy.setYRange(-2.0, 2.0, padding=0.2)
        self.vel_x_plot = self.p_dx.plot(pen=pg.mkPen('r', width=4))
        self.vel_y_plot = self.p_dy.plot(pen=pg.mkPen('b', width=4))

        # Widget 3: State information
        image_dir_root = './src/tribo_plot/tribo_plot/utils/state_image'
        state_names = ['idle', 'touch', 'stay', 'slide', 'detach']
        self.state_images = [
            QtGui.QPixmap(os.path.join(image_dir_root, f'state_{name}.png'))
            for name in state_names]
        self.w3 = QtWidgets.QLabel()
        self.w3.setPixmap(self.state_images[0])  # Initial state: idle
        self.w3.setScaledContents(True)
        self.w3.setAlignment(QtCore.Qt.AlignCenter)

        # Widget 4: Sensor values (4 channels)
        self.w4 = pg.GraphicsLayoutWidget()
        title = pg.LabelItem(
            text="Sensor Values",
            size="20pt",
            bold=True,
            color='w'   # white
        )
        self.w4.addItem(title, row=0, col=0, colspan=2)
        self.w4.nextRow()
        self.p_s1 = self.w4.addPlot(row=1, col=0, title='Channel 1')
        self.p_s2 = self.w4.addPlot(row=2, col=0, title='Channel 2')
        self.p_s3 = self.w4.addPlot(row=3, col=0, title='Channel 3')
        self.p_s4 = self.w4.addPlot(row=4, col=0, title='Channel 4')

        self.p_s1.enableAutoRange(x=False, y=False)
        self.p_s2.enableAutoRange(x=False, y=False)
        self.p_s3.enableAutoRange(x=False, y=False)
        self.p_s4.enableAutoRange(x=False, y=False)
        
        for p in [self.p_s1, self.p_s2, self.p_s3, self.p_s4]:
            p.setLabel('bottom', 'Time (s)', **styles2)
            p.setLabel('left', 'Induced Voltaget (mV)', **styles2)
            p.setYRange(-100, 100)
        
        self.sensor_plots = [
            self.p_s1.plot(pen=pg.mkPen('w', width=2)),
            self.p_s2.plot(pen=pg.mkPen((187, 85, 102), width=2)),
            self.p_s3.plot(pen=pg.mkPen((221, 170, 51), width=2)),
            self.p_s4.plot(pen=pg.mkPen((0, 68, 136), width=2)),
        ]
        self.WINDOW = 5.0  # seconds

        # Add widgets to layout
        layout.addWidget(self.w1, 0, 0, 9, 6)
        layout.addWidget(self.w2, 0, 6, 4, 5)
        layout.addWidget(self.w3, 4, 6, 5, 5)
        layout.addWidget(self.w4, 0, 11, 9, 5)
        
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Data storage
        self.buffer_size = buffer_size
        self.buffer = np.zeros((4, self.buffer_size))

        # Position information
        # Already roated +90 degree !!!!!
        # self.pose_init = np.array([[0.00172, 0.02553], # m
        #                           [0.00824, 0.02397], # a
        #                           [0.00701, 0.02621], # z
        #                           [0.00621, 0.01610], # e
        #                           [0.00000, 0.01148]]) # maze
        
        # self.pose_init = np.array([[0.020, 0.025],
        #                            [0.008, 0.024],
        #                            [0.007, 0.026],
        #                            [0.006, 0.026]]) # srbl
        
        # Sensor dimensions (in meters) - adjust based on actual sensor size
        self.sensor_width = 0.03  # 30mm
        self.sensor_height = 0.03  # 30mm
        self.sensor_origin = np.array([0.0, 0.0])  # Bottom-left corner of sensor
        
        self.pose_init = np.array([0.0, 0.0])

        self.n_touch = 0
        self.current_touch_idx = 0  # Index for current trajectory (set at touch start)

        # Velocity and trajectory data - preallocated circular buffers
        self.max_trajectory_size = 10000  # Preallocate max size
        self.velocity_stack = np.zeros((self.max_trajectory_size, 2), dtype=np.float32)
        self.trajectory = np.zeros((self.max_trajectory_size, 2), dtype=np.float32)
        self.velocity_idx = 0  # Current write index
        self.trajectory_idx = 0

        self.slide_factor = 1.5  # Scaling factor for velocity
        
        # Sensor data - circular buffers (no Python lists!)
        self.sensor_buffer_size = 5000
        self.sensor_data = np.zeros((4, self.sensor_buffer_size), dtype=np.float32)
        self.sensor_idx = 0  # Circular index for sensor data
        self.sensor_time = np.linspace(0.0, 5.0, self.sensor_buffer_size, dtype=np.float32)
        
        # Timer for updating plots
        self.t0 = time.perf_counter()
        
        # Sensor sampling rate (1.2ms interval = 833 Hz)
        self.sensor_sampling_rate = 833.0  # Hz
        self.sensor_dt = 1.0 / self.sensor_sampling_rate  # seconds per sample
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)  # Update every 100ms
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def callback(self, data):
        """Update sensor buffer with new data - Optimized with circular indexing"""
        self.buffer = np.roll(self.buffer, -1, axis=1)
        self.buffer[:, -1] = data
        
        # Update sensor circular buffer (O(1) instead of O(n))
        self.sensor_data[:, self.sensor_idx] = data
        self.sensor_idx = (self.sensor_idx + 1) % self.sensor_buffer_size

    def add_velocity(self, vel):
        """Add velocity to preallocated buffer - Optimized without vstack"""
        vel = np.array(vel, dtype=np.float32)

        # Rotation by +90 degrees around center (0, 0)
        vel = np.array([-vel[1], vel[0]], dtype=np.float32)
        vel = vel * self.slide_factor # scale factor
        # Direct assignment to preallocated array
        self.velocity_stack[self.velocity_idx] = vel
        
        # Calculate trajectory point
        if self.velocity_idx == 0:
            trajectory_point = vel
        else:
            trajectory_point = self.trajectory[self.velocity_idx - 1] + vel
        
        self.trajectory[self.trajectory_idx] = trajectory_point
        
        # Increment indices
        self.velocity_idx += 1
        self.trajectory_idx += 1

    def reset(self):
        """Reset trajectory and velocity when detach/idle - Optimized"""
        self.velocity_idx = 0
        self.trajectory_idx = 0
        # Arrays remain preallocated, just reset indices
        # self.pose_init = np.array([0.0, 0.0]) # no need?

    def add_touch(self):
        self.n_touch += 1
    
    def set_touch_pose(self, pose):
        """
        Update current touch pose from alpha, beta values
        pose: [alpha, beta] - normalized sensor coordinates (0-1 range)
        """
        alpha, beta = pose[0], pose[1]
        touch_factors = [1.2, 1.0]  # Scale factor for touch position adjustment
        alpha = min(max(alpha * touch_factors[0], 0.0), 1.0)
        beta = min(max(beta * touch_factors[1], 0.0), 1.0)
        # Map normalized coordinates to physical position
        # alpha and beta are normalized (0-1), convert to sensor dimensions
        x = self.sensor_origin[0] + alpha * self.sensor_width
        y = self.sensor_origin[1] + beta * self.sensor_height
        
        # Rotate point by +90 degrees around sensor center
        center = np.array([self.sensor_width / 2, self.sensor_height / 2])
        point = np.array([x, y])
        translated_point = point - center
        
        # Rotation matrix for +90 degrees (counter-clockwise)
        rad = np.deg2rad(90)
        rotation_matrix = np.array([[np.cos(rad), -np.sin(rad)],
                                     [np.sin(rad),  np.cos(rad)]])
        rotated_point = translated_point @ rotation_matrix.T
        rotated_point += center
        
        self.pose_init = rotated_point.astype(np.float32)

    def update_state(self, state):
        match state:
            case 'idle':
                self.w3.setPixmap(self.state_images[0])
            case 'touch':
                self.w3.setPixmap(self.state_images[1])
            case 'stay':
                self.w3.setPixmap(self.state_images[2])
            case 'slide':
                self.w3.setPixmap(self.state_images[3])
            case 'detach':
                self.w3.setPixmap(self.state_images[4])
            case _:
                pass

    def update_plots(self):
        """Update all plots with current data - Optimized"""
        t = time.perf_counter() - self.t0

        # Get actual slices (avoid copying)
        vel_len = self.velocity_idx
        traj_len = self.trajectory_idx
        
        # Update trajectory plot with only filled portion
        if traj_len > 0:
            traj = self.trajectory[:traj_len]
            # start_pos = self.pose_init[self.current_touch_idx % 4] # 5
            start_pos = self.pose_init
            traj_disp = (start_pos + traj) * 1000 # convert to mm

            draw_raw = traj_len < 3

            if draw_raw:
                x_draw = traj_disp[:, 0]
                y_draw = traj_disp[:, 1]
                brushes = None
            else:
                try:
                    x = traj_disp[:, 0]
                    y = traj_disp[:, 1]
                    # Spline interpolation for smooth trajectory
                    tck, u = splprep([x, y], s=0)
                    unew = np.linspace(0, 1.0, self.gradient_N * 2)
                    x_draw, y_draw = splev(unew, tck)

                    M = len(x_draw)

                    if M < self.gradient_N:
                        start = 0.95 * (1 - M / self.gradient_N)
                        brushes = self.cmap.map(np.linspace(start, 0.95, M))
                    else:
                        head = self.cmap.map(np.linspace(0.3, 0.95, self.gradient_N))
                        brush_fix = np.array([head[0]] * (M - self.gradient_N))  # Make first quarter same color
                        brushes = np.vstack((brush_fix, head))
                except Exception as e:
                    print(f"Spline fitting error: {e}")
                    x_draw = traj_disp[:, 0]
                    y_draw = traj_disp[:, 1]
                    brushes = None

            self.trajectory_scatter.setData(
                x=x_draw, 
                y=y_draw, 
                brush=brushes)
        else:
            self.trajectory_scatter.setData(x=np.array([0]), y=np.array([0]), brush=None)
            
        
        # Update velocity plots with only filled portion
        if vel_len > 0:
            time_steps = np.arange(vel_len)
            velocity_display = self.velocity_stack[:vel_len] * 1000 # convert to mm
            self.vel_x_plot.setData(time_steps, velocity_display[:, 0])
            self.vel_y_plot.setData(time_steps, velocity_display[:, 1])

            self.p_dx.setXRange(vel_len - self.WINDOW_VEL, vel_len, padding=0)
            self.p_dy.setXRange(vel_len - self.WINDOW_VEL, vel_len, padding=0)
        
        # Update sensor plots - use circular buffer view
        # Reshape data to display in order (handle circular wrap-around)
        sensor_display = np.roll(self.sensor_data, self.sensor_buffer_size - self.sensor_idx, axis=1)
        sensor_display = sensor_display * (6.144 / 32768) * 1000 # convert to mV
        # generate X from actual sampling times (1.2ms intervals)
        num_samples = len(sensor_display[0])
        self.sensor_time = t - np.arange(num_samples - 1, -1, -1, dtype=np.float32) * self.sensor_dt
        for i in range(4):
            self.sensor_plots[i].setData(self.sensor_time, sensor_display[i])
            
        self.p_s1.setXRange(t - self.WINDOW, t, padding=0)
        self.p_s2.setXRange(t - self.WINDOW, t, padding=0)
        self.p_s3.setXRange(t - self.WINDOW, t, padding=0)
        self.p_s4.setXRange(t - self.WINDOW, t, padding=0)
    


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main = AppPlotter()
    main.show()
    app.exec()