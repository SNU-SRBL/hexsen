import torch
from torch import nn
# import torch.nn.functional as F

class MLSTM_FCN(nn.Module):
    def __init__(self, input_feature=4, timesteps=50, num_classes=2, r=16):
        super().__init__()

        self.r = r
        self.in_channels = input_feature # M
        self.hidden_size = 8

        self.relu = nn.ReLU()

        # LSTM branch
        self.lstm = nn.LSTM(input_size=timesteps, hidden_size=self.hidden_size, num_layers=1, batch_first=True)
        self.dropout = nn.Dropout(p=0.8)

        # Conv branch
        """ Conv1d -> reset_parameters: kaiming_uniform """
        self.conv1 = nn.Conv1d(self.in_channels, 128, kernel_size=8, padding='same') # padding same
        self.bn1 = nn.BatchNorm1d(128)

        self.conv2 = nn.Conv1d(128, 256, kernel_size=5, padding=2) # padding same
        self.bn2 = nn.BatchNorm1d(256)

        self.conv3 = nn.Conv1d(256, 128, kernel_size=3, padding=1) # padding same
        self.bn3 = nn.BatchNorm1d(128)

        # Squeeze and Excitation blocks
        """ Linear -> reset_parameters: kaiming_normal """
        self.se1_sq = nn.Linear(128, 128//self.r, bias=False) # (N, 1, 8) # he_normal
        self.se1_ex = nn.Linear(128//self.r, 128, bias=False) # (N, 1, 128)

        self.se2_sq = nn.Linear(256, 256//self.r, bias=False) # (N, 1, 16) # he_normal
        self.se2_ex = nn.Linear(256//self.r, 256, bias=False) # (N, 1, 256)

        # Final classification
        self.classifier = nn.Linear(self.hidden_size + 128, num_classes)

    def se_block(self, y, sqeeze, excite):
        # y: (N, Q, C)
        se = y.mean(dim=1, keepdim=True) # (N, 1, C)
        se = sqeeze(se)
        se = self.relu(se)
        se = excite(se)
        se = torch.sigmoid(se)
        return y * se # braodcasted multiply: (N, Q, C) * (N, 1, C)

    def forward(self, x):
        # x: (N, M, Q)

        # LSTM branch
        lstm_out, _ = self.lstm(x) # (N, M, 8)
        lstm_out = lstm_out[:, -1, :] # (N, 8)
        lstm_out = self.dropout(lstm_out)

        # Conv branch
        y = self.conv1(x) # (N, 128, Q)
        y = self.bn1(y)
        y = self.relu(y)
        y = y.permute(0, 2, 1) # (N, Q, 128)
        y = self.se_block(y, self.se1_sq, self.se1_ex) # (N, Q, 128)

        # Conv Layer 2
        y = y.permute(0, 2, 1) # (N, 128, Q)
        y = self.conv2(y) # (N, 256, Q)
        y = self.bn2(y)
        y = self.relu(y)
        y = y.permute(0, 2, 1) # (N, Q, 256)
        y = self.se_block(y, self.se2_sq, self.se2_ex) # (N, Q, 256)

        # Conv Layer 3
        y = y.permute(0, 2, 1) # (N, 256, Q)
        y = self.conv3(y) # (N, 128, Q)
        y = self.bn3(y)
        y = self.relu(y)
        y = y.permute(0, 2, 1) # (N, Q, 128)

        y = y.mean(dim=1) # Global Average Pooling 1D (N, 128)
        out = torch.cat([lstm_out, y], dim=1) # (N, 136)
        out = self.classifier(out)
        # Don't use Softmax, Use MSELoss, L1Loss, or SmoothL1Loss

        return out


if __name__ == "__main__":
    
    model = MLSTM_FCN()
    input = torch.rand(360, 4, 50)
    output = model(input)
    print(model)
    print(output.shape)
    assert output.shape == (360, 2), "Output shape is incorrect!"
