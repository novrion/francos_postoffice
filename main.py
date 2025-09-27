from tui import * # Useful TUI functions
from postoffice import * # Franco's Post Office simulation logic
import curses

# Min and max screen dimensions
MIN_H = 30
MIN_W = 100

# Stage indexes
STAGE_PARAMETER_SELECTION = 0
STAGE_SIMULATION = 1
STAGE_STATISTICS = 2

def init_select_parameters(scr, init):
    # Takes screen and init (if the screen should be (re)drawn)
    # Draws the static parts of the parameter selection screen if init=True
    # Returns the y pos where the text of init_select_parameters() stops

    h, w = scr.getmaxyx()
    instructions = "Every minute a customer may enter Francos post office with a randomised number of errands. If the queue is empty Madame Franco, who runs the office, will work on the customer's errands right away. Otherwise the customer will enter the queue. When Franco has completed a customer's errands the customer leaves. Sometimes the post office is robbed. Franco tries to fight off the robber with her black belt in karate. Depending on the success of the robbery the post office receives a PR boost or drop (customers are more or less likely to enter). Adjust the parameters and start the simulation using the arrow keys to cycle and SPACE to select. Then step through the simulation using the SPACE key. The statistics of the simulation will be displayed at the end of the simulation."

    # Do not redraw but simulate to return y pos
    if not init:
        return M+draw_box(scr, 1, 0, h-2, w-1, text=instructions, init=False)

    # (re)draw
    scr.clear()
 
    draw_msg(scr, "Press Q to quit")
    text_end_y = draw_box(scr, 1, 0, h-2, w-1, title="FRANCO'S POST OFFICE", text=instructions)
    
    text = "Cycle: ↑↓ | Select/Deselect: <SPACE> | Submit: <ENTER>"
    scr.addstr(text_end_y+M, (w - len(text)) // 2, text)

    scr.refresh()

    return text_end_y+M

def select_parameters(scr, key, postoffice, select_idx, init):
    # Takes screen, last pressed key, PostOffice, menu selection index, and init (if the sreen should be (re)drawn)
    # Draws the static and dynamic parts of the parameter selection screen
    # Allows the user to select menu items and alter parameters
    # Returns true if simulation should start, else False

    # Draw static parts of screen
    text_end_y = init_select_parameters(scr, init)

    h, w = scr.getmaxyx()
    param_names = PostOffice.get_param_names()
    params = postoffice.get_params()
    
    # Normalise selection index
    select_idx %= len(params) + 1

    # Unselected parameters
    for i in range(len(params)):
        if i == select_idx:
            continue
        scr.addstr(text_end_y+M+i, M, f"{param_names[i]}: {params[i]}")
 
    # Start simulation option
    y = text_end_y+M+len(params)+1
    x = M
    text = "START SIMULATION"
    if select_idx == len(params):
        scr.addstr(y, x, text, curses.color_pair(1))
        if key == ' ':
            return True
    else:
        scr.addstr(y, x, text)

    # Selected parameter
    if select_idx != len(params):
        y = text_end_y+M+select_idx
        name = param_names[select_idx]
        value = params[select_idx]

        scr.addstr(y, x, f"{name}: {value}", curses.color_pair(1))

        # User wants to modify parameter
        if key == ' ':
            scr.addstr(y, x + len(name) + 1, ' ' * (w-(x+len(name)+5*M)))
            inp = take_user_input(scr, y, x + len(name) + 2, 10)

            # No user input
            if inp == None:
                scr.addstr(y, x, f"{name}: {value}", curses.color_pair(1))
                return False

            # Assert valid input
            valid, err = PostOffice.assert_valid_param(inp, param_names[select_idx])
            if valid:
                scr.addstr(y, x, f"{name}: {inp}", curses.color_pair(1))
                postoffice.update_param(param_names[select_idx], inp)
                return False

            # Invalid input
            scr.addstr(y, x, f"{name}: {value}", curses.color_pair(1))
            scr.addstr(y, x + len(f"{name}: {value}"), f" ({err})")

    return False

def init_simulate(scr, init):
    # Takes screen and init (if the screen should be (re)drawn)
    # Draws the static parts of the simulation screen if init=True
    # Returns the y pos where the init_simulate() text stops

    h, w = scr.getmaxyx()

    # Don't redraw but simulate to return y pos
    if not init:
        return M+draw_box(scr, 1, 0, h-2, w-1, init=False)

    # (re)draw
    scr.clear()

    draw_msg(scr, "Press Q to quit")
    text_end_y = draw_box(scr, 1, 0, h-2, w-1, title="SIMULATION")

    text = "Press <SPACE> to simulate"
    scr.addstr(text_end_y, (w - len(text)) // 2, text)
    scr.addstr(text_end_y+M, M, "LOGS")

    scr.refresh()
    return text_end_y+M

def simulate(scr, key, postoffice, init):
    # Takes screen, last pressed key, PostOffice and init (if the screen's static parts should be (re)drawn)
    # Draws the simulation screen and its logs
    # Returns True if simulation ended else False

    # Initialise static parts of screen
    text_end_y = init_simulate(scr, init)

    h, w = scr.getmaxyx()

    # Call simulation logic
    if key == ' ':
        postoffice.simulate()

    # Display logs
    y = text_end_y+M
    x = M
    n_logs = min(len(postoffice.logs), h-(y+3*M))
    logs = postoffice.logs[-n_logs:]
    for i in range(len(logs)):
        scr.addstr(y+i, x, ' ' * (w-3*M))
        scr.addstr(y+i, x, logs[i])

    # End message
    if postoffice.end:
        scr.addstr(y+len(logs)+M, x, "End of simulation. Press C to continue...")
        if key in ['c', 'C']:
            return True

    scr.refresh()
    return False

def statistics(scr, postoffice, init):
    # Takes a screen, PostOffice, and init (if the statistics screen should (re)initialise)
    # (re)draws end of simulation statistics screen if init=True

    # Don't redraw screen
    if not init:
        return

    h, w = scr.getmaxyx()
    scr.clear()

    # Quit message and box
    draw_msg(scr, "Press Q to quit")
    text_end_y = draw_box(scr, 1, 0, h-2, w-1, title="Franco's Post Office")

    # Statistics
    y = text_end_y
    scr.addstr(y, M, "END OF SIMULATION STATISTICS")
    scr.addstr(y+M, M, f"Number of customers: {postoffice.n_customers}")
    scr.addstr(y+M+1, M, f"Total customer wait time: {postoffice.tot_wait_time} min")
    if postoffice.n_customers > 0:
        scr.addstr(y+M+2, M, f"Average wait time per customer: {round(postoffice.tot_wait_time / postoffice.n_customers, 2)} min")

def run_tui(stdscr):
    # Main event loop
    # Takes a screen and returns when the program is complete
 
    curses.init_pair(1, 0, 15) # Initialise Curses color
    curses.curs_set(0) # Hide cursor
    postoffice = PostOffice()
    last_h, last_w = stdscr.getmaxyx() # Last tick's screen dimensions
    stage = STAGE_PARAMETER_SELECTION
    init = True # If the screen should initialise (stage hasn't been drawn to screen yet)
    key = None # Most recently pressed key
    select_idx = 0 # Selected option index for parameter selection

    while True:

        # Quit
        if key in ['q', 'Q']:
            return

        # Screen too small (error message)
        if not assert_scr_size(stdscr, MIN_H, MIN_W):
            continue

        # Check if screen sized changed
        h, w = stdscr.getmaxyx()
        screen_changed = (last_h != h or last_w != w)
        last_h = h
        last_w = w


        if stage == STAGE_PARAMETER_SELECTION:

            # Cycle menu
            if key == "KEY_UP":
                select_idx -= 1
            elif key == "KEY_DOWN":
                select_idx += 1

            if select_parameters(stdscr, key, postoffice, select_idx, screen_changed or init):
                stage = STAGE_SIMULATION
                init = True
                continue
            init = False


        elif stage == STAGE_SIMULATION:
            if simulate(stdscr, key, postoffice, screen_changed or init):
                stage = STAGE_STATISTICS
                init = True
                continue
            init = False


        elif stage == STAGE_STATISTICS:
            statistics(stdscr, postoffice, screen_changed or init)
            init = False


        # Get key input
        key = stdscr.getkey()

        stdscr.refresh()

if __name__ == "__main__":
    # Curses wrapper initialises screen and passes it to run_tui
    curses.wrapper(run_tui)
