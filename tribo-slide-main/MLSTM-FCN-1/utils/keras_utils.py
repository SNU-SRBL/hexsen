import numpy as np
import matplotlib.pyplot as plt

import warnings
warnings.simplefilter('ignore', category=DeprecationWarning)

from keras.models import Model
from keras.layers import Permute
from keras.optimizers import Adam
from keras.utils import to_categorical
from keras.preprocessing.sequence import pad_sequences
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, Callback
from keras import backend as K

from utils.generic_utils import load_dataset_at, load_test_dataset_at, calculate_dataset_metrics


def train_model(model:Model, dataset_id, dataset_prefix, dataset_fold_id=None, epochs=50, batch_size=128, val_subset=None,
                normalize_timeseries=False, learning_rate=1e-3, monitor='loss', optimization_mode='auto', compile_model=True):
    X_train, y_train, X_test, y_test, is_timeseries, scaler_X, scaler_y = load_dataset_at(dataset_id,
                                                                            normalize_timeseries=normalize_timeseries)
    max_timesteps, max_nb_variables = calculate_dataset_metrics(X_train)

    if is_timeseries:
        factor = 1. / np.cbrt(2)
    else:
        factor = 1. / np.sqrt(2)

    if dataset_fold_id is None:
        weight_fn = f"./weights/{dataset_prefix}_weights.h5"
    else:
        weight_fn = f"./weights/{dataset_prefix}_fold_{dataset_fold_id}_weights.h5"

    model_checkpoint = ModelCheckpoint(weight_fn, verbose=1, mode=optimization_mode,
                                       monitor=monitor, save_best_only=True, save_weights_only=True)
    reduce_lr = ReduceLROnPlateau(monitor=monitor, patience=100, mode=optimization_mode,
                                  factor=factor, cooldown=0, min_lr=1e-4, verbose=2)
    dynamic_plot = PlotTrainingHistory(update_frequency=10)  # Update every 10 epochs
    callback_list = [model_checkpoint, reduce_lr, dynamic_plot]

    optm = Adam(lr=learning_rate)

    if compile_model:
        model.compile(optimizer=optm, loss='mse', metrics=['mae'])

    if val_subset is not None:
        X_test = X_test[:val_subset]
        y_test = y_test[:val_subset]

    model.fit(X_train, y_train, batch_size=batch_size, epochs=epochs, callbacks=callback_list,
              verbose=2, validation_data=(X_test, y_test))



def evaluate_model(model:Model, dataset_id, dataset_prefix, dataset_fold_id=None, batch_size=128, test_data_subset=None,
                    normalize_timeseries=False):
    X_test, y_test, is_timeseries, scaler_X, scaler_y = load_test_dataset_at(dataset_id, 
                                                                    normalize_timeseries=normalize_timeseries, verbose=True)

    optm = Adam(lr=1e-3)
    model.compile(optimizer=optm, loss='mse', metrics=['mae'])

    if dataset_fold_id is None:
        weight_fn = "./weights/%s_weights.h5" % dataset_prefix
    else:
        weight_fn = "./weights/%s_fold_%d_weights.h5" % (dataset_prefix, dataset_fold_id)
    model.load_weights(weight_fn)

    if test_data_subset is not None:
        X_test = X_test[:test_data_subset]
        y_test = y_test[:test_data_subset]

    print("\nEvaluating : ")
    loss, mae = model.evaluate(X_test, y_test, batch_size=batch_size)
    print()
    print("Final Loss : " , loss, "Final MAE : ", mae)

    # Make predictions
    predictions = model.predict(X_test, batch_size=batch_size)

    # If normalize_timeseries is True, inverse-transform y_test and predictions
    if normalize_timeseries:
        y_test = scaler_y.inverse_transform(y_test)
        predictions = scaler_y.inverse_transform(predictions)

    # Calculate cumulative sum (pose values)
    y_pose = np.cumsum(y_test, axis=0)  # Cumulative sum of y_test row-wise
    pre_pose = np.cumsum(predictions, axis=0)  # Cumulative sum of predictions row-wise

     # Plot the cumulative results
    plt.figure(figsize=(8, 6))
    plt.plot(y_pose[:, 0], y_pose[:, 1], 'b-', label='Ground Truth (Pose)')  # Blue line for y_pose
    plt.plot(pre_pose[:, 0], pre_pose[:, 1], 'r--', label='Predictions (Pose)')  # Red dashed line for pre_pose
    plt.title('Sliding Pose Estimation: Ground Truth vs Predictions')
    plt.xlabel('Pose X')
    plt.ylabel('Pose Y')
    plt.xlim()
    plt.ylim()
    plt.legend()
    plt.grid(True)
    plt.show()

    return mae, loss


class PlotTrainingHistory(Callback):
    def __init__(self, update_frequency=10):
        super().__init__()
        self.update_frequency = update_frequency
        self.history = {'loss': [], 'val_loss': [], 'mae': [], 'val_mae': []}
        self.fig, self.ax = plt.subplots(1, 2, figsize=(12, 5))  # Create subplots for loss and mae
        plt.ion()  # Turn on interactive mode

    def on_epoch_end(self, epoch, logs=None):
        # Append current logs to history
        for key in logs:
            if key in self.history:
                self.history[key].append(logs[key])

        # Update plot every `update_frequency` epochs
        if (epoch + 1) % self.update_frequency == 0 or (epoch + 1) == self.params['epochs']:
            self._update_plot(epoch)

    def _update_plot(self, epoch):
        # Clear the previous plots
        self.ax[0].clear()
        self.ax[1].clear()

        # Plot loss
        self.ax[0].plot(self.history['loss'], label='Training Loss')
        self.ax[0].plot(self.history['val_loss'], label='Validation Loss')
        self.ax[0].set_title('Loss')
        self.ax[0].set_xlabel('Epoch')
        self.ax[0].set_ylabel('Loss')
        self.ax[0].legend()
        self.ax[0].grid(True)

        # Plot MAE
        self.ax[1].plot(self.history['mae'], label='Training MAE')
        self.ax[1].plot(self.history['val_mae'], label='Validation MAE')
        self.ax[1].set_title('Mean Absolute Error (MAE)')
        self.ax[1].set_xlabel('Epoch')
        self.ax[1].set_ylabel('MAE')
        self.ax[1].legend()
        self.ax[1].grid(True)

        # Show updated plots
        plt.suptitle(f"Epoch {epoch + 1}")
        plt.draw()
        plt.pause(0.1)

    def on_train_end(self, logs=None):
        # Ensure plots stay open after training ends
        plt.ioff()
        plt.show()