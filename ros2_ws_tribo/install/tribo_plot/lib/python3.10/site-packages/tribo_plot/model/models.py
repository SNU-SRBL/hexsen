import torch
import torch.nn as nn

class TouchNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.lstm = nn.LSTM(input_size=4000, hidden_size=20, num_layers=2)
        self.fc = nn.Linear(20, 2)

    def forward(self, x):
        x = self.flatten(x)
        x = x.unsqueeze(0)            # (1, 1, 800)
        x, (h_n, c_n) = self.lstm(x)  # x: (1, 1, 20)
        x = x.squeeze(0)              # (1, 20)
        x = self.fc(x)                # (1,2)
        return x


class SlideNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.lstm = nn.LSTM(input_size=200, hidden_size=20, num_layers=2)
        self.fc = nn.Linear(20, 2)

    def forward(self, x):
        x = self.flatten(x)
        x = x.unsqueeze(0)            # (1, 1, 200)
        x, (h_n, c_n) = self.lstm(x)  # x: (1, 1, 20)
        x = x.squeeze(0)              # (1, 20)
        x = self.fc(x)                # (1,2)
        return x


# numpy (2,) not (2,1)
if __name__ == "__main__":
    print('hi')
    
