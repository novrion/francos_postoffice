def time_str(time_int: int):
    # Takes time represented in minutes as an integer > 0
    # Returns the time as a string in 24h format (xx:yy) where 0 <= xx <= 23 and 0 <= yy <= 59

def time_int(time_str: str):
    # Takes time represented as a string in 24h format (xx:yy) where 0 <= xx <= 23 and 0 <= yy <= 59
    # Returns time represented in minutes as an integer > 0

class Customer:
    # A class containing the specification of a customer
    # Each customer has an identification, a certain number of tasks it needs completed, an entry time, and an exit time
    # Used heavily in simulation
    
    def __init__(self, id, time):
        # Takes an id and the current time
        # Constructs a Customer object
        # id, n_tasks, entry_time, exit_time
        pass

    def set_exit_time(self, time, min_per_task):
        # Takes the current time and the time it takes to complete each task
        # Sets the time the customer should leave the post office
        pass

    def get_wait_time(self, time):
        # Takes the current time
        # Returns the time the customer has waited in the post office
        pass

    @staticmethod
    def get_random_n_tasks():
        # Randomises the number of tasks the customer needs to complete
        # 50% for 1 task, 25% for 2 tasks, 12.5% for 3 tasks...
        pass



class PostOffice:
    # A class containing the specifications of a post office
    # This is the main class used in simulation
    # Contains parameters (specified in __init__()) that specify simulation

    def __init__(self):
        # queue (list), time, n_customers, tot_wait_time
        # robbery_time, robbery_succeeded
        # logs (list)
        # open, close
        # spawn_prob, min_per_task, robbery_prob, robbery_success_prob, robbery_kill_prob, robbery_spawn_prob_boost, robbery_spawn_prob_drop, robbery_spawn_prob_adj_coefficient
        pass

    def log(self, text):
        # Takes a string of text and saves it to the PostOffice's logs list for display in the TUI
        pass

    def should_do_robbery(self):
        # Determines if a robbery should occur now
        # Returns True or False
        pass

    def do_robbery(self):
        # Simulates a robbery
        # Calculates the number of customers are killed by the robbers
        # Before clearing the queue, wait time is added to total wait time
        # robbery_succeeded is randomised and robbery_time is updated to now
        # What occurs is logged
        pass

    def should_spawn_customer(self):
        # Determines if a customer should spawn now
        # Randomises based on the spawn_prob parameter and based on if a robbery has recently occurred
        # the final spawn probability is adj * e^(-t/co)
        # where adj is the maximum boost or drop in spawn probability,
        # t is the time since the last robbery,
        # and co is a coefficient to determine how quickly the spawn probability effects of the robbery subsides
        # Returns True or False
        pass

    def spawn_customer(self):
        # Spawns a customer
        # Updates the total number of customers, and adds a new customer to the queue
        # If the queue was empty, the customer's exit time is determined
        # The events are logged
        pass

    def should_customer_leave(self):
        # Determines if the customer in front of the queue should leave the post office
        # Returns true or false
        pass

    def customer_leaves(self):
        # A customer leaves
        # total wait time is updated
        # the customer in front of the queue is removed from the queue
        # The events are logged
        pass

    def init_simulation(self):
        # Initialises the simulation
        # The current time is set to the opening time
        pass

    def simulate(self):
        # Simulates the post office until something happens, main loop
        # Returns False when simulation is complete, else True
        pass

    def read_params(self, path):
        # Takes a file path and reads its content, initialising the PostOffice parameters
        pass

if __name__ == "__main__":
    # Main loop to initialise PostOffice and step through simulation using PostOffice.simulate()
    pass


### Main execution
#
# 1. Initialise PostOffice instance.
# 2. Initialise PosttOffice parameters using read_params()
# 3. Step through PostOffice.simulate() iteratively and print its PostOffice.logs to the GUI or terminal
# 4. End simulation
#
### PostOffice simulation execution:
# 1. Check if a customer should be spawned, if so spawn a customer and log it (should_spawn_customer() & spawn_customer())
# 1.1 If a robbery has occurred recently, compute adjusted spawn rate and use that instead
# 2. Check if the customer currently being served should leave, if so the customer leaves and is logged (should_customer_leave() & customer_leaves())
# 3. Check if a robbery should occur, if so conduct the robbery and log it (should_do_robbery() & do_robbery()
# 4. If no more customers and closed, end simulation
# 5. If current time is opening or closing time, log it
