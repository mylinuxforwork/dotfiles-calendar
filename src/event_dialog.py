# event_dialog.py
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

from gi.repository import Adw, Gtk, GObject
from datetime import datetime
from .event_manager import Event, EventManager


class AddEventDialog(Adw.Dialog):
    """Dialog for adding or editing an event."""
    
    __gsignals__ = {
        'event-saved': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, event_manager: EventManager, date_str: str = "", event: Event = None, **kwargs):
        super().__init__(**kwargs)
        
        self.event_manager = event_manager
        self.editing_event = event
        self.date_str = date_str
        
        self.set_title("Edit Event" if event else "Add Event")
        self.set_content_width(400)
        self.set_content_height(500)
        
        self._build_ui()
        
        # Populate fields if editing
        if event:
            self.title_entry.set_text(event.title)
            self.description_entry.set_text(event.description)
            self.notify_switch.set_active(event.notify)
            
            if event.time:
                self.all_day_switch.set_active(False)
                try:
                    parts = event.time.split(":")
                    self.hour_spin.set_value(int(parts[0]))
                    self.minute_spin.set_value(int(parts[1]))
                except (ValueError, IndexError):
                    pass
            else:
                self.all_day_switch.set_active(True)
            
            self.reminder_combo.set_selected(self._get_reminder_index(event.notify_minutes_before))
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Main toolbar view
        toolbar = Adw.ToolbarView()
        self.set_child(toolbar)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)
        
        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)
        
        # Save button
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        toolbar.add_top_bar(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        # Preferences groups
        # Basic info group
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title("Event Details")
        
        # Title
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Title")
        basic_group.add(self.title_entry)
        
        # Description
        self.description_entry = Adw.EntryRow()
        self.description_entry.set_title("Description")
        basic_group.add(self.description_entry)
        
        content.append(basic_group)
        
        # Time group
        time_group = Adw.PreferencesGroup()
        time_group.set_title("Time")
        time_group.set_margin_top(24)
        
        # All day toggle
        self.all_day_switch = Adw.SwitchRow()
        self.all_day_switch.set_title("All Day")
        self.all_day_switch.set_active(True)
        self.all_day_switch.connect("notify::active", self._on_all_day_toggled)
        time_group.add(self.all_day_switch)
        
        # Time picker row
        self.time_row = Adw.ActionRow()
        self.time_row.set_title("Time")
        self.time_row.set_sensitive(False)
        
        # Hour spinner
        hour_adj = Gtk.Adjustment(value=12, lower=0, upper=23, step_increment=1)
        self.hour_spin = Gtk.SpinButton()
        self.hour_spin.set_adjustment(hour_adj)
        self.hour_spin.set_numeric(True)
        self.hour_spin.set_wrap(True)
        self.hour_spin.set_width_chars(2)
        self.hour_spin.set_valign(Gtk.Align.CENTER)
        
        # Separator label
        colon_label = Gtk.Label(label=":")
        colon_label.set_valign(Gtk.Align.CENTER)
        colon_label.set_margin_start(4)
        colon_label.set_margin_end(4)
        
        # Minute spinner
        minute_adj = Gtk.Adjustment(value=0, lower=0, upper=59, step_increment=5)
        self.minute_spin = Gtk.SpinButton()
        self.minute_spin.set_adjustment(minute_adj)
        self.minute_spin.set_numeric(True)
        self.minute_spin.set_wrap(True)
        self.minute_spin.set_width_chars(2)
        self.minute_spin.set_valign(Gtk.Align.CENTER)
        
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        time_box.append(self.hour_spin)
        time_box.append(colon_label)
        time_box.append(self.minute_spin)
        
        self.time_row.add_suffix(time_box)
        time_group.add(self.time_row)
        
        content.append(time_group)
        
        # Notification group
        notify_group = Adw.PreferencesGroup()
        notify_group.set_title("Notifications")
        notify_group.set_margin_top(24)
        
        # Enable notifications
        self.notify_switch = Adw.SwitchRow()
        self.notify_switch.set_title("Enable Notification")
        self.notify_switch.set_active(True)
        self.notify_switch.connect("notify::active", self._on_notify_toggled)
        notify_group.add(self.notify_switch)
        
        # Reminder time
        self.reminder_row = Adw.ComboRow()
        self.reminder_row.set_title("Remind Me")
        
        reminder_options = Gtk.StringList()
        reminder_options.append("At time of event")
        reminder_options.append("5 minutes before")
        reminder_options.append("15 minutes before")
        reminder_options.append("30 minutes before")
        reminder_options.append("1 hour before")
        reminder_options.append("1 day before")
        
        self.reminder_combo = self.reminder_row
        self.reminder_combo.set_model(reminder_options)
        self.reminder_combo.set_selected(0)
        notify_group.add(self.reminder_row)
        
        content.append(notify_group)
        
        # Delete button for editing
        if self.editing_event:
            delete_group = Adw.PreferencesGroup()
            delete_group.set_margin_top(24)
            
            delete_btn = Gtk.Button(label="Delete Event")
            delete_btn.add_css_class("destructive-action")
            delete_btn.set_halign(Gtk.Align.CENTER)
            delete_btn.connect("clicked", self._on_delete)
            
            delete_group.add(delete_btn)
            content.append(delete_group)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(content)
        
        toolbar.set_content(scrolled)
    
    def _on_all_day_toggled(self, switch, _):
        """Handle all-day toggle."""
        is_all_day = switch.get_active()
        self.time_row.set_sensitive(not is_all_day)
    
    def _on_notify_toggled(self, switch, _):
        """Handle notification toggle."""
        self.reminder_row.set_sensitive(switch.get_active())
    
    def _get_reminder_minutes(self) -> int:
        """Get reminder minutes from combo selection."""
        selected = self.reminder_combo.get_selected()
        mapping = {
            0: 0,       # At time of event
            1: 5,       # 5 minutes before
            2: 15,      # 15 minutes before
            3: 30,      # 30 minutes before
            4: 60,      # 1 hour before
            5: 1440,    # 1 day before
        }
        return mapping.get(selected, 0)
    
    def _get_reminder_index(self, minutes: int) -> int:
        """Get combo index from reminder minutes."""
        mapping = {
            0: 0,
            5: 1,
            15: 2,
            30: 3,
            60: 4,
            1440: 5,
        }
        return mapping.get(minutes, 0)
    
    def _on_save(self, button):
        """Save the event."""
        title = self.title_entry.get_text().strip()
        
        if not title:
            # Show error toast
            toast = Adw.Toast.new("Please enter an event title")
            # Find the toast overlay (if any)
            self.title_entry.grab_focus()
            return
        
        # Build time string
        time_str = ""
        if not self.all_day_switch.get_active():
            hour = int(self.hour_spin.get_value())
            minute = int(self.minute_spin.get_value())
            time_str = f"{hour:02d}:{minute:02d}"
        
        if self.editing_event:
            # Update existing event
            self.editing_event.title = title
            self.editing_event.description = self.description_entry.get_text().strip()
            self.editing_event.time = time_str
            self.editing_event.notify = self.notify_switch.get_active()
            self.editing_event.notify_minutes_before = self._get_reminder_minutes()
            self.editing_event.notified = False  # Reset notification status
            self.event_manager.update_event(self.editing_event)
            self.emit('event-saved', self.editing_event)
        else:
            # Create new event
            event = Event(
                title=title,
                date=self.date_str,
                time=time_str,
                description=self.description_entry.get_text().strip(),
                notify=self.notify_switch.get_active(),
                notify_minutes_before=self._get_reminder_minutes()
            )
            self.event_manager.add_event(event)
            self.emit('event-saved', event)
        
        self.close()
    
    def _on_delete(self, button):
        """Delete the event."""
        if self.editing_event:
            self.event_manager.remove_event(self.editing_event.id)
        self.close()


class EventListDialog(Adw.Dialog):
    """Dialog for viewing events on a specific date."""
    
    def __init__(self, event_manager: EventManager, date_str: str, **kwargs):
        super().__init__(**kwargs)
        
        self.event_manager = event_manager
        self.date_str = date_str
        
        # Parse date for display
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = dt.strftime("%B %d, %Y")
        except ValueError:
            date_display = date_str
        
        self.set_title(f"Events - {date_display}")
        self.set_content_width(400)
        self.set_content_height(450)
        
        self._build_ui()
        self._load_events()
        
        # Register for updates
        self.event_manager.register_callback(self._load_events)
    
    def _build_ui(self):
        """Build the dialog UI."""
        toolbar = Adw.ToolbarView()
        self.set_child(toolbar)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)
        
        # Close button
        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda _: self.close())
        header.pack_start(close_btn)
        
        # Add button
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_event)
        header.pack_end(add_btn)
        
        toolbar.add_top_bar(header)
        
        # Content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        
        scrolled.set_child(self.content_box)
        toolbar.set_content(scrolled)
        
        # Status page for empty state
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("x-office-calendar-symbolic")
        self.status_page.set_title("No Events")
        self.status_page.set_description("Tap + to add an event for this day")
        
        self.events_group = Adw.PreferencesGroup()
    
    def _load_events(self):
        """Load and display events for the date."""
        # Clear existing content
        while True:
            child = self.content_box.get_first_child()
            if child is None:
                break
            self.content_box.remove(child)
        
        events = self.event_manager.get_events_for_date(self.date_str)
        
        if not events:
            self.content_box.append(self.status_page)
        else:
            # Sort events by time
            events.sort(key=lambda e: (e.time == "", e.time))
            
            events_group = Adw.PreferencesGroup()
            
            for event in events:
                row = Adw.ActionRow()
                row.set_title(event.title)
                
                subtitle = event.get_display_time()
                if event.description:
                    subtitle += f" • {event.description}"
                row.set_subtitle(subtitle)
                
                # Notification indicator
                if event.notify:
                    notify_icon = Gtk.Image.new_from_icon_name("preferences-system-notifications-symbolic")
                    notify_icon.set_opacity(0.5)
                    row.add_prefix(notify_icon)
                
                # Edit button
                edit_btn = Gtk.Button()
                edit_btn.set_icon_name("document-edit-symbolic")
                edit_btn.set_valign(Gtk.Align.CENTER)
                edit_btn.add_css_class("flat")
                edit_btn.connect("clicked", self._on_edit_event, event)
                row.add_suffix(edit_btn)
                
                # Arrow
                arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
                row.add_suffix(arrow)
                row.set_activatable(True)
                row.connect("activated", self._on_edit_event, event)
                
                events_group.add(row)
            
            self.content_box.append(events_group)
    
    def _on_add_event(self, button):
        """Show add event dialog."""
        dialog = AddEventDialog(self.event_manager, self.date_str)
        dialog.connect('event-saved', lambda d, e: self._load_events())
        dialog.present(self)
    
    def _on_edit_event(self, widget, event):
        """Show edit event dialog."""
        dialog = AddEventDialog(self.event_manager, self.date_str, event=event)
        dialog.connect('event-saved', lambda d, e: self._load_events())
        dialog.present(self)


class AllEventsDialog(Adw.Dialog):
    """Dialog for viewing all events."""
    
    def __init__(self, event_manager: EventManager, **kwargs):
        super().__init__(**kwargs)
        
        self.event_manager = event_manager
        
        self.set_title("All Events")
        self.set_content_width(450)
        self.set_content_height(550)
        
        self._build_ui()
        self._load_events()
        
        # Register for updates
        self.event_manager.register_callback(self._load_events)
    
    def _build_ui(self):
        """Build the dialog UI."""
        toolbar = Adw.ToolbarView()
        self.set_child(toolbar)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)
        
        # Close button
        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda _: self.close())
        header.pack_start(close_btn)
        
        toolbar.add_top_bar(header)
        
        # Content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        
        scrolled.set_child(self.content_box)
        toolbar.set_content(scrolled)
        
        # Status page for empty state
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("x-office-calendar-symbolic")
        self.status_page.set_title("No Events")
        self.status_page.set_description("Add events by selecting a date on the calendar")
    
    def _load_events(self):
        """Load and display all events grouped by date."""
        # Clear existing content
        while True:
            child = self.content_box.get_first_child()
            if child is None:
                break
            self.content_box.remove(child)
        
        events = self.event_manager.events
        
        if not events:
            self.content_box.append(self.status_page)
            return
        
        # Group events by date
        events_by_date = {}
        for event in events:
            if event.date not in events_by_date:
                events_by_date[event.date] = []
            events_by_date[event.date].append(event)
        
        # Sort dates
        sorted_dates = sorted(events_by_date.keys())
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Separate past and upcoming events
        upcoming_dates = [d for d in sorted_dates if d >= today]
        past_dates = [d for d in sorted_dates if d < today]
        
        # Show upcoming events first
        if upcoming_dates:
            upcoming_group = Adw.PreferencesGroup()
            upcoming_group.set_title("Upcoming Events")
            
            for date_str in upcoming_dates:
                self._add_date_events(upcoming_group, date_str, events_by_date[date_str], today)
            
            self.content_box.append(upcoming_group)
        
        # Show past events
        if past_dates:
            past_group = Adw.PreferencesGroup()
            past_group.set_title("Past Events")
            past_group.set_margin_top(12)
            
            for date_str in reversed(past_dates):  # Most recent first
                self._add_date_events(past_group, date_str, events_by_date[date_str], today)
            
            self.content_box.append(past_group)
        
        if not upcoming_dates and not past_dates:
            self.content_box.append(self.status_page)
    
    def _add_date_events(self, group, date_str, events, today):
        """Add events for a specific date to the group."""
        # Format the date
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if date_str == today:
                date_display = "Today"
            else:
                date_display = dt.strftime("%A, %B %d")
        except ValueError:
            date_display = date_str
        
        # Sort events by time
        events.sort(key=lambda e: (e.time == "", e.time))
        
        for i, event in enumerate(events):
            row = Adw.ActionRow()
            row.set_title(event.title)
            
            # Build subtitle with date (for first event of each date) and time
            if i == 0:
                subtitle = f"📅 {date_display}"
                if event.time:
                    subtitle += f" • {event.get_display_time()}"
            else:
                subtitle = event.get_display_time()
            
            if event.description:
                subtitle += f" • {event.description}"
            
            row.set_subtitle(subtitle)
            
            # Notification indicator
            if event.notify:
                notify_icon = Gtk.Image.new_from_icon_name("preferences-system-notifications-symbolic")
                notify_icon.set_opacity(0.5)
                row.add_prefix(notify_icon)
            
            # Edit button
            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.add_css_class("flat")
            edit_btn.connect("clicked", self._on_edit_event, event)
            row.add_suffix(edit_btn)
            
            # Delete button
            delete_btn = Gtk.Button()
            delete_btn.set_icon_name("user-trash-symbolic")
            delete_btn.set_valign(Gtk.Align.CENTER)
            delete_btn.add_css_class("flat")
            delete_btn.connect("clicked", self._on_delete_event, event)
            row.add_suffix(delete_btn)
            
            row.set_activatable(True)
            row.connect("activated", self._on_edit_event, event)
            
            group.add(row)
    
    def _on_edit_event(self, widget, event):
        """Show edit event dialog."""
        dialog = AddEventDialog(self.event_manager, event.date, event=event)
        dialog.connect('event-saved', lambda d, e: self._load_events())
        dialog.present(self)
    
    def _on_delete_event(self, button, event):
        """Delete an event."""
        self.event_manager.remove_event(event.id)
        self._load_events()
