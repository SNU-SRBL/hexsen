import numpy as np
import pandas as pd
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf


TRAIN_FILES = ['../data/data_v1_total.csv', '../data/data_v2_total.csv']
TEST_FILES = ['../data/data_v1_square.csv', '../data/data_v1_triangle.csv']

def load_dataset_at(index, time_step=50, normalize_timeseries=False, verbose=True) -> (np.array, np.array):
    if verbose: print("Loading dataset : ", TRAIN_FILES[index])

    dataset_path = TRAIN_FILES[index]

    if os.path.exists(dataset_path):
        dataset = pd.read_csv(dataset_path)
    elif os.path.exists(dataset_path[1:]):
        dataset = pd.read_csv(dataset_path[1:])
    else:
        raise FileNotFoundError('File %s not found!' % (TRAIN_FILES[index]))

    is_timeseries = True

    print('dataset shape is : ', dataset.shape)

    # Divide into sensor_data and vel_data
    sensor_data = dataset.iloc[:, :4].values  # Columns 0 to 3
    vel_data = dataset.iloc[:, 4:].values    # Columns 4 to 5

    jump = 20  # Jump size between windows
    num_samples = (len(sensor_data) - time_step) // jump + 1

    X_data = []
    y_data = []

    # Create windows with a jump
    for i in range(0, len(sensor_data) - time_step + 1, jump):
        X_window = sensor_data[i:i + time_step].T  # Transpose to shape (4, 50)
        y_window = vel_data[i:i + time_step].sum(axis=0)
        
        X_data.append(X_window)
        y_data.append(y_window)

    X_data = np.array(X_data)  # Shape: (num_samples, 4, 50)
    y_data = np.array(y_data)  # Shape: (num_samples, 2)

    print('X_data shape: ', X_data.shape, ' y_data shape: ', y_data.shape)

    X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.3, random_state=42)

    # Standardize the data
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    # scale the values
    if is_timeseries:
        # Flatten X_train for scaling (StandardScaler works on 2D arrays)
        X_train_flat = X_train.reshape(-1, X_train.shape[1])
        X_test_flat = X_test.reshape(-1, X_test.shape[1])

        X_train_scaled = scaler_X.fit_transform(X_train_flat).reshape(X_train.shape)
        X_test_scaled = scaler_X.transform(X_test_flat).reshape(X_test.shape)

        if normalize_timeseries:
            y_train_scaled = scaler_y.fit_transform(y_train)
            y_test_scaled = scaler_y.transform(y_test)
        else:
            y_train_scaled = y_train
            y_test_scaled = y_test

    if verbose: print("Finished processing train dataset..")

    if verbose:
        print("Finished loading test dataset..")
        print()
        print("Number of train samples : ", X_train.shape[0], "Number of test samples : ", X_test.shape[0])
        print("Shape of y_train : ", y_train.shape, " Shape of y_test : ", y_test.shape)
        print("Sequence length : ", X_train.shape[-1])

    return X_train_scaled, y_train_scaled, X_test_scaled, y_test_scaled, is_timeseries, scaler_X, scaler_y


def load_test_dataset_at(index, time_step=50, normalize_timeseries=False, verbose=True) -> (np.array, np.array):
    
    _, _, _, _, _, scaler_X, scaler_y = load_dataset_at(0,
                                                        normalize_timeseries=normalize_timeseries)
    
    if verbose: print("Loading dataset : ", TEST_FILES[index])

    dataset_path = TEST_FILES[index]

    if os.path.exists(dataset_path):
        dataset = pd.read_csv(dataset_path)
    elif os.path.exists(dataset_path[1:]):
        dataset = pd.read_csv(dataset_path[1:])
    else:
        raise FileNotFoundError('File %s not found!' % (TEST_FILES[index]))

    is_timeseries = True

    print('dataset shape is : ', dataset.shape)

    # Divide into sensor_data and vel_data
    sensor_data = dataset.iloc[:, :4].values  # Columns 0 to 3
    vel_data = dataset.iloc[:, 4:].values    # Columns 4 to 5

    jump = time_step  # Jump size between windows
    num_samples = (len(sensor_data) - time_step) // jump + 1

    X_data = []
    y_data = []

    # Create windows with a jump
    for i in range(0, len(sensor_data) - time_step + 1, jump):
        X_window = sensor_data[i:i + time_step].T  # Transpose to shape (4, 50)
        y_window = vel_data[i:i + time_step].sum(axis=0)
        
        X_data.append(X_window)
        y_data.append(y_window)

    X_data = np.array(X_data)  # Shape: (num_samples, 4, 50)
    y_data = np.array(y_data)  # Shape: (num_samples, 2)

    print('X_data shape: ', X_data.shape, ' y_data shape: ', y_data.shape)
    X_test = X_data
    y_test = y_data

    # scale the values
    if is_timeseries:
        # Flatten X_train for scaling (StandardScaler works on 2D arrays)
        X_test_flat = X_test.reshape(-1, X_test.shape[1])
        X_test_scaled = scaler_X.transform(X_test_flat).reshape(X_test.shape)

        if normalize_timeseries:
            y_test_scaled = scaler_y.transform(y_test)
        else:
            y_test_scaled = y_test

    if verbose: print("Finished processing test dataset..")

    if verbose:
        print("Finished loading test dataset..")
        print()
        print("Number of test samples : ", X_test.shape[0])
        print("Shape of y_test : ", y_test.shape)
        print("Sequence length : ", X_test.shape[-1])

    return X_test_scaled, y_test_scaled, is_timeseries, scaler_X, scaler_y


def calculate_dataset_metrics(X_train):
    max_nb_variables = X_train.shape[1]
    max_timesteps = X_train.shape[-1]

    return max_timesteps, max_nb_variables



if __name__ == '__main__':
    # load_dataset_at(index=0, time_step=50, normalize_timeseries=True, verbose=True)
    load_test_dataset_at(index=0, time_step=50, normalize_timeseries=False, verbose=True)