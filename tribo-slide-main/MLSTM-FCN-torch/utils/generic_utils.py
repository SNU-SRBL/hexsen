import numpy as np
import os
from sklearn.preprocessing import StandardScaler
import torch
from torch.utils.data import Dataset
# import matplotlib as mpl
# import matplotlib.pylab as plt

# mpl.style.use('seaborn-paper')

TRAIN_FILES = '../data/tribo_260112/'
TEST_FILES = '../data/tribo_260112/'

class MyDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32) # Regression

    def __len__(self):
        return len(self.x)
    
    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]
    

def load_dataset_at(index, fold_index=None, normalize_timeseries=False, verbose=True):
    if verbose: print("Loading train / test dataset : ", TRAIN_FILES, TEST_FILES)

    x_train_path = TRAIN_FILES + "X_train.npy"
    y_train_path = TRAIN_FILES + "y_train.npy"
    x_test_path = TEST_FILES + "X_test.npy"
    y_test_path = TEST_FILES + "y_test.npy"

    if os.path.exists(x_train_path):
        X_train = np.load(x_train_path)
        y_train = np.load(y_train_path)
        X_test = np.load(x_test_path)
        y_test = np.load(y_test_path)
    elif os.path.exists(x_train_path[1:]):
        X_train = np.load(x_train_path[1:])
        y_train = np.load(y_train_path[1:])
        X_test = np.load(x_test_path[1:])
        y_test = np.load(y_test_path[1:])
    else:
        raise FileNotFoundError('File %s not found!' % (TRAIN_FILES))

    is_timeseries = True

    # Scale the values
    if is_timeseries:
        
        X_train_trans = X_train.transpose(0, 2, 1)  # (N, 50, 4)
        X_test_trans = X_test.transpose(0, 2, 1) # (N, T, C)

        # Flatten to (N*T, C) for StandardScaler
        X_train_flat = X_train_trans.reshape(-1, X_train_trans.shape[2])
        X_test_flat = X_test_trans.reshape(-1, X_test_trans.shape[2])

        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train_flat).reshape(X_train_trans.shape)
        X_test_scaled = scaler_X.transform(X_test_flat).reshape(X_test_trans.shape)

        # Transpose back to (N, C, T)
        X_train_scaled = X_train_scaled.transpose(0, 2, 1)
        X_test_scaled = X_test_scaled.transpose(0, 2, 1)

        if normalize_timeseries:
            scaler_y = StandardScaler()
            y_train_scaled = scaler_y.fit_transform(y_train)
            y_test_scaled = scaler_y.transform(y_test)
        else:
            y_train_scaled = y_train
            y_test_scaled = y_test
            
    if verbose:
        print("Finished processing train/test dataset..")
        print()
        print("Train scaled dataset : ", X_train_scaled.shape, y_train_scaled.shape) 
        print("Test scaled dataset : ", X_test_scaled.shape, y_test_scaled.shape)
        print("Number of train samples : ", X_train_scaled.shape[0])
        print("Number of test samples : ", X_test_scaled.shape[0])
        print("Sequence length : ", X_train_scaled.shape[-1])
 
    return (X_train_scaled, y_train_scaled, X_test_scaled, y_test_scaled, is_timeseries, scaler_X, scaler_y)


def calculate_dataset_metrics(X_train):
    max_nb_variables = X_train.shape[1]
    max_timesteps = X_train.shape[-1]

    return max_timesteps, max_nb_variables


if __name__ == "__main__":
    
    load_dataset_at(0, normalize_timeseries=True)