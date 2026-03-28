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
    for _ in tqdm(range(n), desc="generating tickets:"):
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
    
    # Group tickets by purchase count
    groups = defaultdict(list)
    for ticket, cnt in ticket_counter.items():
        groups[cnt].append(ticket)
    
    # Target counts you want: 3,5,6,7,8
    target_counts = [3,5,6,7,8]
    
    print("\n" + "="*70)
    print("Randomly Selected Tickets from Each Purchase Count Group")
    print("="*70)
    
    for cnt in target_counts:
        if cnt in groups and len(groups[cnt]) > 0:
            selected = random.choice(groups[cnt])
            print(f"Purchase Count = {cnt} | Random Ticket: {selected}")
        else:
            print(f"Purchase Count = {cnt} | No tickets found")
    
    print("="*70)

if __name__ == "__main__":
    main()