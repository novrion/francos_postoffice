from postoffice import PostOffice
from gui import GUI
import curses

def start_gui(stdscr):
    # A secondary wrapper to initialise one GUI and PostOffice object and start simulation
    # Also initialises another color to be used when drawing text to the parameter selection UI
    # The secondary wrapper is necessary due to how the Curses library wrapper() behaves
    # Another option would be to not have a GUI class and directly pass the Curses screen to GUI.run()
    # and construct the PostOffice inside GUI.run().
    # But due to the depths of the TUI application, class variables like GUI.key are very convenient

    postoffice = PostOffice()

    gui = GUI(stdscr)
    gui.run(postoffice)

if __name__ == "__main__":
    # Initialises a Curses screen and passes it to start_gui

    curses.wrapper(start_gui)
