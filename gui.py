# The curses documentation has been read for this project: https://docs.python.org/3/library/curses.html

import textwrap
import curses
from curses.textpad import rectangle
from postoffice import PostOffice

MIN_W = 80
MIN_H = 31

class GUI:
    # A class that wraps the Curses TUI over the PostOffice class
    # Used to create a user interface for the simulation logic of the PostOffice class
    # Contains a curses screen variable (scr) to manipulate the UI, a key (the last keyboard input of the user), and fixed helper variables specifying coordinates of the UI

    def __init__(self, scr):
        # Takes a Curses screen object and constructs a GUI object
        
        curses.init_pair(1, 0, 15)


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

        self.scr.clear()
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

    def select_params(self, reinit, select_idx, postoffice):
        # The main update function of the parameter selection UI
        # Takes the current selection index of the menu and a PostOffice object
        # and draws the selectable parameters and the "START SIMULATION" selection
        # If "START SIMULATION" is slelected True is returned, else False is returned
        # If a parameter is selected, the modify_param() and update_param() functions handle
        # taking user input and updating the parameter, ensuring user input is valid

        if reinit:
            self.init_select_params()

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
            self.scr.addstr(uy+len(param_names)+1, x, text, curses.color_pair(1))
            if self.key == " ":
                return True
        else:
            self.scr.addstr(uy+len(param_names)+1, x, text)

        return False

    def init_simulation(self):
        # Takes a PostOffice object and initialises simulation stage of the UI and the PostOffice simulation
        # Initialising the UI contains drawing all static text of the UI
        # Finally refreshes the screen to display the new UI

        self.scr.clear()
        h, w = self.scr.getmaxyx()

        self.draw_box(2, 0, h-2, w-1, title="Franco's Post Office")
        self.draw_quit_msg()

        text = "Press <SPACE> to simulate"
        self.scr.addstr(3, (w - len(text)) // 2, text)
        self.scr.addstr(5, 4, "LOGS")

        self.scr.refresh()

    def simulate(self, reinit, postoffice):
        # The main simulation function of the simulation stage UI
        # Takes a PostOffice object and simulates, writing all logs from the simulation to the screen
        # Simulation stops at every minute new logs are written
        # Simulation steps forward from the user entering the <SPACE> key
        # If the simulation is complete, True is returned, else False

        if reinit:
            self.init_simulation()

        end = False
        if self.key == " ":
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

        self.scr.refresh()

        return end

    def show_statistics(self, reinit, postoffice):
        # Draws the static statistics UI screen with a summary of the simulation's statistics
        # Takes a PostOffice object and displays its simulation statistics
        # Finally refreshes scr

        if not reinit:
            return

        self.scr.clear()
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

    def draw_error_msg(self, text):
        h, w = self.scr.getmaxyx()
        text = f"Minimum {MIN_W}x{MIN_H} terminal required"
        if len(text) >= w:
            text = text[:w-1]
        self.scr.addstr(0, 0, text)

    def run(self, postoffice):
        # The main TUI loop
        # Takes a PostOffice object and simulates the post office integrated into the Curses TUI
        # Takes user input to forward the simulation and refreshes the screen when necessary

        stage = 0 # Stage of GUI (parameter selection (0), simulation (1), and showing statistics (2))
        select_idx = 0 # Selection index (used to highlight options in parameter selection)
        last_h, last_w = self.scr.getmaxyx() # Keeps track of last tick's screen size
        reinit = False # If the screen should be reinitialised due to new screen size

        if last_h >= MIN_H and last_w >= MIN_W:
            self.init_select_params()

        while True:

            h, w = self.scr.getmaxyx()

            # Check if screen dimensions are too small
            if h < MIN_H or w < MIN_W:
                self.scr.clear()
                self.draw_error_msg(f"Minimum {MIN_W}x{MIN_H} terminal required")
                self.scr.refresh()
                continue

            # Check if screen size changed
            if last_h != h or last_w != w:
                reinit = True
                last_h = h
                last_w = w

            # User quits
            if self.key == "q" or self.key == "Q":
                return

            # parameter selection stage
            if stage == 0:

                if self.key == "KEY_DOWN":
                    select_idx += 1
                elif self.key == "KEY_UP":
                    select_idx -= 1

                start = self.select_params(reinit, select_idx, postoffice)
                if start:
                    stage += 1
                    self.init_simulation()

            # Simulation stage
            elif stage == 1:

                end = self.simulate(reinit, postoffice)
                if end:
                    stage += 1
                    self.show_statistics(True, postoffice)

            # End of simulation statistics stage
            elif stage == 2:
                self.show_statistics(reinit, postoffice)

            # Get user input
            self.key = self.scr.getkey()

def start_gui(stdscr):
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

    curses.wrapper(start_gui)
