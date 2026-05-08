import argparse
import numpy as np
from path_basic_svg import extract_path_coordinates, SLIDE_MAP
from path_basic import generate_path, generate_circle_path, SHAPE_LIST

class PathGenerator:
    def __init__(self, basic_array: np.ndarray, x=0.0225, y=0.50000, z=0.440, v: float=0.06, hz: int=20):
        self.x = x
        self.y = y
        self.z = z
        self.rx = 0.0 # 2025-07 rx ry rz = [1.220, 1.176, 1.184]
        self.ry = -1/2 * np.pi
        self.rz = 0.0

        self.height = 0.1 # [m]; 0.1m = 100mm = 10cm

        self.v = v
        self.hz = hz
        self.base_pose = np.array([self.x, self.y, self.z, self.rx, self.ry, self.rz])

        # Base Path
        self.out = basic_array

        self.x_i = self.out[0, 0]
        self.y_i = self.out[0, 1]
        self.x_e = self.out[-1, 0]
        self.y_e = self.out[-1, 1]

    def generate_init(self):
        # 2025-07: 3 seconds * 20 Hz = 60 steps
        n_steps = int(3 * self.hz) # 3 seconds pause
        path_array = np.array([[self.x_i, self.y_i, self.height, 0, 0, 0] for _ in range(n_steps)]) # 3 second pause
        return path_array

    def generate_path1(self):
        # Path 1: z + height -> z
        total_time = self.height /self.v # 0.1m / v along z axis
        steps = int(np.ceil(total_time * self.hz)) # round up
        z_values = np.linspace(self.height, 0, steps)
        path_array = np.array([[self.x_i, self.y_i, z, 0, 0, 0] for z in z_values])
        pause_steps = 1 * self.hz  # 1 second pause
        pause_array = np.array([[self.x_i, self.y_i, z_values[-1], 0, 0, 0] for _ in range(pause_steps)]) # 1 second pause
        return np.concatenate((path_array, pause_array), axis=0)

    def generate_path2(self):
        # Path 2: Basic XY Path
        path_array = np.array([[self.out[i, 0], self.out[i, 1], 0, 0, 0, 0] for i in range(self.out.shape[0])])
        pause_steps = 1 * self.hz  # 1 second pause
        pause_array = np.array([[self.x_e, self.y_e, 0, 0, 0, 0] for _ in range(pause_steps)]) # 1 second pause
        return np.concatenate((path_array, pause_array), axis=0)

    def generate_path3(self):
        # Path 3: z -> z + height
        total_time = self.height / self.v
        steps = int(np.ceil(total_time * self.hz))
        z_values = np.linspace(0, self.height, steps)
        path_array = np.array([[self.x_e, self.y_e, z, 0, 0, 0] for z in z_values])
        pause_steps = int(0.5 * self.hz)  # 0.5 second pause
        pause_array = np.array([[self.x_e, self.y_e, z_values[-1], 0, 0, 0] for _ in range(pause_steps)]) # 0.5 second pause
        return np.concatenate((path_array, pause_array), axis=0)

    def generate_path4(self):
        # Path 4 : Returning
        distance = np.sqrt((self.x_i-self.x_e)**2 + (self.y_i-self.y_e)**2)
        distance = max(0.02, distance) # Minimum length
        total_time = distance / self.v # [sec]
        steps = int(np.ceil(total_time * self.hz))
        x_values = np.linspace(self.x_e, self.x_i, steps)
        y_values = np.linspace(self.y_e, self.y_i, steps)
        path_array = np.array([[x, y, self.height, 0, 0, 0] for x, y in zip(x_values, y_values)])
        return path_array

    def generate_total_path(self):
        path_init = self.generate_init()
        path1 = self.generate_path1()
        path2 = self.generate_path2()
        path3 = self.generate_path3()
        path4 = self.generate_path4()

        full_path = np.concatenate((path_init, path1, path2, path3, path4), axis=0)

        # Add the base array element-wise to each row
        full_path_with_base = full_path + self.base_pose
        return full_path_with_base

    def save(self, filename="./test.csv"):
        path_array = self.generate_total_path()
        np.savetxt(filename, path_array, delimiter=",", fmt='%.5f',comments='')
        print(f"Saved {filename}")


def main():
    
    # Parameters
    L = 0.03            # [m]; Length of the square path in meters
    velocity = 0.10     # [m/s]; Robot velocity in meters per second
    frequency = 50      # [Hz]; Command   

    # pose_init = [-0.095, 0.57500, 0.24130] # 2025-07
    # pose_init = [-0.638, -0.01850, 0.08000] # center -> Channel1
    # pose_init = [-0.56200, 0.03090, 0.06710] # 2026-01
    # pose_init = [-0.56200, 0.03090, 0.06555] # 2026-01-19 Sensor 2D-25
    pose_init = [-0.56200, 0.03090, 0.06560] # 2026-02-11 Sensor 2D-29
    # pose_init = [-0.56200, 0.03090, 0.08000] # Safety mode

    parser = argparse.ArgumentParser(description="Plot SVG paths.")
    parser.add_argument('--slide', type=str, default=None,
                        help='Choose slide folder to plot.')
    args = parser.parse_args()
    slide_folder = "./slide-" + args.slide + "/"

    match args.slide:
        
        case "lasa" | "digit":
            ver_slide = SLIDE_MAP.get(args.slide)[0]
            n_svg = SLIDE_MAP.get(args.slide)[1]
            svg_file = f"{args.slide}_{ver_slide}" # digit_v1

            svg_list = [f"{svg_file}-{i:02d}" for i in range(1, n_svg + 1)]  # lasa_v1-01 ... 
            print(f'Number of Available Shapes: {len(svg_list)}')

            # Shape Path Generation
            for svg in svg_list:
                svg_file = slide_folder + "path_" + svg + ".svg"
                out = extract_path_coordinates(svg_file, L, velocity, frequency)
                path = PathGenerator(out, x=pose_init[0], y=pose_init[1], z=pose_init[2], v=velocity, hz=frequency)
                path.save(slide_folder + f"path_{svg}.csv") # e.g., path_square.csv
        
        case "shape":
            shape_list = SHAPE_LIST
            print(f'Number of Available Shapes: {len(shape_list)}')

            # Shape Path Generation
            for shape in shape_list:
                if shape == 'circle':
                    out = generate_circle_path(L=L, hz=frequency, velocity=velocity, direction='CW')
                elif shape == 'circleCCW':
                    out = generate_circle_path(L=L, hz=frequency, velocity=velocity, direction='CCW')
                else:
                    out = generate_path(L=L, hz=frequency, velocity=velocity, shape=shape)
                path = PathGenerator(out, x=pose_init[0], y=pose_init[1], z=pose_init[2], v=velocity, hz=frequency)
                path.save(slide_folder + f"path_{shape}.csv") # e.g., path_square.csv

        case None:
            print("Please provide a slide name using --slide argument.")
            return
        case _:
            print(f"Slide '{args.slide}' not recognized.")
            return

if __name__ == "__main__":
	main()