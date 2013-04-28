activity
========

*Watcher Daemon* and *Watcher Report* are a pair of applications to help you
keep track of where you are spending your time.


Watcher Daemon
--------------

*Watcher Daemon* is a background application that silently records the current
program you are running, along with the current time, window title and last
user input (for calculating away time). This is stored in the `data/` folder
and separated by date. By changing the program source you can enable recording
of screenshots too.


Watcher Report
--------------

*Watcher Report* is a GUI application that shows how you spent the current day,
the previous day and the previous week in the computer, using data recorded by
the Daemon. You can filter by process name and window title to see details.
