import random
import math
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

    # Returns False when siulation is complete, else True
    def simulate(self):
        update = False
        while not update:

            # End of simulation (past closing and no more customers)
            if self.time > self.close and not self.queue:
                # TODO: Show statistics
                return False

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

def select_parameters(scr, postoffice, initialised, cycle_idx, key):
    parameter_names = [
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

    parameters = [
        postoffice.open,
        postoffice.close,
        postoffice.spawn_prob,
        postoffice.min_per_task,
        postoffice.robbery_prob,
        postoffice.robbery_success_prob,
        postoffice.robbery_kill_prob,
        postoffice.robbery_spawn_prob_boost,
        postoffice.robbery_spawn_prob_drop,
        postoffice.robbery_spawn_prob_adj_coefficient,
    ]

    cycle_idx %= (len(parameters) + 1)

    height, width = scr.getmaxyx()
    ey_title = 4
    ey_instructions = ey_title+1 + 11
    ey_params = height-2

    # Initialisation
    if not initialised:
        initialised = True
        scr.clear()

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

        text = "Cycle: <TAB> | Select: <ENTER>"
        scr.addstr(ey_instructions +2 +1, ((width - len(text)) // 2), text)

        cycle_idx = 0

    sy = ey_instructions + 3
    x = 2
    for i in range(len(parameter_names)):
        if i == cycle_idx:
            pass
        else:
            scr.addstr(sy + i, x, f"{parameter_names[i]}: {parameters[i]}")

    text = "Start Simulation"
    if cycle_idx == len(parameter_names):
        pass
        #scr.addstr(ey_params - 2, width-3 -len(text), text)
    else:
        scr.addstr(ey_params - 2, width-3 -len(text), text)

    scr.addstr(ey_instructions + 10, 50, f"{cycle_idx}")

    return cycle_idx

def run_gui(stdscr):
    postoffice = PostOffice()
    stage = 0
    initialised = False
    key = None
    cycle_idx = 0 # For parameter selection

    while stage <= 2:

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

        elif stage == 1:

            if not postoffice.simulate():
                # End of simulation
                stage += 1
                show_statistics()

        else:

            # Quit statistics summary
            if key == curses.KEY_ENTER:
                return

        # Changes made to the screen?
        if key != None:
            stdscr.refresh()
            key = None

        key = stdscr.getkey()


wrapper(run_gui)











#!/usr/bin/env python
#from itertools import cycle
#import curses, contextlib, time
#
#@contextlib.contextmanager
#def curses_screen():
#    """Contextmanager's version of curses.wrapper()."""
#    try:
#        stdscr=curses.initscr()
#        curses.noecho()
#        curses.cbreak()
#        stdscr.keypad(1)
#        try: curses.start_color()
#        except: pass
#
#        yield stdscr
#    finally:
#        stdscr.keypad(0)
#        curses.echo()
#        curses.nocbreak()
#        curses.endwin()
#
#if __name__=="__main__":
#    with curses_screen() as stdscr:
#        c = curses.A_BOLD
#        if curses.has_colors():
#            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
#            c |= curses.color_pair(1)
#
#        curses.curs_set(0) # make cursor invisible
#
#        y, x = stdscr.getmaxyx()
#        for col in cycle((c, curses.A_BOLD)):
#            stdscr.erase()
#            stdscr.addstr(y//2, x//2, 'abc', col)
#            stdscr.refresh()
#            time.sleep(1)
