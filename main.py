import random
import math
import time
import textwrap
import curses
from curses.textpad import rectangle

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
        # Randomises the number of tasks the customer needs help completing
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

        self.logs = []

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

    def init_simulation(self):
        # Initialises the simulation
        # The current time is set to the opening time

        self.time = self.open

    def simulate(self):
        # Simulates the post office until something happens
        # Returns False when simulation is complete, else True

        update = False
        while not update:

            # End of simulation (past closing and no more customers)
            if self.time > self.close and not self.queue:
                return False

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
                return True

            # New customer
            if self.should_spawn_customer():
                update = True
                self.spawn_customer()

            # Customer leaves
            if self.should_customer_leave():
                update = True
                self.customer_leaves()

            self.time += 1

        return True

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
            self.open,
            self.close,
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

class GUI:
    # A class that wraps the Curses TUI over the PostOffice class
    # Used to create a user interface for the simulation logic of the PostOffice class
    # Contains a curses screen variable (scr) to manipulate the UI, a key (the last keyboard input of the user), and fixed helper variables specifying coordinates of the UI

    def __init__(self, scr):
        # Takes a Curses screen object and constructs a GUI object

        self.scr = scr # Curses screen
        self.key = None # Current user input

        self.dy_instructions = 12 # Lower y pos of instructions in stage 0

    def draw_box(self, uly, ulx, dry, drx, title=None, text=None):
        # Takes uly (up left y), ulx (up left x), dry (down right y), drx (down right x) coordinates
        # (these specify the upper left corner and bottom right corner of the box)
        # and draws a box to scr with optional title and text
        # Text is wrapped and cut off if it exceeds the box limits

        rectangle(self.scr, uly, ulx, dry, drx)

        if text:
            w = drx - ulx
            lines = textwrap.wrap(text, width=w-3)
            for i in range(len(lines)):
                if uly+2+i >= dry:
                    break
                self.scr.addstr(uly+2+i, ulx+2, lines[i])

        if title:
            title = f"  {title}  "
            self.scr.addstr(uly, (drx + ulx - len(title)) // 2, title)

    def draw_quit_msg(self):
        # Draws a quit message to the top left corner of the scr object

        self.scr.addstr(0, 0, "Press Q to EXIT")

    def init_select_params(self):
        # Initialises the parameter selection UI
        # Draws everything except the options selectable by the user (draws everything static)
        # Refreshes the screen finally

        h, w = self.scr.getmaxyx()

        # Instructions
        instructions = "Every minute a customer may enter Francos post office with a randomised number of errands. If the queue is empty Madame Franco, who runs the office, will work on the customer's errands right away. Otherwise the customer will enter the queue. When Franco has completed a customer's errands the customer leaves. Sometimes the post office is robbed. Franco tries to fight off the robber with her black belt in karate. Depending on the success of the robbery the post office receives a PR boost or drop (customers are more or less likely to enter). Adjust the parameters and start the simulation using the arrow keys to cycle and SPACE to select. Then step through the simulation using the SPACE key. The statistics of the simulation will be displayed at the end of the simulation."
        self.draw_box(2, 0, self.dy_instructions, w-1, title="FRANCO'S POST OFFICE", text=instructions)
        self.draw_quit_msg()

        # Parameters
        self.draw_box(self.dy_instructions+1, 0, h-2, w-1, title="Parameters")

        text = "Cycle: ↑↓ | Select/Deselect: <SPACE> | Submit: <ENTER>"
        self.scr.addstr(self.dy_instructions+2, ((w - len(text)) // 2), text)

        self.scr.refresh()

    def modify_param(self, y, x, original_param, param_name):
        # Takes the y and x coordinate of a parameter value in the parameter selection UI
        # and the original parameter value and name
        # Takes user input continuously until the user enters <SPACE> or submits a valid parameter input with the carriage return
        # On submission, the entered parameter input is determined valid or invalid
        # If valid, the parameter is returned, else the loop continues
        # If <SPACE> is pressed, None is returned, signaling no new parameter modification

        param = ""

        while True:
            self.key = self.scr.getkey()

            # Submit input
            if self.key == "\n":

                # Check if input is valid parameter
                valid, err_str = PostOffice.assert_valid_param(param, param_name)
                if valid:
                    self.scr.addstr(y, x, " " * 40)

                    # "Normalise" time, i.e 05:05 -> 5:05
                    if param_name in ["open", "close"]:
                        param = time_str(time_int(param))

                    return param

                # Write error message and return None
                self.scr.addstr(y, x, " " * 40)
                self.scr.addstr(y, x, f"{original_param} ({err_str})")
                return None

            # Exit
            elif self.key == " ":
                self.scr.addstr(y, x, " " * 40)
                return None

            # Backspace
            elif len(self.key) == 1 and ord(self.key) == 127: #self.key == "KEY_BACKSPACE"
                if len(param) > 0:
                    param = param[:-1]
                    self.scr.addstr(y, x, " " * 40)
                    self.scr.addstr(y, x, param)
            
            # Input new character
            elif self.key.isalpha() or self.key.isdigit() or self.key in [':', '.']:
                if len(param) < 10:
                    param += self.key
                    self.scr.addstr(y, x, " " * 40)
                    self.scr.addstr(y, x, param) 

    def select_params(self, select_idx, postoffice):
        # The main update function of the parameter selection UI
        # Takes the current selection index of the menu and a PostOffice object
        # and draws the selectable parameters and the "START SIMULATION" selection
        # If "START SIMULATION" is slelected True is returned, else False is returned
        # If a parameter is selected, the modify_param() and update_param() functions handle
        # taking user input and updating the parameter, ensuring user input is valid

        param_names = PostOffice.get_param_names()
        uy = self.dy_instructions+5
        x = 2

        select_idx %= len(param_names) + 1

        for i in range(len(param_names)):
            text = f"{param_names[i]}: "
            val_str = f"{time_str(postoffice.get_params()[i]) if i < 2 else postoffice.get_params()[i]}"

            if i == select_idx:
                self.scr.addstr(uy+i, x, text + val_str, curses.color_pair(1))

                if self.key == " ":
                    self.scr.addstr(uy+i, x, text + " " * 40)
                    self.scr.move(uy+i, x+len(text))

                    new_val_str = self.modify_param(uy+i, x+len(text), val_str, param_names[i])
                    if new_val_str != None:
                        postoffice.update_param(param_names[i], new_val_str)

                    self.scr.addstr(uy+i, x, text + f"{new_val_str if new_val_str else val_str}", curses.color_pair(1))

            else:
                self.scr.addstr(uy+i, x, text + val_str)

        text = "START SIMULATION"
        if select_idx == len(param_names):
            self.scr.addstr(uy+len(param_names)+2, x, text, curses.color_pair(1))
            if self.key == " ":
                return True
        else:
            self.scr.addstr(uy+len(param_names)+2, x, text)

        return False

    def init_simulation(self, postoffice):
        # Takes a PostOffice object and initialises simulation stage of the UI and the PostOffice simulation
        # Initialising the UI contains drawing all static text of the UI
        # Finally refreshes the screen to display the new UI

        postoffice.init_simulation()

        h, w = self.scr.getmaxyx()
        self.draw_box(2, 0, h-2, w-1, title="Franco's Post Office")
        self.draw_quit_msg()

        text = "Press <SPACE> to simulate"
        self.scr.addstr(3, (w - len(text)) // 2, text)

        self.scr.addstr(5, 4, "LOGS")

        self.scr.refresh()

    def simulate(self, postoffice):
        # The main simulation function of the simulation stage UI
        # Takes a PostOffice object and simulates, writing all logs from the simulation to the screen
        # Simulation stops at every minute new logs are written
        # Simulation steps forward from the user entering the <SPACE> key
        # If the simulation is complete, True is returned, else False

        end = not postoffice.simulate()

        h, w = self.scr.getmaxyx()
        y = 5
        x = 4

        # Display logs
        n_logs = min(len(postoffice.logs), h-15)
        logs = postoffice.logs[-n_logs:]
        for i in range(len(logs)):
            self.scr.addstr(y+2+i, x, " " * (w-5))
            self.scr.addstr(y+2+i, x, logs[i])

        if end:
            self.scr.addstr(y+2+len(logs)+2, x, "End of simulation. Press any key to continue.")
            self.scr.refresh()
            self.key = self.scr.getkey()

        return end

    def show_statistics(self, postoffice):
        # Draws the static statistics UI screen with a summary of the simulation's statistics
        # Takes a PostOffice object and displays its simulation statistics
        # Finally refreshes scr

        h, w = self.scr.getmaxyx()

        # Box and quit message
        self.draw_box(2, 0, h-2, w-1, title="Franco's Post Office")
        self.draw_quit_msg()

        # Text
        self.scr.addstr(4, 4, "END OF SIMULATION STATISTICS")
        self.scr.addstr(6, 4, f"Number of customers: {postoffice.n_customers}")
        self.scr.addstr(7, 4, f"Total customer wait time: {postoffice.tot_wait_time} min")
        if postoffice.n_customers > 0:
            self.scr.addstr(8, 4, f"Average wait time per customer: {round(postoffice.tot_wait_time / postoffice.n_customers, 2)} min")

        self.scr.refresh()

    def run(self, postoffice):
        # The main TUI loop
        # Takes a PostOffice object and simulates the post office integrated into the Curses TUI
        # Takes user input to forward the simulation and refreshes the screen when necessary

        stage = 0 # Stage of GUI
        select_idx = 0 # Selection index

        self.scr.clear()
        self.init_select_params()

        while True:

            if self.key == "q":
                return

            # parameter selection stage
            if stage == 0:

                if self.key == "KEY_DOWN":
                    select_idx += 1
                elif self.key == "KEY_UP":
                    select_idx -= 1

                start = self.select_params(select_idx, postoffice)
                if start:
                    stage += 1
                    self.scr.clear()
                    self.init_simulation(postoffice)

            # Simulation stage 
            elif stage == 1:

                # Continue simulation
                if self.key == " ":

                    end = self.simulate(postoffice)
                    if end:
                        stage += 1
                        self.scr.clear()
                        self.show_statistics(postoffice)


            # Refresh screen only if changes were made
            if self.key != None:
                self.scr.refresh()
                self.key = None

            # Get user input
            self.key = self.scr.getkey()

def run_gui(stdscr):
    # A secondary wrapper to initialise one GUI and PostOffice object and start simulation
    # Also initialises another color to be used when drawing text to the parameter selection UI
    # The secondary wrapper is necessary due to how the Curses library wrapper() behaves
    # Another option would be to not have a GUI class and directly pass the Curses screen to GUI.run()
    # and construct the PostOffice inside GUI.run().
    # But due to the depths of the TUI application, class variables like GUI.key are very convenient

    # Initialise color
    curses.init_pair(1, 0, 15)

    postoffice = PostOffice()

    gui = GUI(stdscr)
    gui.run(postoffice)

if __name__ == "__main__":
    # Initialises a Curses screen and passes it to run_gui

    curses.wrapper(run_gui)
