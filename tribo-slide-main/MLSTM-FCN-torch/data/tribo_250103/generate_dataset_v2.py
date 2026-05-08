import numpy as np
np.random.seed(1000)

#train and test size are 360 and 585
from scipy.io import loadmat

def generate_dataset(win_size=50, n_test=5): # jump

    libras_dataset = r""
    version = "v6"

    ''' Load train set '''
    data_shape_dict = loadmat(libras_dataset + f"datacell{version}_slide_shape.mat")
    # data_spline_dict = loadmat(libras_dataset + f"datacell{version}_slide_spline.mat")
    shape_rawdata = data_shape_dict['data_cell']
    # spline_rawdata = data_spline_dict['data_cell']
    print(f"shape data shape: {shape_rawdata.shape}")
    # print(f"spline data shape: {spline_rawdata.shape}")
    raw_data = shape_rawdata # raw_data = np.concatenate((shape_rawdata, spline_rawdata), axis=1)
    print(f'raw data type and size: {type(raw_data)} {raw_data.shape}')
    
    nb_cell,  nb_repeat= raw_data.shape
    n_test = n_test
    print(f"number of task: {nb_cell}, number of repeat: {nb_repeat}")

    # Find empty cell element
    for i in range(nb_cell):
        for j in range(nb_repeat):
            if raw_data[i, j].size == 0:
                print(f"cell {i}, # {j} is empty") # Find empty cell element

    
    raw_data_train = np.empty((0, 6))
    raw_data_test = np.empty((0, 6))
    raw_data_demo = np.empty((0, 6))
    """
    for i in range(nb_cell - n_test):
        raw_data_train = np.concatenate((raw_data_train, raw_data[0,i]), axis=0)

    for i in range(nb_cell - n_test, nb_cell):
        raw_data_test = np.concatenate((raw_data_test, raw_data[0,i]), axis=0)

    print(f'Raw Train data set shape: {raw_data_train.shape}')
    print(f'Raw Test data set shape: {raw_data_test.shape}')

    X_data_train = raw_data_train[:, :4]
    y_data_train = raw_data_train[:, 4:]
    X_data_test = raw_data_test[:, :4]
    y_data_test = raw_data_test[:, 4:]   

    X_train = []
    y_train = []
    X_test = []
    y_test = []

    print(f'Timestep size: {win_size}')
    jump = win_size // 3

    # Create windows with a jump for TRAIN
    for i in range(0, len(X_data_train) - win_size + 1, jump):
        X_window = np.transpose(X_data_train[i: i + win_size]) # Transpose to (4, win_size)
        y_window = np.sum(y_data_train[i: i + win_size], axis=0)

        X_train.append(X_window)
        y_train.append(y_window)

    # Create windows with a jump for TEST
    for i in range(0, len(X_data_test) - win_size + 1, jump):
        X_window = np.transpose(X_data_test[i: i + win_size]) # Transpose to (4, win_size)
        y_window = np.sum(y_data_test[i: i + win_size], axis=0)

        X_test.append(X_window)
        y_test.append(y_window)

    X_train = np.array(X_train)
    y_train = np.array(y_train)
    X_test = np.array(X_test)
    y_test = np.array(y_test)


    ''' Save the datasets '''
    # X shape (N, 4, 50) y shape (N, 2)
    print("Train dataset : ", X_train.shape, y_train.shape) 
    print("Test dataset : ", X_test.shape, y_test.shape)
    print("Train dataset metrics : ", X_train.mean(), X_train.std())
    print("Train dataset metrics (y) : ", y_train.mean(), y_train.std())
    print("Test dataset metrics : ", X_test.mean(), X_test.std())
    print("Train dataset metrics (y) : ", y_test.mean(), y_test.std())

    np.save(libras_dataset + 'X_train.npy', X_train)
    np.save(libras_dataset + 'y_train.npy', y_train)
    np.save(libras_dataset + 'X_test.npy', X_test)
    np.save(libras_dataset + 'y_test.npy', y_test)
    """

if __name__ == "__main__":
    generate_dataset(win_size=100, n_test=5)



