import matplotlib.pyplot as plt
import pandas as pd

def main(id=30):
        
    # Read JSON log file into pandas DataFrame
    # data = pd.read_json(f'output/train_log_{id}.json.txt', lines=True)
    data = pd.read_json(f'output/train_log.json.txt', lines=True)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot train_loss and val_loss
    ax1.plot(data['epoch'], data['train_loss'], label='Train Loss', linewidth=2)
    ax1.plot(data['epoch'], data['val_loss'], label='Validation Loss', linewidth=2)
    ax1.set_ylabel('Loss')
    ax1.set_title('Train and Validation Loss')
    ax1.legend()
    ax1.grid(True)

    # Plot val_rmse
    ax2.plot(data['epoch'], data['val_rmse'], label='Validation RMSE', color='green', linewidth=2)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Validation RMSE')
    ax2.set_title('Validation RMSE')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("output/loss_rmse_plot.png")
    # plt.show()


if __name__ == "__main__":
    main(id=30)