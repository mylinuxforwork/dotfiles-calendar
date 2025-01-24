from gi.repository import Adw
from gi.repository import Gtk
from datetime import datetime

@Gtk.Template(resource_path='/com/ml4w/calendar/window.ui')
class DotfilesCalendarWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DotfilesCalendarWindow'

    calendar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        current_month = datetime.now().strftime('%m')
        self.calendar.set_month(datetime.now().month-1)
        self.calendar.set_day(datetime.now().day)

