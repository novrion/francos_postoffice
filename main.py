from gui import *
from postoffice import *
import curses

MIN_H = 30
MIN_W = 100
STAGE_PARAMETER_SELECTION = 0
STAGE_SIMULATION = 1
STAGE_STATISTICS = 2

def init_select_parameters(scr):
    h, w = scr.getmaxyx()
    scr.clear()

    instructions = "Every minute a customer may enter Francos post office with a randomised number of errands. If the queue is empty Madame Franco, who runs the office, will work on the customer's errands right away. Otherwise the customer will enter the queue. When Franco has completed a customer's errands the customer leaves. Sometimes the post office is robbed. Franco tries to fight off the robber with her black belt in karate. Depending on the success of the robbery the post office receives a PR boost or drop (customers are more or less likely to enter). Adjust the parameters and start the simulation using the arrow keys to cycle and SPACE to select. Then step through the simulation using the SPACE key. The statistics of the simulation will be displayed at the end of the simulation."

    draw_msg(scr, "Press Q to quit")
    text_end_y = draw_box(scr, 1, 0, h-2, w-1, title="FRANCO'S POST OFFICE", text=instructions)
    
    text = "Cycle: ↑↓ | Select/Deselect: <SPACE> | Submit: <ENTER>"
    scr.addstr(text_end_y+M, (w - len(text)) // 2, text)

    scr.refresh()

    return text_end_y+M

def select_parameters(scr, key, postoffice, select_idx):
    text_end_y = init_select_parameters(scr)
    param_names = PostOffice.get_param_names()
    params = postoffice.get_params()
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
            scr.addstr(y, x + len(name) + 1, ' ' * 40)
            inp = take_user_input(scr, y, x + len(name) + 2, 10)

            # No user input
            if inp == None:
                scr.addstr(y, x, f"{name}: {value}", curses.color_pair(1))
                return False

            valid, err = PostOffice.assert_valid_param(inp, param_names[select_idx])
            if valid:
                scr.addstr(y, x, f"{name}: {inp}", curses.color_pair(1))
                postoffice.update_param(param_names[select_idx], inp)
                return False

            # Invalid input
            scr.addstr(y, x, f"{name}: {value} ({err})", curses.color_pair(1))

    return False

def init_simulate(scr):
    h, w = scr.getmaxyx()
    scr.clear()

    draw_msg(scr, "Press Q to quit")
    text_end_y = draw_box(scr, 1, 0, h-2, w-1, title="SIMULATION")

    text = "Press <SPACE> to simulate"
    scr.addstr(text_end_y, (w - len(text)) // 2, text)
    scr.addstr(text_end_y+M, M, "LOGS")

    scr.refresh()
    return text_end_y+M

def simulate(scr, key, postoffice):
    h, w = scr.getmaxyx()
    text_end_y = init_simulate(scr)

    # Call simulation logic
    end = False
    if key == ' ':
        end = not postoffice.simulate()

    # Display logs
    y = text_end_y+M
    x = M
    n_logs = min(len(postoffice.logs), h-(y+3*M))
    logs = postoffice.logs[-n_logs:]
    for i in range(len(logs)):
        scr.addstr(y+i, x, ' ' * (w-3*M))
        scr.addstr(y+i, x, logs[i])

    # End message
    if end:
        scr.addstr(y+len(logs)+M, x, "End of simulation. Press C to continue...")
        scr.refresh()
        get_keys(scr, ['c', 'C'])

    scr.refresh()

    return end

def statistics(scr, postoffice):
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
    curses.init_pair(1, 0, 15)
    curses.curs_set(0)
    postoffice = PostOffice()
    last_h, last_w = stdscr.getmaxyx()
    stage = STAGE_PARAMETER_SELECTION
    key = None
    select_idx = 0

    while True:

        # Quit
        if key in ['q', 'Q']:
            return

        # Screen too small (error message)
        if not assert_scr_size(stdscr, MIN_H, MIN_W):
            continue

        if stage == STAGE_PARAMETER_SELECTION:

            # Cycle menu
            if key == "KEY_UP":
                select_idx -= 1
            elif key == "KEY_DOWN":
                select_idx += 1

            if select_parameters(stdscr, key, postoffice, select_idx):
                stage = STAGE_SIMULATION
                continue

        elif stage == STAGE_SIMULATION:
            if simulate(stdscr, key, postoffice):
                stage = STAGE_STATISTICS
                continue

        elif stage == STAGE_STATISTICS:
            statistics(stdscr, postoffice)


        # Get key input
        key = stdscr.getkey()

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(run_tui)
