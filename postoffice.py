import random
import math

def time_str(time_int: int):
    # Takes time represented in minutes as an integer > 0
    # Returns the time as a string in 24h format (xx:yy) where 0 <= xx <= 23 and 0 <= yy <= 59

    if time_int < 0:
        raise ValueError("Invalid time_int arg in time_str(). Should be an integer >= 0.")
    for i in range(time_int // (24 * 60)):
        time_int -= 24 * 60
    hours = time_int // 60
    minutes = time_int % 60
    formatted_minutes = minutes if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{formatted_minutes}"

def time_int(time_str: str):
    # Takes time represented as a string in 24h format (xx:yy) where 0 <= xx <= 23 and 0 <= yy <= 59
    # Returns time represented in minutes as an integer > 0
    
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
    # A class containing the specification of a customer
    # Each customer has an identification, a certain number of tasks it needs completed, an entry time, and an exit time
    # Used heavily in simulation
    
    def __init__(self, id, time):
        # Takes an id and the current time
        # Constructs a Customer object

        self.id = id
        self.n_tasks = self.get_random_n_tasks()
        self.entry_time = time
        self.exit_time = None

    def set_exit_time(self, time, min_per_task):
        # Takes the current time and the time it takes to complete each task
        # Sets the time the customer should leave the post office

        self.exit_time = time + self.n_tasks * min_per_task

    def get_wait_time(self, time):
        # Takes the current time
        # Returns the time the customer has waited in the post office

        return time - self.entry_time

    @staticmethod
    def get_random_n_tasks():
        # Randomises the number of tasks the customer needs to complete
        # 50% for 1 task, 25% for 2 tasks, 12.5% for 3 tasks...
        
        ret = 1
        while True:
            if random.random() <= 0.5:
                ret += 1
            else:
                return ret



class PostOffice:
    # A class containing the specifications of a post office
    # This is the main class used in simulation
    # Contains parameters (specified in __init__()) that specify simulation

    def __init__(self):
        self.queue = [] # The current queue of customers
        self.time = 0 # Time represented as an integer (minutes): 0 <= x < 24 * 60
        self.n_customers = 0 # Total number of customers processed
        self.tot_wait_time = 0 # Total customer wait time

        self.robbery_time = None # Time of last robbery (None if no robbery yet)
        self.robbery_succeeded = None # If the last robbery succeeded (None if no robbery yet)

        self.end = False # If simulation has ended
        self.logs = [] # The logs to display to the user

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

        # Helper variables
        self.init_simulation = False

    def log(self, text):
        # Takes a string of text and saves it to the PostOffice's logs list for display in the TUI

        self.logs.append(text.strip())

    def should_do_robbery(self):
        # Determines if a robbery should occur now
        # Returns True or False

        return self.time < self.close and random.random() <= self.robbery_prob

    def do_robbery(self):
        # Simulates a robbery
        # Calculates the number of customers are killed by the robbers
        # Before clearing the queue, wait time is added to total wait time
        # robbery_succeeded is randomised and robbery_time is updated to now
        # What occurs is logged

        n_kills = 0
        for customer in self.queue:
            self.tot_wait_time += customer.get_wait_time(self.time)
            if random.random() <= self.robbery_kill_prob:
                n_kills += 1
        self.queue.clear()

        self.log(f"{time_str(self.time)} A robber has entered the post office!")
        self.log(f"The queue has dispersed and {n_kills} customers have been killed!")

        self.robbery_succeeded = random.random() <= self.robbery_success_prob
        self.robbery_time = self.time

        if self.robbery_succeeded:
            self.log("Madame Franco, who has a black belt in karate, tries to fight off the robber, but fails.")
        else:
            self.log("Madame Franco, who has a black belt in karate, tries to fight off the robber, and succeeds!")

    def should_spawn_customer(self):
        # Determines if a customer should spawn now
        # Randomises based on the spawn_prob parameter and based on if a robbery has recently occurred
        # the final spawn probability is adj * e^(-t/co)
        # where adj is the maximum boost or drop in spawn probability,
        # t is the time since the last robbery,
        # and co is a coefficient to determine how quickly the spawn probability effects of the robbery subsides
        # Returns True or False

        if self.time >= self.close:
            return False
        
        spawn_prob = self.spawn_prob
        if self.robbery_time:
            time_diff = self.time - self.robbery_time
            prob_adj = -self.robbery_spawn_prob_drop if self.robbery_succeeded else self.robbery_spawn_prob_boost
            spawn_prob += prob_adj * pow(math.e, -time_diff/self.robbery_spawn_prob_adj_coefficient)

        return random.random() <= spawn_prob

    def spawn_customer(self):
        # Spawns a customer
        # Updates the total number of customers, and adds a new customer to the queue
        # If the queue was empty, the customer's exit time is determined
        # The events are logged

        self.n_customers += 1
        new_customer = Customer(self.n_customers, self.time)
        if not self.queue:
            new_customer.set_exit_time(self.time, self.min_per_task)
            self.log(f"{time_str(self.time)} Customer {new_customer.id} enters the post office and is served immediately")
        else:
            self.log(f"{time_str(self.time)} Customer {new_customer.id} enters the post office and stands in line as no. {len(self.queue) + 1}")
        self.queue.append(new_customer)

    def should_customer_leave(self):
        # Determines if the customer in front of the queue should leave the post office
        # Returns true or false
        
        return self.queue and self.queue[0].exit_time == self.time

    def customer_leaves(self):
        # A customer leaves
        # total wait time is updated
        # the customer in front of the queue is removed from the queue
        # The events are logged

        leaving_customer = self.queue.pop(0)
        self.tot_wait_time += leaving_customer.get_wait_time(self.time)
        if self.queue:
            self.queue[0].set_exit_time(self.time, self.min_per_task)
            self.log(f"{time_str(self.time)} Customer {leaving_customer.id} leaves and customer {self.queue[0].id} is served")
        else:
            self.log(f"{time_str(self.time)} Customer {leaving_customer.id} leaves")

    def simulate(self):
        # Simulates the post office until something happens
        # Returns False when simulation is complete, else True

        # If first time calling simulate(), set current time to opening time
        if not self.init_simulation:
            self.time = self.open
            self.init_simulation = True

        update = False
        while not update:

            # End of simulation (past closing and no more customers)
            if self.time > self.close and not self.queue:
                self.end = True
                break

            # Post office opens
            if self.time == self.open:
                self.log(f"{time_str(self.time)} The post office opens")
                update = True

            # Post office closes
            if self.time == self.close:
                self.log(f"{time_str(self.time)} The post office closes")
                update = True

            # Robbery
            if self.should_do_robbery():
                self.do_robbery()
                self.time += 1
                break

            # New customer
            if self.should_spawn_customer():
                update = True
                self.spawn_customer()

            # Customer leaves
            if self.should_customer_leave():
                update = True
                self.customer_leaves()

            self.time += 1

    def update_param(self, param_name, new_val):
        # Takes a new parameter value and the parameter's name as a string
        # Updates the corresponding parameter with the new value

        if param_name == "open":
            self.open = time_int(new_val)
        elif param_name == "close":
            self.close = time_int(new_val)
        elif param_name == "spawn_prob":
            self.spawn_prob = float(new_val)
        elif param_name == "min_per_task":
            self.min_per_task = int(new_val)
        elif param_name == "robbery_prob":
            self.robbery_prob = float(new_val)
        elif param_name == "robbery_success_prob":
            self.robbery_success_prob = float(new_val)
        elif param_name == "robbery_kill_prob":
            self.robbery_kill_prob = float(new_val)
        elif param_name == "robbery_spawn_prob_boost":
            self.robbery_spawn_prob_boost = float(new_val)
        elif param_name == "robbery_spawn_prob_drop":
            self.robbery_spawn_prob_drop = float(new_val)
        elif param_name == "robbery_spawn_prob_adj_coefficient":
            self.robbery_spawn_prob_adj_coefficient = float(new_val)

    def get_params(self):
        # Returns a list of the current parameter values

        return [
            time_str(self.open),
            time_str(self.close),
            self.spawn_prob,
            self.min_per_task,
            self.robbery_prob,
            self.robbery_success_prob,
            self.robbery_kill_prob,
            self.robbery_spawn_prob_boost,
            self.robbery_spawn_prob_drop,
            self.robbery_spawn_prob_adj_coefficient,
        ]

    @staticmethod
    def get_param_names():
        # Returns a list of the parameter names

        return [
            "open",
            "close",
            "spawn_prob",
            "min_per_task",
            "robbery_prob",
            "robbery_success_prob",
            "robbery_kill_prob",
            "robbery_spawn_prob_boost",
            "robbery_spawn_prob_drop",
            "robbery_spawn_prob_adj_coefficient"
        ]

    @staticmethod
    def get_param_descriptions():
        # Returns a list of more descriptions of the parameters
        
        return [
            "Opening time of postoffice",
            "Closing time of postoffice",
            "Probability a customer enters each minute",
            "How many minutes it takes Franco to complete a customer's task",
            "Probability the postoffice is robbed each minute",
            "Probability a robbery succeeds",
            "Probability a customer is killed during robbery",
            "Fixed increase in probability a customer enters the post office after unsuccessful robbery",
            "Fixed decrease in probability a customer enters the post office after successful robbery",
            "Coefficient to decay probability adjustment after robbery (low values decay quicker)"
        ]

    @staticmethod
    def assert_valid_param(param, param_name):
        # Takes a user's input value for a parameter and the parameter's name
        # Returns a tuple (bool, str) where bool is False when the user input is invalid, else True
        # str is the error message when bool is False
        # Each parameter has its own requirements for validity

        valid = (True, "")

        if param_name in ["open", "close"]:
            invalid = (False, "24h format 'xx:yy'")

            try:
                t = time_int(param)
                if t < 0:
                    return invalid 
                return valid 
            except:
                return invalid

        elif param_name in ["spawn_prob", "robbery_prob", "robbery_success_prob", "robbery_kill_prob", "robbery_spawn_prob_boost", "robbery_spawn_prob_drop"]:
            invalid = (False, f"0 <= {param_name} <= 1")

            try:
                var = float(param)
                if var > 1 or var < 0:
                    return invalid
                return valid
            except:
                return invalid

        elif param_name in ["min_per_task"]:
            invalid = (False, "Must be integer greater than 0")

            try:
                var = int(param)
                if var < 1:
                    return invalid
                return valid
            except:
                return invalid

        elif param_name in ["robbery_spawn_prob_adj_coefficient"]:
            invalid = (False, "Must be greater than 0")

            try:
                var = float(param)
                if var <= 0:
                    return invalid
                return valid
            except:
                return invalid

        return False
