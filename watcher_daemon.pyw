import os
import errno
import time
import datetime


import win32gui
import win32process
import ctypes, ctypes.wintypes
from win32com.client import GetObject


TAKE_SCREENSHOTS = False
INTERVAL = 6 # in seconds
DATA_DIR = "data"
SCREENSHOTS_DIR = "screenshots"
ENTRIES_FILENAME = "entries.txt"
FIELD_SEPARATOR = " | "

def make_dir(path):
    """Equivalent to "mkdir -p".
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno == errno.EEXIST:
            pass
        else:
            raise

def get_day_dir(date):
    """Return the path of the directory corresponding to \"date\""""
    return "{:d}-{:d}-{:d}".format(date.year, date.month, date.day)

def get_entries_file(date):
    """Return the path of the entries file corresponding to \"date\""""
    return os.path.join(DATA_DIR, get_day_dir(date), ENTRIES_FILENAME)


class WindowsInfo:
    def __init__(self):
        # Required for consulting idle time.
        self.liinfo = type("LASTINPUTINFO" \
            , (ctypes.Structure,) \
            , {'_fields_': [('cbSize', ctypes.wintypes.UINT) \
            , ('dwTime', ctypes.wintypes.DWORD)]} \
            )()

        self.liinfo.cbSize = ctypes.sizeof(self.liinfo)

    def get_idle_time(self):
        """Return the number of seconds since last mouse or keyboard action."""
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self.liinfo))
        current_tick = ctypes.windll.kernel32.GetTickCount()
        return (current_tick - self.liinfo.dwTime) / 1000.0

    def get_active_window_and_process(self):
        """Returns the title of the active window and its process."""
        window = win32gui.GetForegroundWindow()

        if window == 0:
            return (0, 0)

        window_name = win32gui.GetWindowText(window).replace("\n", " ")
        
        pid = win32process.GetWindowThreadProcessId(window)[1]

        for process in GetObject("winmgmts:").InstancesOf("Win32_Process"):
            if int(process.Properties_("ProcessId").Value) == int(pid):
                return window_name, process.Properties_("Name").Value


def take_screenshot(date, timestamp):
    """Save a full screenshot of the desktop."""
    import ImageGrab
    screenshot = ImageGrab.grab()
    path = os.path.join(DATA_DIR, get_day_dir(date), SCREENSHOTS_DIR)
    make_dir(path)
    screenshot.save(os.path.join(path, str(int(timestamp)) + ".png"))

last_windows = []

def start():
    """Start the main loop watching and recording user activity."""
    make_dir(DATA_DIR)

    # Sorry *nix and Mac folks. If you want to help, send me a message
    info = WindowsInfo()

    while 1:
        current_time = time.time()
        today = datetime.datetime.today()
        idle_time = info.get_idle_time()

        if idle_time <= INTERVAL and TAKE_SCREENSHOTS:
            take_screenshot(today, current_time)

        active_window_process = info.get_active_window_and_process()
        if not active_window_process:
            continue

        window_name, process_name = active_window_process
        if not window_name:
            continue

        last_windows.append(window_name)
        if len(last_windows) > 10:
            last_windows.pop(0)

        fields = [str(int(current_time)), str(idle_time), process_name, window_name]
        entry = FIELD_SEPARATOR.join([field for field in fields])

        make_dir(os.path.join(DATA_DIR, get_day_dir(today)))
        with open(get_entries_file(today), "a") as file:
            file.write(entry + "\n")

        # sleep for INTERVAL minus the time we spent committing the entry
        time.sleep(INTERVAL - (time.time() - current_time))

if __name__ == "__main__":
    from tray import tray
    tray('Watcher Daemon', 'report.ico')
    from simpleserver import serve
    serve(last_windows, port=2342)

    try:
        start()
    except Exception as e:
        import traceback
        traceback.print_exc(file=open("error_log.txt", "a"))
