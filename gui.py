import curses
from curses.textpad import rectangle
import textwrap

M = 2 # Margin

def assert_scr_size(scr, min_h, min_w):
    h, w = scr.getmaxyx()
    if h < min_h or w < min_w:
        scr.clear()
        draw_error_msg(scr, f"{min_w}x{min_h} min screen size")
        scr.refresh()
        return False
    return True

def draw_box(scr, uly, ulx, dry, drx, title=None, text=None, init=True):

    # Simulate the box but don't draw it
    if not init:
        if text:
            lines = textwrap.wrap(text, width=(drx-ulx-M-1))
            return uly+M+len(lines)
        return uly+M

    # Actually draw the box
    rectangle(scr, uly, ulx, dry, drx)

    if title:
        title = f"  {title}  "
        scr.addstr(uly, (drx + ulx - len(title)) // 2, title)

    if text:
        lines = textwrap.wrap(text, width=(drx-ulx-M-1))
        for i in range(len(lines)):
            if uly+M+i >= dry:
                break
            scr.addstr(uly+M+i, ulx+M, lines[i])
        return uly+M+len(lines)

    return uly+M

def draw_error_msg(scr, text):
    scr.clear()
    h, w = scr.getmaxyx()
    scr.addstr(0, 0, text[:min(w, len(text))])
    scr.refresh()

def draw_msg(scr, text):
    scr.addstr(0, 0, text)

def take_user_input(scr, y, x, max_len):
    scr.addstr(y, x, ' ' * max_len)
    scr.move(y, x)
    curses.curs_set(1)

    inp = ""
    while True:
        key = scr.getkey()

        # Submit or Exit
        if key in ['\n', ' ']:
            scr.addstr(y, x, ' ' * max_len)
            curses.curs_set(0)
            return (inp if key == "\n" else None)

        # Backspace
        if (len(key) == 1 and ord(key) == 127) or key == "KEY_BACKSPACE":
            if len(inp) > 0:
                inp = inp[:-1]
                scr.addstr(y, x+len(inp), " ")
                scr.move(y, x+len(inp))

        # Input new character
        elif key.isalpha() or key.isdigit() or key in [':', '.']:
            if len(inp) < max_len:
                inp += key
                scr.addstr(y, x, inp)
