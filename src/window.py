# window.py
#
# Copyright 2025 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk, GLib, Gdk
from datetime import datetime
from .event_manager import EventManager
from .event_dialog import EventListDialog, AddEventDialog, AllEventsDialog

# CSS for styling calendar marked days
CALENDAR_CSS = """
/* Try border-bottom approach for marked calendar days */
calendar > grid > label.day-number[data-marked="true"],
calendar day:checked label,
calendar label.day:checked,
.day-number:backdrop:marked,
calendar.view grid label:marked {
    border-bottom: 2px solid @accent_color;
    font-weight: bold;
}
"""


@Gtk.Template(resource_path='/com/ml4w/calendar/window.ui')
class DotfilesCalendarWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DotfilesCalendarWindow'

    calendar = Gtk.Template.Child()
    events_banner = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load custom CSS for calendar styling
        self._load_css()
        
        # Initialize event manager
        self.event_manager = EventManager()
        
        # Set up calendar
        current_month = datetime.now().strftime('%m')
        self.calendar.set_month(datetime.now().month - 1)
        self.calendar.set_day(datetime.now().day)
        
        # Connect calendar signals
        self.calendar.connect("day-selected", self._on_day_selected)
        self.calendar.connect("next-month", self._on_month_changed)
        self.calendar.connect("prev-month", self._on_month_changed)
        self.calendar.connect("next-year", self._on_month_changed)
        self.calendar.connect("prev-year", self._on_month_changed)
        
        # Add double-click gesture for GTK4
        gesture = Gtk.GestureClick.new()
        gesture.set_button(1)  # Left mouse button
        gesture.connect("released", self._on_calendar_click)
        self.calendar.add_controller(gesture)
        
        # Register for event updates
        self.event_manager.register_callback(self._update_calendar_marks)
        
        # Initial mark update
        GLib.idle_add(self._update_calendar_marks)
    
    def _load_css(self):
        """Load custom CSS for calendar styling."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(CALENDAR_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _get_selected_date_str(self) -> str:
        """Get the currently selected date as a string (YYYY-MM-DD)."""
        date = self.calendar.get_date()
        return date.format("%Y-%m-%d")
    
    def _on_day_selected(self, calendar):
        """Handle single click on a day - could show a subtle indicator."""
        pass
    
    def _on_calendar_click(self, gesture, n_press, x, y):
        """Handle click on calendar - double-click shows events."""
        if n_press == 2:  # Double click
            date_str = self._get_selected_date_str()
            events = self.event_manager.get_events_for_date(date_str)
            
            if events:
                # Show event list
                dialog = EventListDialog(self.event_manager, date_str)
                dialog.present(self)
            else:
                # Show add event dialog directly
                dialog = AddEventDialog(self.event_manager, date_str)
                dialog.present(self)
    
    def _on_month_changed(self, calendar):
        """Handle month/year change - update marks."""
        GLib.idle_add(self._update_calendar_marks)
    
    def _update_calendar_marks(self):
        """Update calendar to mark dates with events and update indicator."""
        # Clear all marks first
        self.calendar.clear_marks()
        
        # Get current displayed month/year
        date = self.calendar.get_date()
        current_year = date.get_year()
        current_month = date.get_month()
        
        # Get all dates with events
        dates_with_events = self.event_manager.get_dates_with_events()
        
        # Find days in the current month that have events
        days_with_events = []
        for date_str in dates_with_events:
            try:
                parts = date_str.split("-")
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                
                if year == current_year and month == current_month:
                    self.calendar.mark_day(day)
                    days_with_events.append(day)
            except (ValueError, IndexError):
                pass
        return False  # Don't repeat
    
    def show_events_for_selected_date(self):
        """Public method to show events for the selected date."""
        date_str = self._get_selected_date_str()
        dialog = EventListDialog(self.event_manager, date_str)
        dialog.present(self)
    
    def add_event_for_selected_date(self):
        """Public method to add event for the selected date."""
        date_str = self._get_selected_date_str()
        dialog = AddEventDialog(self.event_manager, date_str)
        dialog.present(self)
    
    def show_all_events(self):
        """Public method to show all events."""
        dialog = AllEventsDialog(self.event_manager)
        dialog.present(self)
