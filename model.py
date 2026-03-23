import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency, norm
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

import random
random.seed(2025)
np.random.seed(2025)
# --------------------------
# Configuration
# --------------------------
class Config:
    RED_BALL_RANGE = (1, 34)
    BLUE_BALL_RANGE = (1, 17)
    RED_BALL_COUNT = 6
    CANDIDATE_COUNT = 20  # Number of candidate red ball combinations to generate
    TOP_PREDICTIONS = 5    # Final number of predictions to output
    FREQUENCY_WEIGHT = 0.3
    PARITY_WEIGHT = 0.2
    SUM_WEIGHT = 0.2
    SIZE_WEIGHT = 0.15
    GAP_WEIGHT = 0.15

CONFIG = Config()

# --------------------------
# Data Loading & Preprocessing
# --------------------------
def load_lottery_data(data_path: str = "./data/ssq/data.csv") -> pd.DataFrame:
    """Load and preprocess lottery data (supports real/simulated data)"""
    try:
        df = pd.read_csv(data_path)
        df = df[['红球_1', '红球_2', '红球_3', '红球_4', '红球_5', '红球_6', '蓝球']].astype(int)
        print(f"✅ Loaded real data: {len(df)} draws")
    except FileNotFoundError:
        print("⚠️  Real data not found. Generating simulated data...")
        np.random.seed(42)
        n_draws = 1500
        red_balls = []
        blue_balls = []
        
        for _ in range(n_draws):
            red = np.sort(np.random.choice(range(*CONFIG.RED_BALL_RANGE), size=CONFIG.RED_BALL_COUNT, replace=False))
            red_balls.append(red)
            blue = np.random.choice(range(*CONFIG.BLUE_BALL_RANGE), size=1)[0]
            blue_balls.append(blue)
        
        red_df = pd.DataFrame(red_balls, columns=[f'红球_{i}' for i in range(1, 7)])
        blue_df = pd.DataFrame(blue_balls, columns=['蓝球'])
        df = pd.concat([red_df, blue_df], axis=1)
        print(f"✅ Generated simulated data: {len(df)} draws")
    
    # Validate data integrity
    assert all(df[f'红球_{i}'].between(*CONFIG.RED_BALL_RANGE).all() for i in range(1, 7)), "Invalid red ball values"
    assert df['蓝球'].between(*CONFIG.BLUE_BALL_RANGE).all(), "Invalid blue ball values"
    
    return df

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Calculate key statistical metrics from historical data"""
    red_cols = [f'红球_{i}' for i in range(1, 7)]
    
    # 1. Frequency statistics
    all_red = df[red_cols].values.flatten()
    red_freq = pd.Series(all_red).value_counts(normalize=True).sort_index()
    blue_freq = df['蓝球'].value_counts(normalize=True).sort_index()
    
    # 2. Parity statistics (odd/even)
    df['red_odd_count'] = df[red_cols].apply(lambda x: sum(num % 2 == 1 for num in x), axis=1)
    odd_dist = df['red_odd_count'].value_counts(normalize=True).sort_index()
    
    # 3. Sum statistics
    df['red_sum'] = df[red_cols].sum(axis=1)
    sum_mean, sum_std = df['red_sum'].mean(), df['red_sum'].std()
    sum_norm_params = (sum_mean, sum_std)
    
    # 4. Size statistics (1-16: small, 17-33: large)
    df['red_large_count'] = df[red_cols].apply(lambda x: sum(num >= 17 for num in x), axis=1)
    large_dist = df['red_large_count'].value_counts(normalize=True).sort_index()
    
    # 5. Gap statistics (consecutive number differences)
    def calculate_gaps(row):
        balls = row[red_cols].values
        gaps = balls[1:] - balls[:-1]
        return gaps.mean()
    
    df['red_avg_gap'] = df.apply(calculate_gaps, axis=1)
    gap_mean, gap_std = df['red_avg_gap'].mean(), df['red_avg_gap'].std()
    gap_norm_params = (gap_mean, gap_std)
    
    # Compile metrics
    metrics = {
        'red_freq': red_freq,
        'blue_freq': blue_freq,
        'odd_dist': odd_dist,
        'sum_norm': sum_norm_params,
        'large_dist': large_dist,
        'gap_norm': gap_norm_params,
        'historical_df': df
    }
    
    return df, metrics

# --------------------------
# Candidate Generation
# --------------------------
def generate_red_candidates(metrics: Dict) -> List[np.ndarray]:
    """Generate candidate red ball combinations (sorted, no duplicates)"""
    candidates = []
    red_freq = metrics['red_freq']
    
    # Generate candidates with frequency bias
    while len(candidates) < CONFIG.CANDIDATE_COUNT:
        # Weighted random selection (favor under-represented balls)
        weights = 1 - red_freq.values  # Inverse frequency weighting
        weights = weights / weights.sum()
        
        candidate = np.random.choice(
            red_freq.index, 
            size=CONFIG.RED_BALL_COUNT, 
            replace=False, 
            p=weights
        )
        candidate = np.sort(candidate)
        
        # Avoid duplicate candidates
        if not any(np.array_equal(candidate, existing) for existing in candidates):
            candidates.append(candidate)
    
    return candidates

def generate_blue_candidates(metrics: Dict) -> List[int]:
    """Generate candidate blue balls"""
    blue_freq = metrics['blue_freq']
    weights = 1 - blue_freq.values  # Inverse frequency weighting
    weights = weights / weights.sum()
    
    # Top 5 candidates based on inverse frequency
    candidates = np.random.choice(
        blue_freq.index, 
        size=5, 
        replace=False, 
        p=weights
    ).tolist()
    
    return candidates

# --------------------------
# Consistency Scoring
# --------------------------
def calculate_red_consistency_score(candidate: np.ndarray, metrics: Dict) -> float:
    """Score candidate red balls based on statistical consistency"""
    red_freq = metrics['red_freq']
    odd_dist = metrics['odd_dist']
    sum_mean, sum_std = metrics['sum_norm']
    large_dist = metrics['large_dist']
    gap_mean, gap_std = metrics['gap_norm']
    
    # 1. Frequency uniformity score (lower = better)
    candidate_freq = pd.Series(candidate).value_counts(normalize=True)
    # Align with historical frequency index
    aligned_freq = pd.Series(0.0, index=red_freq.index)
    aligned_freq[candidate_freq.index] = candidate_freq.values
    freq_diff = np.abs(aligned_freq - red_freq).sum()
    freq_score = 1 - freq_diff  # Normalize to [0,1]
    
    # 2. Parity balance score
    odd_count = sum(num % 2 == 1 for num in candidate)
    parity_score = odd_dist.get(odd_count, 0.0)
    
    # 3. Sum distribution score (normal distribution probability)
    candidate_sum = candidate.sum()
    sum_z = (candidate_sum - sum_mean) / sum_std
    sum_score = norm.pdf(sum_z) / norm.pdf(0)  # Normalize to [0,1]
    
    # 4. Size balance score
    large_count = sum(num >= 17 for num in candidate)
    size_score = large_dist.get(large_count, 0.0)
    
    # 5. Gap distribution score
    gaps = candidate[1:] - candidate[:-1]
    avg_gap = gaps.mean()
    gap_z = (avg_gap - gap_mean) / gap_std
    gap_score = norm.pdf(gap_z) / norm.pdf(0)  # Normalize to [0,1]
    
    # Weighted total score
    total_score = (
        freq_score * CONFIG.FREQUENCY_WEIGHT +
        parity_score * CONFIG.PARITY_WEIGHT +
        sum_score * CONFIG.SUM_WEIGHT +
        size_score * CONFIG.SIZE_WEIGHT +
        gap_score * CONFIG.GAP_WEIGHT
    )
    
    return total_score

def calculate_blue_consistency_score(candidate: int, metrics: Dict) -> float:
    """Score candidate blue ball based on frequency uniformity"""
    blue_freq = metrics['blue_freq']
    # Inverse frequency score (favor under-represented)
    candidate_freq = blue_freq.get(candidate, 0.0)
    score = 1 - candidate_freq  # Higher = more under-represented
    return score

# --------------------------
# Prediction Pipeline
# --------------------------
def predict_next_draw(df: pd.DataFrame, metrics: Dict) -> List[Dict]:
    """Generate final predictions with highest consistency scores"""
    # Generate candidates
    red_candidates = generate_red_candidates(metrics)
    blue_candidates = generate_blue_candidates(metrics)
    
    # Score red candidates
    red_scores = [(cand, calculate_red_consistency_score(cand, metrics)) 
                  for cand in red_candidates]
    # Sort red candidates by score (descending)
    red_scores.sort(key=lambda x: x[1], reverse=True)
    top_red = [cand for cand, _ in red_scores[:CONFIG.TOP_PREDICTIONS]]
    
    # Score blue candidates
    blue_scores = [(cand, calculate_blue_consistency_score(cand, metrics)) 
                   for cand in blue_candidates]
    # Sort blue candidates by score (descending)
    blue_scores.sort(key=lambda x: x[1], reverse=True)
    top_blue = [cand for cand, _ in blue_scores[:CONFIG.TOP_PREDICTIONS]]
    
    # Create final predictions (pair top red and blue candidates)
    predictions = []
    for i in range(CONFIG.TOP_PREDICTIONS):
        predictions.append({
            'prediction_id': i + 1,
            'red_balls': top_red[i].tolist(),
            'blue_ball': top_blue[i],
            'red_score': red_scores[i][1],
            'blue_score': blue_scores[i][1],
            'total_score': (red_scores[i][1] + blue_scores[i][1]) / 2
        })
    
    return predictions

# --------------------------
# Validation & Visualization
# --------------------------
def validate_predictions(predictions: List[Dict], metrics: Dict) -> None:
    """Validate predictions against historical metrics"""
    sum_mean, sum_std = metrics['sum_norm']
    print("\n" + "="*60)
    print("Prediction Validation Report")
    print("="*60)
    
    for pred in predictions:
        red = np.array(pred['red_balls'])
        blue = pred['blue_ball']
        red_sum = red.sum()
        
        # Check sum range (within 2σ of historical mean)
        sum_within_range = abs(red_sum - sum_mean) <= 2 * sum_std
        
        # Check parity balance (historical common range: 2-4 odds)
        odd_count = sum(num % 2 == 1 for num in red)
        parity_valid = 2 <= odd_count <= 4
        
        # Check size balance (historical common range: 2-4 large balls)
        large_count = sum(num >= 17 for num in red)
        size_valid = 2 <= large_count <= 4
        
        print(f"\nPrediction {pred['prediction_id']}:")
        print(f"  Red Balls: {red.tolist()}, Blue Ball: {blue}")
        print(f"  Total Score: {pred['total_score']:.4f} (Red: {pred['red_score']:.4f}, Blue: {pred['blue_score']:.4f})")
        print(f"  Sum: {red_sum} (Mean±2σ: {sum_mean:.1f}±{2*sum_std:.1f}) - {'Valid' if sum_within_range else 'Invalid'}")
        print(f"  Parity (Odds): {odd_count} - {'Valid' if parity_valid else 'Invalid'}")
        print(f"  Size (Large): {large_count} - {'Valid' if size_valid else 'Invalid'}")

def plot_prediction_analysis(predictions: List[Dict], metrics: Dict) -> None:
    """Visualize predictions vs historical metrics"""
    plt.rcParams['figure.figsize'] = (15, 10)
    red_cols = [f'红球_{i}' for i in range(1, 7)]
    historical_df = metrics['historical_df']
    
    # 1. Red ball frequency comparison
    plt.subplot(2, 3, 1)
    all_historical_red = historical_df[red_cols].values.flatten()
    historical_freq = pd.Series(all_historical_red).value_counts().sort_index()
    
    # Combine all predicted red balls
    all_pred_red = np.concatenate([np.array(pred['red_balls']) for pred in predictions])
    pred_freq = pd.Series(all_pred_red).value_counts().sort_index()
    
    # Align indices
    all_red_numbers = range(*CONFIG.RED_BALL_RANGE)
    historical_freq_aligned = pd.Series(0, index=all_red_numbers)
    historical_freq_aligned[historical_freq.index] = historical_freq.values / len(historical_df)
    
    pred_freq_aligned = pd.Series(0, index=all_red_numbers)
    pred_freq_aligned[pred_freq.index] = pred_freq.values / len(predictions)
    
    plt.plot(historical_freq_aligned.index, historical_freq_aligned.values, 'b-', label='Historical', alpha=0.7)
    plt.plot(pred_freq_aligned.index, pred_freq_aligned.values, 'r-', label='Predictions', alpha=0.7)
    plt.title('Red Ball Frequency Comparison')
    plt.xlabel('Red Ball Number')
    plt.ylabel('Normalized Frequency')
    plt.legend()
    plt.xticks(range(1, 34, 3))
    
    # 2. Red sum distribution
    plt.subplot(2, 3, 2)
    pred_sums = [np.array(pred['red_balls']).sum() for pred in predictions]
    plt.hist(historical_df['red_sum'], bins=20, alpha=0.5, label='Historical', color='blue')
    plt.axvline(historical_df['red_sum'].mean(), color='blue', linestyle='--', label='Historical Mean')
    plt.hist(pred_sums, bins=5, alpha=0.8, label='Predictions', color='red')
    plt.title('Red Ball Sum Distribution')
    plt.xlabel('Sum of Red Balls')
    plt.ylabel('Frequency')
    plt.legend()
    
    # 3. Parity distribution
    plt.subplot(2, 3, 3)
    historical_odd_dist = historical_df['red_odd_count'].value_counts().sort_index()
    pred_odd_counts = [sum(num % 2 == 1 for num in pred['red_balls']) for pred in predictions]
    pred_odd_dist = pd.Series(pred_odd_counts).value_counts().sort_index()
    
    plt.bar(historical_odd_dist.index - 0.15, historical_odd_dist.values / len(historical_df), 
            width=0.3, label='Historical', alpha=0.7)
    plt.bar(pred_odd_dist.index + 0.15, pred_odd_dist.values / len(predictions), 
            width=0.3, label='Predictions', alpha=0.7)
    plt.title('Red Ball Odd Count Distribution')
    plt.xlabel('Number of Odd Red Balls')
    plt.ylabel('Normalized Frequency')
    plt.legend()
    plt.xticks(range(7))
    
    # 4. Blue ball frequency
    plt.subplot(2, 3, 4)
    historical_blue_freq = historical_df['蓝球'].value_counts().sort_index()
    pred_blue_balls = [pred['blue_ball'] for pred in predictions]
    pred_blue_freq = pd.Series(pred_blue_balls).value_counts().sort_index()
    
    plt.bar(historical_blue_freq.index - 0.15, historical_blue_freq.values / len(historical_df), 
            width=0.3, label='Historical', alpha=0.7)
    plt.bar(pred_blue_freq.index + 0.15, pred_blue_freq.values / len(predictions), 
            width=0.3, label='Predictions', alpha=0.7)
    plt.title('Blue Ball Frequency Comparison')
    plt.xlabel('Blue Ball Number')
    plt.ylabel('Normalized Frequency')
    plt.legend()
    plt.xticks(range(1, 17, 2))
    
    # 5. Large ball distribution
    plt.subplot(2, 3, 5)
    historical_large_dist = historical_df['red_large_count'].value_counts().sort_index()
    pred_large_counts = [sum(num >= 17 for num in pred['red_balls']) for pred in predictions]
    pred_large_dist = pd.Series(pred_large_counts).value_counts().sort_index()
    
    plt.bar(historical_large_dist.index - 0.15, historical_large_dist.values / len(historical_df), 
            width=0.3, label='Historical', alpha=0.7)
    plt.bar(pred_large_dist.index + 0.15, pred_large_dist.values / len(predictions), 
            width=0.3, label='Predictions', alpha=0.7)
    plt.title('Red Ball Large Count Distribution')
    plt.xlabel('Number of Large Red Balls (≥17)')
    plt.ylabel('Normalized Frequency')
    plt.legend()
    plt.xticks(range(7))
    
    # 6. Prediction scores
    plt.subplot(2, 3, 6)
    pred_ids = [pred['prediction_id'] for pred in predictions]
    total_scores = [pred['total_score'] for pred in predictions]
    plt.bar(pred_ids, total_scores, color='green', alpha=0.7)
    plt.title('Prediction Consistency Scores')
    plt.xlabel('Prediction ID')
    plt.ylabel('Total Consistency Score')
    plt.ylim(0, 1)
    plt.xticks(pred_ids)
    
    plt.tight_layout()
    plt.show()

# --------------------------
# Main Execution
# --------------------------
def main():
    # 1. Load and preprocess data
    df = load_lottery_data()
    df, metrics = preprocess_data(df)
    
    # 2. Generate predictions
    print("Generating predictions (minimizing statistical changes)...")
    predictions = predict_next_draw(df, metrics)
    
    # 3. Print results
    print("\n" + "="*60)
    print("Top Predictions (Most Consistent with Historical Data)")
    print("="*60)
    for pred in predictions:
        print(f"\nPrediction {pred['prediction_id']}:")
        print(f"  Red Balls: {sorted(pred['red_balls'])}")
        print(f"  Blue Ball: {pred['blue_ball']}")
        print(f"  Consistency Score: {pred['total_score']:.4f}")
    
    # # 4. Validate and visualize
    # validate_predictions(predictions, metrics)
    # plot_prediction_analysis(predictions, metrics)
    
    # 5. Disclaimer
    print("\n" + "="*60)
    print("DISCLAIMER")
    print("="*60)
    print("1. This prediction is based on historical statistical analysis only")
    print("2. Lottery draws are random events - no prediction can guarantee winning")
    print("3. Please gamble responsibly and within your financial means")
    print("="*60)

if __name__ == "__main__":
    main()