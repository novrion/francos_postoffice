import random
import math
import curses
from curses import wrapper
from curses.textpad import rectangle

def time_str(time_int: int):
    if time_int < 0:
        raise ValueError("Invalid time_int arg in time_str(). Should be an integer >= 0.")
    for i in range(time_int // (24 * 60)):
        time_int -= 24 * 60
    hours = time_int // 60
    minutes = time_int % 60
    formatted_minutes = minutes if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes}"

def time_int(time_str: str):
    parts = time_str.strip().split(':')
    if len(parts) != 2:
        raise ValueError("Invalid time_str arg in time_int(). Should be formatted xx:yy (0 <= xx <= 23, 0 <= yy <= 59)")
    try:
        hour = int(parts[0])
        minutes = int(parts[1])
        if not ((0 <= hour <= 23) and (0 <= minutes <= 59)):
            raise ValueError()
        return hour * 60 + minutes
    except ValueError as err:
        raise ValueError("Invalid time_str arg in time_int(). Could not convert xx (hours) and yy (minutes) of 'xx:yy' to integers.")

class Customer:
    def __init__(self, id, time):
        self.id = id
        self.n_tasks = self.get_random_n_tasks()
        self.entry_time = time
        self.exit_time = None

    def set_exit_time(self, time, min_per_task):
        self.exit_time = time + self.n_tasks * min_per_task

    def get_wait_time(self, time):
        return time - self.entry_time

    @staticmethod
    def get_random_n_tasks():
        ret = 1
        while True:
            if random.random() <= 0.5:
                ret += 1
            else:
                return ret

class PostOffice:
    def __init__(self):
        self.queue = [] # The current queue of customers
        self.time = 0 # Time represented as an integer (minutes): 0 <= x < 24 * 60
        self.n_customers = 0 # Total number of customers processed
        self.tot_wait_time = 0 # Total customer wait time

        self.robbery_time = None # Time of last robbery (None if no robbery yet)
        self.robbery_succeeded = None # If the last robbery succeeded (None if no robbery yet)

        # Parameters
        self.open = time_int("09:00") # Opening time
        self.close = time_int("18:00") # Closing time
        self.spawn_prob = 0.2 # Probability a customer enters each minute
        self.min_per_task = 2 # Time to complete a task
        self.robbery_prob = 0.001 # Probability a robbery occurs each minute
        self.robbery_success_prob = 0.3 # Probability a robbery succeeds
        self.robbery_kill_prob = 0.5 # Probability each customer dies from robbery
        self.robbery_spawn_prob_boost = 0.3 # Fixed boost in customer spawn probability after unsuccessful robbery
        self.robbery_spawn_prob_drop = 0.15 # Fixed drop in customer spawn probability after successful robbery
        self.robbery_spawn_prob_adj_coefficient = 10 # Coefficient to determine the longevity of adjusted spawn probability after a robbery

    def should_do_robbery(self):
        return self.time < self.close and random.random() <= self.robbery_prob

    def do_robbery(self):
        # TODO: Add logs
        n_kills = 0
        for customer in self.queue:
            self.tot_wait_time += customer.get_wait_time(self.time)
            if random.random() <= self.robbery_kill_prob:
                n_kills += 1
        self.queue.clear()

        self.robbery_succeeded = random.random() <= self.robbery_success_prob
        self.robbery_time = self.time

    def should_spawn_customer(self):
        if self.time >= self.close:
            return False
        
        spawn_prob = self.spawn_prob
        if self.robbery_time:
            time_diff = self.time - self.robbery_time
            prob_adj = -self.robbery_spawn_prob_drop if self.robbery_succeeded else self.robbery_spawn_prob_boost
            spawn_prob += prob_adj * pow(math.e, -time_diff/self.robbery_spawn_prob_adj_coefficient)

        return random.random() <= spawn_prob

    def spawn_customer(self):
        # TODO: Add logs
        self.n_customers += 1
        new_customer = Customer(self.n_customers, self.time)
        if not self.queue:
            new_customer.set_exit_time(self.time, self.min_per_task)
        self.queue.append(new_customer)

    def should_customer_leave(self):
        return self.queue and self.queue[0].exit_time == self.time

    def customer_leaves(self):
        # TODO: Add logs
        leaving_customer = self.queue.pop(0)
        self.tot_wait_time += leaving_customer.get_wait_time(self.time)
        if self.queue:
            self.queue[0].set_exit_time(self.time, self.min_per_task)

    def simulate(self):
        update = False
        while not update:

            # End of simulation (past closing and no more customers)
            if self.time > self.close and not self.queue:
                # TODO: Show statistics
                return

            # Post office opens
            if self.time == self.open:
                # TODO: Opening log
                update = True

            # Post office closes
            if self.time == self.close:
                # TODO: Closing log
                update = True

            # Robbery
            if self.should_do_robbery():
                self.do_robbery()
                self.time += 1
                return

            # New customer
            if self.should_spawn_customer():
                update = True
                self.spawn_customer()

            # Customer leaves
            if self.should_customer_leave():
                update = True
                self.customer_leaves()

            self.time += 1

class GUI():
    def __init__(self):
        pass

    def run(self):
        pass


def main():
    postoffice = PostOffice()
    gui = GUI()
    gui.run(postoffice)

if __name__ == "__main__":
    main()
