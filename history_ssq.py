import pandas as pd
import numpy as np
from collections import Counter

# ----------------------
# 1. 读取历史数据
# ----------------------
df = pd.read_csv("./data/ssq/data.csv")
df = df.sort_values("期数", ascending=True).reset_index(drop=True)

red_cols = ["红球_1", "红球_2", "红球_3", "红球_4", "红球_5", "红球_6"]
blue_col = "蓝球"

all_red = df[red_cols].values.flatten().astype(int)
all_blue = df[blue_col].values.astype(int)

# ----------------------
# 2. 计算红球冷热号
# ----------------------
red_counter = Counter(all_red)
hot_red = [num for num, cnt in red_counter.most_common(12)]
cold_red = [num for num, cnt in red_counter.most_common()[-12:]]

# ----------------------
# 3. 计算遗漏值
# ----------------------
def get_missing_numbers(ball_list, total_range, top_n=15):
    last_appear = {}
    for idx, num in enumerate(ball_list):
        last_appear[num] = idx
    missing = {}
    for num in total_range:
        missing[num] = len(ball_list) - last_appear.get(num, 0)
    sorted_missing = sorted(missing.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in sorted_missing[:top_n]]

missing_red = get_missing_numbers(all_red, range(1, 34))
missing_blue = get_missing_numbers(all_blue, range(1, 17), top_n=8)

# ----------------------
# 4. 位置规律
# ----------------------
pos_ranges = []
for i, col in enumerate(red_cols):
    nums = df[col].astype(int).values
    low = int(np.percentile(nums, 15))
    high = int(np.percentile(nums, 85))
    pos_ranges.append((low, high))

# ----------------------
# 5. 选号策略（修复类型问题）
# ----------------------
def generate_recommended_red():
    selected = set()

    selected.update(np.random.choice(hot_red, size=2, replace=False))
    selected.update(np.random.choice(cold_red, size=2, replace=False))
    selected.update(np.random.choice(missing_red, size=2, replace=False))

    final = []
    for low, high in pos_ranges:
        candidates = [n for n in selected if low <= n <= high]
        if candidates:
            pick = int(np.random.choice(candidates))  # 强制转 int
            final.append(pick)
            selected.remove(pick)
        else:
            pick = int(np.random.randint(low, high+1))
            final.append(pick)

    final = sorted(list(set(final)))
    while len(final) < 6:
        final.append(int(np.random.randint(1, 34)))
        final = sorted(list(set(final)))
    return sorted(final[:6])

def generate_recommended_blue():
    blue_pool = list(set(missing_blue[:5] + [all_blue[-1], all_blue[-2]]))
    return int(np.random.choice(blue_pool))  # 强制转 int

# ----------------------
# 6. 输出
# ----------------------
print("="*60)
print("NEXT DRAW PREDICTION (Based on History Data)")
print("="*60)

pred_red = generate_recommended_red()
pred_blue = generate_recommended_blue()

print(f"Predicted Red Balls: {pred_red}")
print(f"Predicted Blue Ball: [ {pred_blue} ]")

print("\nStrategy Logic:")
print("- Hot numbers (high frequency)")
print("- Cold numbers (long missing)")
print("- Position range analysis")
print("- No repeated numbers, sorted")
print("="*60)