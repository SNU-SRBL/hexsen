import torch
from torch import nn
from torch.utils.data import DataLoader
import numpy as np
import os
import tqdm
import joblib
from dataclasses import dataclass
import tyro

from model.mlstm_fcn import MLSTM_FCN
from utils.generic_utils import MyDataset, load_dataset_at, calculate_dataset_metrics
from utils.json_logger import JsonLogger

@dataclass
class Args:
    seed: int = 42
    epoch: int = 1000
    learning_rate: float = 1e-3
    batch_size: int = 128
    output_dir: str = 'output'
    normalize_timeseries: bool = True
    gpu_idx: int = 0

class BaseWorkspace():
    def __init__(self, cfg: Args):
        self.total_epoch = cfg.epoch
        self.batch_size = cfg.batch_size
        self.output_dir = cfg.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        seed = 42
        torch.manual_seed(seed)
        np.random.seed(seed)
        # random.seed(seed)

        # Load Data
        dataset_id = 0
        dataset_packet = load_dataset_at(dataset_id, fold_index=None, 
                                         normalize_timeseries=cfg.normalize_timeseries, verbose=True)
        X_train, y_train, X_test, y_test, is_timeseries, scaler_X, scaler_y = dataset_packet
        self.scaler_y = scaler_y
        joblib.dump(scaler_X, os.path.join(self.output_dir, 'scaler_X.pkl'))
        joblib.dump(self.scaler_y, os.path.join(self.output_dir, 'scaler_y.pkl'))
        max_timesteps, max_nb_variables = calculate_dataset_metrics(X_train)
        num_classes = y_train.shape[1]

        training_data = MyDataset(X_train, y_train)
        self.train_loader = DataLoader(training_data, batch_size=self.batch_size, shuffle=True)

        test_data = MyDataset(X_test, y_test)
        self.test_loader = DataLoader(test_data, batch_size=self.batch_size, shuffle=False)

        if is_timeseries:
            factor = 1. / np.cbrt(2)
        else:
            factor = 1. / np.sqrt(2)

        self.model = MLSTM_FCN(input_feature=max_nb_variables, 
                               timesteps=max_timesteps, 
                               num_classes=num_classes)

        self.loss_fn = nn.MSELoss() # nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=cfg.learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=factor, patience=100,
            cooldown=0, min_lr=1e-4
        )

        # Load Model
        self.device = torch.device(f'cuda:{cfg.gpu_idx}' if torch.cuda.is_available() else 'cpu')
        print(f"Using {self.device} device")
        self.model.to(self.device)

        self.global_step = 0
        self.epoch = 0

        self.best_val_rmse = float('inf')  # Track best RMSE
    
    def save_checkpoint(self, rmse, is_best=False):
        if not is_best:
            model_path = f"model_ep_{self.epoch+1}.pth"
            torch.save({
                'epoch': self.epoch,
                'val_rmse': rmse,
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict()
            }, os.path.join(self.output_dir, model_path))
        else:
            best_model_path = os.path.join(self.output_dir, f"model_best.pth")
            torch.save({
                'epoch': self.epoch,
                'val_rmse': rmse,
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict()
            }, best_model_path)   

    def validate(self):
        self.model.eval()
        total_loss = 0.0
        preds, targets = [], []

        with torch.no_grad():
            for X, y in self.test_loader:
                X, y = X.to(self.device), y.to(self.device)

                pred = self.model(X)                      # (N, 2)
                loss = self.loss_fn(pred, y)
                total_loss += loss.item() * X.size(0)

                preds.append(pred.detach().cpu().numpy())
                targets.append(y.detach().cpu().numpy())

        avg_loss = total_loss / len(self.test_loader.dataset)

        # Inverse scale for evaluation
        preds = np.vstack(preds)
        targets = np.vstack(targets)
        preds_real = self.scaler_y.inverse_transform(preds)
        targets_real = self.scaler_y.inverse_transform(targets)

        rmse = np.sqrt(np.mean((preds_real - targets_real) ** 2))

        print(f"Validation - Avg Loss: {avg_loss:.6f}, RMSE (real): {rmse:.6f}")
        return avg_loss, rmse
    
    def run(self):

        # Train Loop
        log_path = os.path.join(self.output_dir, 'train_log.json.txt')
        with JsonLogger(log_path) as json_logger:
            for local_epoch_idx in range(self.total_epoch):
                self.model.train()
                train_losses = []

                with tqdm.tqdm(self.train_loader, desc=f"Training epoch {self.epoch+1}") as tepoch:
                    for batch_idx, (X, y) in enumerate(tepoch):
                        X, y = X.to(self.device), y.to(self.device)

                        # Compute prediction error
                        pred = self.model(X)
                        loss = self.loss_fn(pred, y)

                        # Backpropagation
                        loss.backward()
                        self.optimizer.step()
                        self.optimizer.zero_grad()

                        # Logging
                        train_losses.append(loss.item())
                        tepoch.set_postfix(loss=loss.item())
                        
                        # is_last_batch = (batch_idx == (len(train_loader)-1))
                        # if not is_last_batch:
                            # pass
                        self.global_step += 1

                avg_train_loss = np.mean(train_losses)

                # Evalutation
                val_loss, val_rmse = self.validate()

                # Scheduler step
                old_lr = self.optimizer.param_groups[0]['lr']
                self.scheduler.step(val_loss)
                new_lr = self.optimizer.param_groups[0]['lr']
                if new_lr < old_lr:
                    print(f"Learning rate reduced: {old_lr:.6f} → {new_lr:.6f}")

                # Log results
                log_dict = {
                    'epoch': self.epoch + 1,
                    'train_loss': avg_train_loss,
                    'val_loss': val_loss,
                    'val_rmse': val_rmse,
                    'lr': new_lr
                }
                json_logger.log(log_dict)

                # Save Chackpoint (every 100 epoch)
                if (self.epoch + 1) % 100 == 0:
                    self.save_checkpoint(val_rmse, is_best=False)

                # if ((self.epoch + 1) > 100) and (val_rmse < self.best_val_rmse):
                #     self.best_val_rmse = val_rmse
                #     self.save_checkpoint(val_rmse, is_best=True)
                
                # Finsihed one epoch
                print(f"Epoch {self.epoch+1}/{self.total_epoch} - Avg Loss: {avg_train_loss:.4f}")
                self.epoch += 1

if __name__ == "__main__":
    
    cfg = tyro.cli(Args)
    workspace = BaseWorkspace(cfg)
    workspace.run()

