import random
import math
import time
import textwrap
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
    return f"{hours}:{formatted_minutes}"

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

    def get_params(self):
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

        if param_name in ["open", "close"]:
            try:
                t = time_int(param)
                if t < 0:
                    return (False, f"{param_name} should be 24h format 'xx:yy'")
                return (True, "")
            except ValueError as err:
                return (False, f"{param_name} should be 24h format 'xx:yy'")

        elif param_name in ["spawn_prob", "robbery_prob", "robbery_success_prob", "robbery_kill_prob", "robbery_spawn_prob_boost", "robbery_spawn_prob_drop"]:
            try:
                var = float(param)
                if var > 1 or var < 0:
                    return (False, f"0 <= {param_name} <= 1.")
                return (True, "")
            except:
                return (False, f"0 <= {param_name} <= 1.")

        elif param_name in ["min_per_task"]:
            try:
                var = int(param)
                if var < 1:
                    return (False, f"integer {param_name} > 0.")
                return (True, "")
            except:
                return (False, f"integer {param_name} > 0.")

        elif param_name in ["robbery_spawn_prob_adj_coefficient"]:
            try:
                var = float(param)
                if var <= 0:
                    return (False, f"{param_name} > 0")
                return (True, "")
            except:
                return (False, f"{param_name} > 0")

        return False

    def log(self, text):
        self.logs.append(text.strip())

    def should_do_robbery(self):
        return self.time < self.close and random.random() <= self.robbery_prob

    def do_robbery(self):
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
        if self.time >= self.close:
            return False
        
        spawn_prob = self.spawn_prob
        if self.robbery_time:
            time_diff = self.time - self.robbery_time
            prob_adj = -self.robbery_spawn_prob_drop if self.robbery_succeeded else self.robbery_spawn_prob_boost
            spawn_prob += prob_adj * pow(math.e, -time_diff/self.robbery_spawn_prob_adj_coefficient)

        return random.random() <= spawn_prob

    def spawn_customer(self):
        self.n_customers += 1
        new_customer = Customer(self.n_customers, self.time)
        if not self.queue:
            new_customer.set_exit_time(self.time, self.min_per_task)
            self.log(f"{time_str(self.time)} Customer {new_customer.id} enters the post office and is served immediately")
        else:
            self.log(f"{time_str(self.time)} Customer {new_customer.id} enters the post office and stands in line as no. {len(self.queue) + 1}")
        self.queue.append(new_customer)

    def should_customer_leave(self):
        return self.queue and self.queue[0].exit_time == self.time

    def customer_leaves(self):
        leaving_customer = self.queue.pop(0)
        self.tot_wait_time += leaving_customer.get_wait_time(self.time)
        if self.queue:
            self.queue[0].set_exit_time(self.time, self.min_per_task)
            self.log(f"{time_str(self.time)} Customer {leaving_customer.id} leaves and customer {self.queue[0].id} is served")
        else:
            self.log(f"{time_str(self.time)} Customer {leaving_customer.id} leaves")

    # Returns False when siulation is complete, else True
    def simulate(self, scr, initialised):
        height, width = scr.getmaxyx()
        if not initialised:
            scr.clear()

            draw_box(scr, 2, 0, height-2, width-1, title="Franco's Post Office")
            draw_quit_note(scr)

            text = "Press <SPACE> to simulate"
            scr.addstr(3, (width - len(text)) // 2, text)

            scr.refresh()

            self.time = self.open

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

        # Draw logs to screen
        y = 5
        x = 4
        scr.addstr(y, x, "Logs")
        n_logs = min(len(self.logs), height-12)
        logs = self.logs[-n_logs-1:]
        for i in range(len(logs)):
            scr.addstr(y+2 + i, x, " " * (width-5))
            scr.addstr(y+2 + i, x, logs[i])

        return True

def draw_box(scr, sy, sx, ey, ex, text=None, title=None):
    # Draws a box with an optional title and text inside on scr
    # Takes the screen, top left y pos, top left x pos, bottom right y pos, bottom right x pos and optional text and title args

    # Draw box
    rectangle(scr, sy, sx, ey, ex)

    # Text
    w = ex - sx - 4
    if text:
        lines = textwrap.wrap(text, width=w+1)
        for i in range(len(lines)):
            if sy+2+i >= ey:
                break
            scr.addstr(sy+2+i, sx+2, lines[i])

    # Title
    if title:
        title = f"  {title}  "
        scr.addstr(sy, (ex + sx - len(title)) // 2, title)

def draw_quit_note(scr):
    scr.addstr(0, 0, "Type Q to QUIT")

def modify_param(scr, y, x, postoffice, param_name, original_param_value):
    param = ""
    while True:
        key = scr.getkey()
        if key == "\n":

            # Check if input is valid parameter
            valid, err_str = PostOffice.assert_valid_param(param, param_name)
            if valid:
                scr.addstr(y, x, param)
                break

            # Write error message
            scr.addstr(y, x, f"{original_param_value} ({err_str})")
            scr.refresh()
            time.sleep(3)
            return None

        # Exit
        if key == "KEY_ESCAPE":
            return None

        # Backspace
        elif key == "KEY_BACKSPACE": # ord(key) == 127
            if len(param) > 0:
                param = param[:-1]
                scr.addstr(y, x, " " * 40)
                scr.addstr(y, x, param)

        # Input new character
        elif key.isalpha() or key.isdigit() or key in [':', '.']:
            #scr.refresh()
            if len(param) < 10:
                param += key
                scr.addstr(y, x, " " * 40)
                scr.addstr(y, x, param)

    if param_name == "open":
        postoffice.open = time_int(param)
    elif param_name == "close":
        postoffice.close = time_int(param)
    elif param_name == "spawn_prob":
        postoffice.spawn_prob = float(param)
    elif param_name == "min_per_task":
        postoffice.min_per_task = int(param)
    elif param_name == "robbery_prob":
        postoffice.robbery_prob = float(param)
    elif param_name == "robbery_success_prob":
        postoffice.robbery_success_prob = float(param)
    elif param_name == "robbery_kill_prob":
        postoffice.robbery_kill_prob = float(param)
    elif param_name == "robbery_spawn_prob_boost":
        postoffice.robbery_spawn_prob_boost = float(param)
    elif param_name == "robbery_spawn_prob_drop":
        postoffice.robbery_spawn_prob_drop = float(param)
    elif param_name == "robbery_spawn_prob_adj_coefficient":
        postoffice.robbery_spawn_prob_adj_coefficient = float(param)

    return param

def select_parameters(scr, postoffice, initialised, cycle_idx, key):
    cycle_idx %= (len(postoffice.get_params()) + 1)

    height, width = scr.getmaxyx()
    ey_title = 4
    ey_instructions = ey_title+1 + 11
    ey_params = height-2

    # Initialisation
    if not initialised:
        initialised = True
        scr.clear()

        # Quit note
        draw_quit_note(scr)

        # Title
        text = "FRANCO'S POST OFFICE"
        sx = (width-1 -len(text)) // 2 - 2
        ex = sx + len(text) + 3
        draw_box(scr, 0, sx, ey_title, ex, text=text)

        # Instructions
        instructions = "Franco's Post Office simulates Madame Franco's post office. Every minute the store is open a customer may enter. Every customer has a randomised number of tasks that he or she needs to complete. If there are no other customers in the store Franco will get to work on the new customer's tasks right away. Otherwise the customer enters the queue. When Franco has completed all of a customer's tasks the customer leaves. Rarely the post office is robbed. Franco usually manages to fight off the robbers with her black belt in karate. Then the post office gets a PR boost. This increases the probability that customers visit her post office. Unfortunately, sometimes the robbers succeed. This decreases the probability that customers enter the post office. Adjust the parameters of the simulation and click PLAY to start the simulation. Then step through the simulation by pressing the SPACE key. At the end the statistics of the simulation will be summarised."
        draw_box(scr, ey_title + 1, 0, ey_instructions, width-1, text=instructions, title="Instructions")

        # Parameters
        draw_box(scr, ey_instructions + 2, 0, ey_params, width-1, title="Parameters")

        text = "Cycle: ↑↓ | Select: <SPACE>"
        scr.addstr(ey_instructions +2 +1, ((width - len(text)) // 2), text)

        cycle_idx = 0

        scr.refresh()

    sy = ey_instructions + 5
    x = 2
    for i in range(len(PostOffice.get_param_names())):
        param_name_str = f"{PostOffice.get_param_names()[i]}: "
        param_str = f"{time_str(postoffice.get_params()[i]) if i < 2 else postoffice.get_params()[i]}"
        if i == cycle_idx:
            scr.addstr(sy + i, x, param_name_str + param_str, curses.color_pair(1))
            if key == " ":
                scr.addstr(sy + i, x, param_name_str + " " * 20)
                scr.move(sy + i, x + len(param_name_str))
                new_val = modify_param(scr, sy+i, x+len(param_name_str), postoffice, PostOffice.get_param_names()[i], param_str)
                scr.addstr(sy + i, x, " " * (width - 5))
                scr.addstr(sy + i, x, f"{PostOffice.get_param_names()[i]}: {new_val if new_val != None else param_str}", curses.color_pair(1))
        else:
            scr.addstr(sy + i, x, param_name_str + param_str)

    text = "Start Simulation"
    if cycle_idx == len(PostOffice.get_param_names()):
        scr.addstr(ey_params - 2, width-3 -len(text), text, curses.color_pair(1))
        if key == " ":
            return -1
    else:
        scr.addstr(ey_params - 2, width-3 -len(text), text)

    return cycle_idx

def show_statistics(scr, postoffice):
    height, width = scr.getmaxyx()

    scr.clear()

    draw_box(scr, 2, 0, height-2, width-1, title="Franco's Post Office")
    draw_quit_note(scr)

    scr.addstr(4, 4, "End Of Simulation Statistics")
    scr.addstr(6, 4, f"Number of customers: {postoffice.n_customers}")
    scr.addstr(7, 4, f"Total customer wait time: {postoffice.tot_wait_time} min")
    if postoffice.n_customers > 0:
        scr.addstr(8, 4, f"Average wait time per customer: {round(postoffice.tot_wait_time / postoffice.n_customers, 2)} min")

    scr.refresh()

def run_gui(stdscr):
    curses.init_pair(1, 0, 15) # Initialise selection color for use later

    postoffice = PostOffice()
    stage = 0
    initialised = False
    warning = False
    key = None
    cycle_idx = 0 # For parameter selection

    while stage <= 2:
        height, width = stdscr.getmaxyx()
        if height < 30 or width < 80:
            if warning == False:
                stdscr.clear()
                stdscr.addstr(0, 0, "This application requires a terminal window that is at least 30x80")
                stdscr.refresh()
                warning = True
                initialised = False
            continue
        else:
            warning = False

        if key == "q":
            return

        if stage == 0:

            if key == "KEY_DOWN":
                cycle_idx += 1
            elif key == "KEY_UP":
                cycle_idx -= 1

            cycle_idx = select_parameters(stdscr, postoffice, initialised, cycle_idx, key)
            initialised = True
            if cycle_idx == -1:
                # Parameter selection complete
                stage += 1
                initialised = False
                stdscr.clear()

        elif stage == 1:

            if not initialised or key == " ":
                end_simulation = not postoffice.simulate(stdscr, initialised)
                initialised = True

                if end_simulation:
                    # End of simulation
                    stage += 1
                    show_statistics(stdscr, postoffice)

        # Changes made to the screen?
        if key != None:
            stdscr.refresh()
            key = None

        if initialised:
            key = stdscr.getkey()

wrapper(run_gui)
