import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 1. 读取数据
df = pd.read_csv("./data/ssq/data.csv")
# 按期数升序排序（保证时间顺序正确）
df = df.sort_values("期数").reset_index(drop=True)

# 红球/蓝球列名
red_cols = ["红球_1", "红球_2", "红球_3", "红球_4", "红球_5", "红球_6"]
blue_col = "蓝球"

# 把所有红球数据拉平（用于冷热号统计）
all_red_balls = df[red_cols].values.flatten()
all_blue_balls = df[blue_col].values

# --------------------------
# 图1：红球冷热号频次柱状图（最核心的冷热分析）
# --------------------------
plt.figure(figsize=(16, 6))
red_counter = Counter(all_red_balls)
# 按号码1-33排序
red_nums = sorted(red_counter.keys())
red_counts = [red_counter[num] for num in red_nums]

plt.bar(red_nums, red_counts, color='#ff4444', alpha=0.8, edgecolor='black')
plt.axhline(y=np.mean(red_counts), color='blue', linestyle='--', label=f'Average Frequency: {np.mean(red_counts):.1f}')
plt.title("Red Ball Frequency Distribution (Hot/Cold Numbers)", fontsize=14)
plt.xlabel("Red Ball Number (1-33)", fontsize=12)
plt.ylabel("Total Appearances", fontsize=12)
plt.xticks(np.arange(1, 34, 1))
plt.grid(axis='y', alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# --------------------------
# 图2：蓝球冷热号频次柱状图
# --------------------------
plt.figure(figsize=(12, 5))
blue_counter = Counter(all_blue_balls)
blue_nums = sorted(blue_counter.keys())
blue_counts = [blue_counter[num] for num in blue_nums]

plt.bar(blue_nums, blue_counts, color='#0000aa', alpha=0.8, edgecolor='black')
plt.axhline(y=np.mean(blue_counts), color='red', linestyle='--', label=f'Average Frequency: {np.mean(blue_counts):.1f}')
plt.title("Blue Ball Frequency Distribution (Hot/Cold Numbers)", fontsize=14)
plt.xlabel("Blue Ball Number (1-16)", fontsize=12)
plt.ylabel("Total Appearances", fontsize=12)
plt.xticks(np.arange(1, 17, 1))
plt.grid(axis='y', alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# --------------------------
# 图3：红球6个位置的号码分布热力图（看每个位置的出号偏好）
# --------------------------
plt.figure(figsize=(14, 8))
# 构建6行（6个位置）×33列（1-33号）的频次矩阵
heatmap_data = np.zeros((6, 33))
for pos_idx, col in enumerate(red_cols):
    pos_counter = Counter(df[col])
    for num in range(1, 34):
        heatmap_data[pos_idx, num-1] = pos_counter.get(num, 0)

im = plt.imshow(heatmap_data, cmap='Reds', aspect='auto')
plt.colorbar(im, label='Appearances')
plt.title("Red Ball Position Heatmap (Row=Position 1-6, Column=Number 1-33)", fontsize=14)
plt.yticks(np.arange(6), [f"Red {i+1}" for i in range(6)], fontsize=11)
plt.xticks(np.arange(33), np.arange(1, 34), fontsize=9)
plt.xlabel("Red Ball Number", fontsize=12)
plt.ylabel("Position", fontsize=12)
plt.tight_layout()
plt.show()

# --------------------------
# 图4：近100期红球走势（时间轴压缩，只看近期趋势）
# --------------------------
# 取最近100期数据（避免线条太密）
recent_df = df.tail(100).reset_index(drop=True)
recent_issues = recent_df["期数"].values
recent_red = recent_df[red_cols].values.T
recent_blue = recent_df[blue_col].values

plt.figure(figsize=(16, 7))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
for i, red in enumerate(recent_red):
    plt.plot(recent_issues, red, label=f"Red {i+1}", color=colors[i], linewidth=2, marker='o', markersize=4)
plt.plot(recent_issues, recent_blue, label="Blue", color='navy', linewidth=3, marker='s', markersize=6)

plt.title("Recent 100 Issues: Red & Blue Ball Trend", fontsize=14)
plt.xlabel("Issue Number", fontsize=12)
plt.ylabel("Ball Number", fontsize=12)
plt.ylim(0, 35)
plt.yticks(np.arange(1, 36, 1))
plt.grid(True, alpha=0.3)
plt.legend(ncol=7, fontsize=10)
plt.tight_layout()
plt.show()