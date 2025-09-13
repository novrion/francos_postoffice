import sys
import random
import math

class UnitTest:
    @staticmethod
    def test_n_tasks_probability_distr():
        map = dict()
        for i in range(100000):
            customer = Customer(0, TimeStamp())
            if not customer.n_tasks in map:
                map[customer.n_tasks] = 1
            else:
                map[customer.n_tasks] += 1
        
        li = []
        for key in map:
            li.append([key, map[key]])
        li.sort()
        for item in li:
            print(f"n_tasks: {item[0]}, % of total customers: {item[1] / 1000}%")


class TimeStamp:
    def __init__(self, valid_timestamp_str: str = None, time: int = None):
        if valid_timestamp_str:
            parts = valid_timestamp_str.strip().split(':')
            hour = int(parts[0])
            minutes = int(parts[1])
            self.time = hour * 60 + minutes
        elif time:
            self.time = time
        else:
            self.time = 0

    def __str__(self):
        hour = self.time // 60
        minutes = self.time % 60
        formatted_minutes = minutes if minutes >= 10 else f"0{minutes}"
        return f"{hour}:{formatted_minutes}"
    
    def __gt__(self, other):
        return self.time > other.time
    
    def __ge__(self, other):
        return self.time >= other.time
    
    def __lt__(self, other):
        return self.time < other.time
    
    def __le__(self, other):
        return self.time <= other.time
    
    def __eq__(self, other):
        return self.time == other.time
    
    def add_minutes(self, minutes: int):
        self.time += minutes
        for i in range(self.time // (24 * 60)):
            self.time -= 24 * 60

    @staticmethod
    def assert_valid_timestamp(timestamp_str: str):
        try:
            parts = timestamp_str.strip().split(':')
            if len(parts) != 2:
                return False

            hour = int(parts[0])
            minutes = int(parts[1])
            return (0 <= hour <= 23) and (0 <= minutes <= 59)
        except:
            print("Failed to parse timestamp string. Invalid.")
            return False


class Customer:
    def __init__(self, id, current_time: TimeStamp):
        self.id = id
        self.n_tasks = self.randomise_n_tasks()
        self.entry_time = TimeStamp(time=current_time.time)
        self.exit_time = None
        self.wait_time = 0

    def __str__(self):
        return f"customer {self.id}"

    def randomise_n_tasks(self):
        ret = 1
        while True:
            if random.random() >= 0.5:
                ret += 1
            else:
                return ret

    def set_exit_time(self, current_time: TimeStamp, minutes_to_complete_task: int):
        self.exit_time = TimeStamp(time=current_time.time)
        self.exit_time.add_minutes(minutes_to_complete_task * self.n_tasks)
        self.wait_time = self.exit_time.time - self.entry_time.time

class Organisation:
    def __init__(self, params_path):

        # Parameters
        self.open: TimeStamp = None
        self.close: TimeStamp = None
        self.customer_spawn_probability = 0.0
        self.robbery_probability = 0.0
        self.robbery_success_rate = 0.0
        self.robbery_customer_spawn_probability_boost = 0.0
        self.robbery_customer_spawn_probability_drop = 0.0
        self.minutes_to_complete_task = 0
        self.robbery_kill_probability = 0.0
        self.robbery_spawn_prob_adj_coefficient = 1

        if not self.initialise_params(params_path):
            raise ValueError(f"Error initialising parameters with path: {params_path}")

        self.queue = []
        self.current_time = TimeStamp(time=self.open.time)
        self.customer_count = 0
        self.total_customer_wait_time = 0

        self.last_robbery_time = None
        self.last_robbery_successful = None

    @staticmethod
    def assert_valid_probability(val):
        return 0 <= val <= 1
        
    def initialise_params(self, path):
        file = open(path, 'r')
        if not file:
            print(f"Error opening file: {path}.")
            return False

        try:
            lines = file.readlines()
            params = lines[1].strip().split(',')

            if not TimeStamp.assert_valid_timestamp(params[0]) or not TimeStamp.assert_valid_timestamp(params[1]):
                print("Invalid timestamp. Should be formatted xx:yy (00 <= xx <= 23, 00 <= yy <= 59).")
                return False
            
            self.open = TimeStamp(valid_timestamp_str=params[0])
            self.close = TimeStamp(valid_timestamp_str=params[1])
            if self.close <= self.open:
                print("Invalid timestamps. Close must be after open.")
                return False

            self.customer_spawn_probability = float(params[2])
            if not self.assert_valid_probability(self.customer_spawn_probability):
                print("Invalid customer_spawn_probability. Should be between 0 and 1.")
                return False

            self.robbery_probability = float(params[3])
            if not self.assert_valid_probability(self.robbery_probability):
                print("Invalid robbery_probability. Should be between 0 and 1.")
                return False

            self.robbery_success_rate = float(params[4])
            if not self.assert_valid_probability(self.robbery_probability):
                print("Invalid robbery_probability. Should be between 0 and 1.")
                return False

            self.robbery_customer_spawn_probability_boost = float(params[5])
            if not self.assert_valid_probability(self.robbery_customer_spawn_probability_boost):
                print("Invalid robbery_customer_spawn_probability_boost. Should be between 0 and 1.")
                return False

            self.robbery_customer_spawn_probability_drop = float(params[6])
            if not self.assert_valid_probability(self.robbery_customer_spawn_probability_drop):
                print("Invalid robbery_customer_spawn_probability_drop. Should be between 0 and 1.")
                return False

            self.minutes_to_complete_task = int(params[7])
            if not self.minutes_to_complete_task > 0:
                print("Invalid minutes_to_complete_task. Should be an integer greater than 0.")
                return False

            self.robbery_kill_probability = float(params[8])
            if not self.assert_valid_probability(self.robbery_kill_probability):
                print("Invalid robbery_kill_probability. Should be between 0 and 1.")
                return False

            self.robbery_spawn_prob_adj_coefficient = float(params[9])
            if self.robbery_spawn_prob_adj_coefficient <= 0:
                print("Invalid robbery_spawn_prob_adj_coefficient. Should be greater than 0.")
                return False

        except:
            print(f"Error parsing parameters in file: {path}")
            return False

        file.close()
        return True

    def print_params(self):
        print("============= SIMULATION PARAMETERS =============")
        print(f"open: {self.open}")
        print(f"close: {self.close}")
        print(f"customer_spawn_probability: {self.customer_spawn_probability}")
        print(f"robbery_probability: {self.robbery_probability}")
        print(f"robbery_customer_spawn_probability_boost: {self.robbery_customer_spawn_probability_boost}")
        print(f"robbery_customer_spawn_probability_drop: {self.robbery_customer_spawn_probability_drop}")
        print(f"minutes_to_complete_task: {self.minutes_to_complete_task}")
        print("=================================================")

    def print_statistics(self):
        if self.customer_count == 0:
            print("STATISTICS: 0 customers, total customer wait time 0 minutes")
        else:
            print(f"STATISTICS: {self.customer_count} customers, total customer wait time {self.total_customer_wait_time} minutes = {self.total_customer_wait_time // self.customer_count} minutes per customer")

    def simulate_robbery(self):
        n_kills = 0
        for customer in self.queue:
            self.total_customer_wait_time += self.current_time.time - customer.entry_time.time
            if random.random() <= self.robbery_kill_probability:
                n_kills += 1
        self.queue.clear()
        
        print(f"Kl {self.current_time} A robber has entered the organisation! The queue has dispersed and {n_kills} customers have been killed!")
        print(f"Madame Franco, who has a black belt in karate, tries to fight off the robbers, ", end='')

        # Madame Franco succeeds or fails
        if random.random() <= self.robbery_success_rate:
            print("but fails.")
            self.last_robbery_successful = True
        else:
            print("and succeeds!")
            self.last_robbery_successful = False

        self.last_robbery_time = TimeStamp(time=self.current_time.time)


    def spawn_customer(self):
        spawn_rate = self.customer_spawn_probability
        if self.last_robbery_time:
            time_diff = self.current_time.time - self.last_robbery_time.time - 1
            probability_adjustment = -self.robbery_customer_spawn_probability_drop if self.last_robbery_successful else self.robbery_customer_spawn_probability_boost
            spawn_rate = self.customer_spawn_probability + pow(math.e, -time_diff/self.robbery_spawn_prob_adj_coefficient) * probability_adjustment
            if abs(spawn_rate - self.customer_spawn_probability) < 0.01:
                self.last_robbery_time = None
                self.last_robbery_successful = None

        return random.random() <= spawn_rate


    def simulate(self):
        print("Starting simulation with parameters:")
        self.print_params()

        while True:

            # End simulation if past closing time and no more customer
            if self.current_time > self.close and not self.queue:
                self.print_statistics()
                return

            # Opening time
            if self.current_time == self.open:
                print("Kl ", self.current_time, "öppnas dörren")

            # Closing time
            if self.current_time == self.close:
                print("Kl ", self.current_time, "stängs dörren")

            # Robbery
            if random.random() <= self.robbery_probability:
                self.simulate_robbery()

                # No new customers and all customers from the line are removed if robbery
                self.current_time.add_minutes(1)
                continue

            # New customer
            if self.current_time < self.close and self.spawn_customer():
                self.customer_count += 1
                new_customer = Customer(self.customer_count, self.current_time)
                if not self.queue:
                    new_customer.set_exit_time(self.current_time, self.minutes_to_complete_task)
                self.queue.append(new_customer)

                if len(self.queue) == 1:
                    print("Kl ", self.current_time, f"kommer kund {new_customer.id} in och blir genast betjänad")
                else:
                    print("Kl ", self.current_time, f"kommer kund {new_customer.id} in och ställer sig i kön som nr {len(self.queue)}")

            # Customer leaves (all tasks are complete)
            if self.queue and self.queue[0].exit_time == self.current_time:
                completed_customer = self.queue.pop(0)
                self.total_customer_wait_time += completed_customer.wait_time
                if self.queue:
                    print("Kl ", self.current_time, f"går kund {completed_customer.id} och kund {self.queue[0].id} blir betjänad")
                    self.queue[0].set_exit_time(self.current_time, self.minutes_to_complete_task)
                else:
                    print("Kl ", self.current_time, f"går kund {completed_customer.id}")

            self.current_time.add_minutes(1)


def main():

    # Initialise simulation with parameters (let the user decide parameter file path)
    while True:
        path = input("File to parse for parameters: ")
        try:
            organisation = Organisation(path)
        except ValueError as err:
            print(f"Could not initialise organisation with path: {path}")
            print(err)
            continue
        break

    organisation.simulate()

if __name__ == "__main__":
    main()
