import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader


class SequenceDataset(Dataset):
    def __init__(self, data, seq_len=7, output_dim=1):
        """
        构建时序数据集：从连续数据中截取长度为seq_len的序列作为输入，下一个值作为目标
        :param data: 原始连续数据（1D数组）
        :param seq_len: 输入序列长度（固定为7）
        :param output_dim: 预测目标维度
        """
        self.seq_len = seq_len
        self.output_dim = output_dim
        self.X, self.y = self._create_sequences(data)
    
    def _create_sequences(self, data):
        X = []
        y = []
        # 遍历数据，截取每个长度为7的序列，对应下一个值为目标
        for i in range(len(data) - self.seq_len - self.output_dim + 1):
            seq = data[i:i+self.seq_len].reshape(-1, 1)  # (7, 1)：seq_len=7，input_dim=1
            target = data[i+self.seq_len:i+self.seq_len+self.output_dim]  # (output_dim,)
            X.append(seq)
            y.append(target)
        return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# 模拟原始数据：正弦波（带少量噪声，模拟真实时序数据）
np.random.seed(42)
time_steps = np.linspace(0, 100, 1000)  # 1000个时间步
data = np.sin(time_steps) + 0.1 * np.random.randn(len(time_steps))  # 正弦波+噪声

# 构建数据集和数据加载器
dataset = SequenceDataset(data, seq_len=7, output_dim=1)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)


class RNNPredictor(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=64, num_layers=2, output_dim=1, dropout=0.1):
        """
        RNN 时序预测模型
        :param input_dim: 每个时刻的输入特征维度（如每个位置是1个数值，则为1）
        :param hidden_dim: RNN 隐藏层维度（可调整）
        :param num_layers: RNN 层数（可调整）
        :param output_dim: 预测目标维度（如预测下一个7维序列，则为7）
        :param dropout:  dropout 概率（防止过拟合）
        """
        super(RNNPredictor, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # RNN 层（batch_first=True 表示输入格式为 (batch_size, seq_len, input_dim)）
        self.rnn = nn.RNN(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0  # 单层RNN不启用dropout
        )
        
        # 全连接层：将 RNN 输出映射到目标维度
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim)
        )
    
    def forward(self, x):
        """
        前向传播
        :param x: 输入数据，shape=(batch_size, seq_len=7, input_dim)
        :return: 预测结果，shape=(batch_size, output_dim)
        """
        # 1. RNN 层计算：output shape=(batch_size, seq_len, hidden_dim)
        #    hidden shape=(num_layers, batch_size, hidden_dim)（最后一层隐藏状态）
        output, hidden = self.rnn(x)
        
        # 2. 取 RNN 最后一个时刻的输出（时序预测核心：用历史序列的最终状态预测下一个值）
        last_hidden = output[:, -1, :]  # shape=(batch_size, hidden_dim)
        
        # 3. 全连接层映射到目标维度
        pred = self.fc(last_hidden)  # shape=(batch_size, output_dim)
        return pred
    

# 设备配置（CPU/GPU）
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 初始化模型、损失函数、优化器
model = RNNPredictor(
    input_dim=1,    # 每个时刻输入1个特征
    hidden_dim=64,  # 隐藏层维度（可调整为32/128）
    num_layers=2,   # RNN层数（可调整为1/3）
    output_dim=1,   # 预测1个目标值
    dropout=0.1
).to(device)

criterion = nn.MSELoss()  # 回归任务用均方误差损失
optimizer = optim.Adam(model.parameters(), lr=1e-3)  # Adam优化器

# 训练参数
epochs = 50
model.train()  # 训练模式

for epoch in range(epochs):
    total_loss = 0.0
    for batch_X, batch_y in dataloader:
        # 数据移到设备上
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        
        # 前向传播
        pred = model(batch_X)
        loss = criterion(pred, batch_y)
        
        # 反向传播+参数更新
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * batch_X.size(0)
    
    # 计算epoch平均损失
    avg_loss = total_loss / len(dataset)
    if (epoch + 1) % 10 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Average Loss: {avg_loss:.6f}")

print("训练完成！")


def predict_next(model, last_sequence, device):
    """
    用训练好的模型预测下一个数据
    :param model: 训练好的RNN模型
    :param last_sequence: 最后一个已知序列（shape=(seq_len=7, input_dim=1)）
    :param device: 设备（CPU/GPU）
    :return: 预测的下一个值（shape=(output_dim,)）
    """
    model.eval()  # 评估模式（禁用dropout）
    with torch.no_grad():  # 禁用梯度计算
        # 调整输入格式：(batch_size=1, seq_len=7, input_dim=1)
        input_seq = last_sequence.unsqueeze(0).to(device)
        pred = model(input_seq)
        return pred.squeeze().cpu().numpy()  # 转换为numpy数组

# 测试预测：取数据集中最后一个序列作为输入
last_seq = dataset.X[-1]  # shape=(7, 1)（已知的最后7个数据）
true_next = dataset.y[-1].cpu().numpy()  # 真实的下一个值
pred_next = predict_next(model, last_seq, device)  # 模型预测的下一个值

print(f"已知最后7个序列：{last_seq.squeeze().numpy()}")
print(f"真实下一个值：{true_next[0]:.4f}")
print(f"模型预测下一个值：{pred_next[0]:.4f}")