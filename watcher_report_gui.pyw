import sys
import traceback
import wx
import wx.lib.mixins.listctrl as listmix

import watcher_report
watcher_report.MAX_NAME_LENGTH = 10000

def show_error():
    message = ''.join(traceback.format_exception(*sys.exc_info()))
    dialog = wx.MessageDialog(None, message, 'Error!', wx.OK|wx.ICON_ERROR)
    dialog.ShowModal()


class SummaryList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, summary):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.InsertColumn(0, "name")
        self.InsertColumn(1, "time", wx.LIST_FORMAT_RIGHT, width=78)

        self.setResizeColumn(0)

        self.update(summary)

    def update(self, summary):
        self.DeleteAllItems()

        for i, entry in enumerate(summary):
            name, time = entry
            
            self.InsertStringItem(i, name)
            self.SetStringItem(i, 1, time)


class PeriodPanel(wx.Panel):
    def __init__(self, parent, title, summary):
        wx.Panel.__init__(self, parent)

        title_text = wx.StaticText(self, label=title)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title_text, 0, wx.BOTTOM, 10)
        #sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)

        self.summary_list = SummaryList(self, summary)
        sizer.Add(self.summary_list, 1, wx.EXPAND | wx.ALL)

        self.SetSizerAndFit(sizer)


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)

        panel = wx.Panel(self)

        periods_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.period_panels = []
        period_tuples = zip(watcher_report.PERIODS_NAMES, \
                            watcher_report.PERIODS)

        for name, period in period_tuples:
            summary = watcher_report.get_summary(*period)
            period_panel = PeriodPanel(panel, name, summary)
            periods_sizer.Add(period_panel, 1, wx.EXPAND | wx.ALL, 5)
            self.period_panels.append(period_panel)

        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filter_sizer.Add(wx.StaticText(panel, -1, "Filter"), 0, wx.RIGHT, 10)
        self.filter_field = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        filter_sizer.Add(self.filter_field, 1, wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(periods_sizer, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(filter_sizer, 0, wx.EXPAND | wx.ALL, 10)

        icon = wx.Icon('report.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        panel.SetSizerAndFit(main_sizer)

        self.SetSizeHints(350, 98)
        self.SetSize((650, 260))

        self.filter_field.SetFocus()
        self.filter_field.Bind(wx.EVT_TEXT_ENTER, self.OnFilter)

    def OnFilter(self, event):
        watcher_report.USE_PROCESS_NAME = self.filter_field.IsEmpty()
        watcher_report.FILTER = self.filter_field.GetValue()
        for period, panel in zip(watcher_report.PERIODS, self.period_panels):
            panel.summary_list.update(watcher_report.get_summary(*period))


if __name__ == "__main__":
    app = wx.App()
    try:
        frame = MainWindow(None, "Watcher Report")
        frame.Show()
        app.MainLoop()
    except:
        show_error()
