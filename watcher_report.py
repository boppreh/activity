import datetime
import os
from itertools import izip_longest
from collections import Counter

import watcher_daemon

MAX_IDLE_TIME = 5 * 60  # in seconds

PERIODS_NAMES = ["Today", "Yesterday", "Past Week (average)"]
PERIODS = [(0, 1), (1, 2), (2, 9)]

# "Sublime Text     1:08"
SUMMARY_PROCESS_FORMAT = "{:<15s} {:s}"
TIME_FORMAT = "{:.0%} - {:>2.0f}:{:02.0f}"
TIME_FORMAT_SHORT = "{:.0%}"
MAX_NAME_LENGTH = 15

COLUMN_FORMAT = "{:^" + str(80 / len(PERIODS)) + "s}"

USE_PROCESS_NAME = True
FILTER = ""


def format_process_name(process_name):
    """Convert a process name to a more readable format.

    Example:
        "sublime_text-2-blahblahblah.exe" -> "Sublime Text 2 blahblah...
    """
    name = os.path.splitext(process_name)[0] \
           .replace("_", " ") \
           .replace("-", " ") \
           .title()

    if len(name) >= MAX_NAME_LENGTH:
        name = name[:MAX_NAME_LENGTH - 3] + "..."

    return name

def matches(title, process_name, substrings):
    """Returns True if title and process_name contains all space
    separated words in substrings.
    """
    title = title.lower()
    process_name = process_name.lower()

    for string in substrings.lower().split(" "):
        if not (string in title or string in process_name):
            return False

    return True

def get_active_names_counter(entries):
    """Given a list of string entries, parses them, removes sequences of
    inactvity longer than MAX_IDLE_TIME seconds and return the number
    of occurences of each process.
    """
    total_counter = Counter()
    sequence_counter = Counter()
    # Idle time of the previous entry. If the next entry has a smaller
    # idle time, it's a different inactvity sequence.
    prev_idle_time = 0

    for line in entries:
        # example line: "1311169041 | 1.016 | explorer.exe | data"
        str_idle_time, process_name, title = line.split(" | ", 3)[1:]
        idle_time = float(str_idle_time)

        if USE_PROCESS_NAME:
            name = process_name
        else:
            name = title

        if idle_time <= prev_idle_time:
            # It's a new sequence, commit the temporary counter.
            total_counter += sequence_counter
            sequence_counter.clear()

        if idle_time > MAX_IDLE_TIME:
            # This sequence is too long and shouldn't be counted.
            sequence_counter.clear()
        elif matches(title, process_name, FILTER):
            sequence_counter[name] += 1

    # Sequence counters are only commited when a new sequence starts,
    # so there might still be valid entries there.
    return total_counter + sequence_counter

def get_date_period_counters(start, end):
    """Return the number of active occurences of each process in each day
    in a certain date period in relation to today.
    """
    for day in range(start, end):
        date = datetime.datetime.today() - datetime.timedelta(day)

        try:
            with open(watcher_daemon.get_entries_file(date)) as entries:
                entries = [entry.decode("UTF-8") for entry in entries]
                yield get_active_names_counter(entries)
        except IOError:
            # There's nothing recorded on that day.
            continue

def get_time_string(seconds, total_seconds):
    """Returns a formatted string with hours, minutes and percentage
    of total time.
    """
    all_minutes = seconds / 60
    minutes = int(all_minutes % 60)
    hours = int(all_minutes / 60)
    # If-else is to guard against divisions by zero.
    percentage = seconds / total_seconds if total_seconds else 1
    if not hours and not minutes:
        return TIME_FORMAT_SHORT.format(percentage)
    else:
        return TIME_FORMAT.format(percentage, hours, minutes)

def get_summary(start, end):
    """Return a list of tuples with the formatted process name and mean time
    spent on the top processes during the specified period. The first value
    is the total and includes the number of entries in the title.

    Ex: [("Total (150 entries)", "4:50"), ("Opera", "2:30"), ("Explorer",
    "0:08"), ...] 
    """

    counters_by_day = list(get_date_period_counters(start, end))
    summed_counters = sum(counters_by_day, Counter())

    time_multiplier = float(watcher_daemon.INTERVAL) / len(counters_by_day)

    total_title = "Total ({:d} entries)".format(len(summed_counters))
    total_seconds = sum(summed_counters.values()) * time_multiplier
    total_time = get_time_string(total_seconds, total_seconds)

    yield (total_title, total_time)

    for name, count in summed_counters.most_common():
        if USE_PROCESS_NAME:
            name = format_process_name(name)

        seconds = count * time_multiplier
        time = get_time_string(seconds, total_seconds)

        yield (name, time)
        

if __name__ == "__main__":
    print "".join([COLUMN_FORMAT.format(name) for name in PERIODS_NAMES])
    print ""

    summaries = [get_summary(start, end) for start, end in PERIODS]
    for columns in izip_longest(*summaries, fillvalue=""):
        line = ""

        for entry in columns:
            if entry:
                text = SUMMARY_PROCESS_FORMAT.format(*entry)
            else:
                text = ""
            
            line += COLUMN_FORMAT.format(text)

        print line
