from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio

@Gtk.Template(resource_path='/com/ml4w/calendar/settings.ui')
class DotfilesCalendarSettings(Adw.PreferencesWindow):
    __gtype_name__ = 'DotfilesCalendarSettings'

    eventsbuttoncommand = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

