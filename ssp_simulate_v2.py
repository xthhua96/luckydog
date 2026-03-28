import random
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

def generate_ticket():
    red_balls = tuple(sorted(random.sample(range(1, 34), 6)))
    blue_ball = random.randint(1, 16)
    return red_balls + (blue_ball,)

def generate_multiple_tickets(n):
    counter = Counter()
    for _ in range(n):
        ticket = generate_ticket()
        counter[ticket] += 1
    return counter

def check_prize(winning_ticket, ticket):
    red_win, blue_win = winning_ticket[:6], winning_ticket[6]
    red, blue = ticket[:6], ticket[6]
    red_hit = len(set(red) & set(red_win))
    blue_hit = (blue == blue_win)

    if red_hit == 6 and blue_hit:
        return "First"
    elif red_hit == 6 and not blue_hit:
        return "Second"
    elif red_hit == 5 and blue_hit:
        return "Third"
    elif red_hit == 5 or (red_hit == 4 and blue_hit):
        return "Fourth"
    elif red_hit == 4 or (red_hit == 3 and blue_hit):
        return "Fifth"
    elif blue_hit:
        return "Sixth"
    else:
        return None

def count_all_prizes(counter, winning_ticket):
    prizes = {
        "First": 0,
        "Second": 0,
        "Third": 0,
        "Fourth": 0,
        "Fifth": 0,
        "Sixth": 0
    }
    for ticket, count in counter.items():
        res = check_prize(winning_ticket, ticket)
        if res in prizes:
            prizes[res] += count
    return prizes

def main():
    total_sales = 400_000_000
    ticket_price = 2
    n_tickets = total_sales // ticket_price
    print(f"Generating {n_tickets} tickets...")

    ticket_counter = generate_multiple_tickets(n_tickets)
    sorted_items = sorted(ticket_counter.items(), key=lambda x: x[1])
    tickets_sorted = [t for t, c in sorted_items]
    counts_sorted = [c for t, c in sorted_items]

    sample_points = 50
    indices = np.linspace(0, len(tickets_sorted)-1, sample_points, dtype=int)

    trend = {
        "purchase_count": [],
        "First": [],
        "Second": [],
        "Third": [],
        "Fourth": [],
        "Fifth": [],
        "Sixth": []
    }

    print("Sampling tickets from lowest to highest purchase count...")
    for idx in indices:
        win_ticket = tickets_sorted[idx]
        purchase_count = counts_sorted[idx]
        prizes = count_all_prizes(ticket_counter, win_ticket)

        trend["purchase_count"].append(purchase_count)
        trend["First"].append(prizes["First"])
        trend["Second"].append(prizes["Second"])
        trend["Third"].append(prizes["Third"])
        trend["Fourth"].append(prizes["Fourth"])
        trend["Fifth"].append(prizes["Fifth"])
        trend["Sixth"].append(prizes["Sixth"])

    plt.figure(figsize=(12,7))
    colors = ['#ff3333', '#ff9933', '#ffff33', '#33ff33', '#3399ff', '#9933ff']
    labels = ["1st", "2nd", "3rd", "4th", "5th", "6th"]
    keys = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"]

    for i, key in enumerate(keys):
        plt.plot(trend["purchase_count"], trend[key], label=labels[i], color=colors[i], linewidth=2)

    plt.xlabel("Ticket Purchase Count")
    plt.ylabel("Number of Winners")
    plt.title("Prize Winner Trend from Lowest to Highest Purchase Tickets")
    plt.yscale("log")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()