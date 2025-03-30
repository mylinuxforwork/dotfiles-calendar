from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio

@Gtk.Template(resource_path='/com/ml4w/calendar/settings.ui')
class DotfilesCalendarSettings(Adw.PreferencesDialog):
    __gtype_name__ = 'DotfilesCalendarSettings'

    eventsbuttoncommand = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings(schema_id="com.ml4w.calendar")
        self.eventsbuttoncommand.set_text(self.settings.get_string("eventsbuttoncommand"))

