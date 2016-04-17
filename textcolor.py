import sys

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(30,38)
RESET = 0
GREY = 0


def has_colours(stream):
    """Check if a stream has colors. From Python cookbook, #475186"""

    if not hasattr(stream, "isatty"):
        return False

    if not stream.isatty():
        return False # auto color only on TTYs

    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False


stdout_has_colours = has_colours(sys.stdout)


def textcolor(text, colour=WHITE):
    """Returned colored text if available"""
    if stdout_has_colours:
        return "\x1b[1;%dm" % (colour) + text + "\x1b[0m"
    else:
        return text
