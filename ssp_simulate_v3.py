import random
from tqdm import tqdm
from collections import Counter, defaultdict
import numpy as np
import matplotlib.pyplot as plt

def generate_ticket():
    red_balls = tuple(sorted(random.sample(range(1, 34), 6)))
    blue_ball = random.randint(1, 16)
    return red_balls + (blue_ball,)

def generate_multiple_tickets(n):
    counter = Counter()
    for _ in tqdm(range(n), desc="Generating tickets"):
        ticket = generate_ticket()
        counter[ticket] += 1
    return counter

def main():
    total_sales = 400_000_000
    ticket_price = 2
    n_tickets = total_sales // ticket_price
    print(f"Total tickets to generate: {n_tickets}")

    ticket_counter = generate_multiple_tickets(n_tickets)

    # Count how many unique tickets exist for each purchase count
    count_distribution = defaultdict(int)
    for ticket, count in ticket_counter.items():
        if 1 <= count <= 35:
            count_distribution[count] += 1

    # Prepare data for plotting
    x = list(range(1, 36))
    y = [count_distribution.get(c, 0) for c in x]

    # Print result table
    print("\n" + "-" * 50)
    print("Purchase Count | Unique Ticket Count")
    print("-" * 50)
    for c in x:
        print(f"{c:>13} | {count_distribution.get(c, 0):>18}")
    print("-" * 50)

    # Plot distribution
    plt.figure(figsize=(12, 6))
    bars = plt.bar(x, y, color='#4477dd', alpha=0.8, edgecolor='black')
    plt.xlabel("Number of Times Purchased", fontsize=12)
    plt.ylabel("Number of Unique Tickets", fontsize=12)
    plt.title("Distribution of Unique Tickets by Purchase Count (1 to 35)", fontsize=14)
    plt.xticks(np.arange(1, 36, 1))
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()