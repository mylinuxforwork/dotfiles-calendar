# event_manager.py
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

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from gi.repository import GLib, Gio

class Event:
    """Represents a calendar event or reminder."""
    
    def __init__(self, title: str, date: str, time: str = "", 
                 description: str = "", notify: bool = True, 
                 notify_minutes_before: int = 0, event_id: str = None):
        self.id = event_id or str(uuid.uuid4())
        self.title = title
        self.date = date  # Format: YYYY-MM-DD
        self.time = time  # Format: HH:MM (24h) or empty for all-day
        self.description = description
        self.notify = notify
        self.notify_minutes_before = notify_minutes_before
        self.notified = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "time": self.time,
            "description": self.description,
            "notify": self.notify,
            "notify_minutes_before": self.notify_minutes_before,
            "notified": self.notified
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        event = cls(
            title=data.get("title", ""),
            date=data.get("date", ""),
            time=data.get("time", ""),
            description=data.get("description", ""),
            notify=data.get("notify", True),
            notify_minutes_before=data.get("notify_minutes_before", 0),
            event_id=data.get("id")
        )
        event.notified = data.get("notified", False)
        return event
    
    def get_datetime(self) -> Optional[datetime]:
        """Get the datetime of this event."""
        try:
            if self.time:
                return datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
            else:
                return datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            return None
    
    def get_display_time(self) -> str:
        """Get a formatted time string for display."""
        if self.time:
            try:
                dt = datetime.strptime(self.time, "%H:%M")
                return dt.strftime("%I:%M %p")
            except ValueError:
                return self.time
        return "All day"


class EventManager:
    """Manages calendar events with persistence and notifications."""
    
    def __init__(self):
        self.home_folder = os.path.expanduser('~')
        self.config_folder = os.path.join(self.home_folder, ".config", "com.ml4w.calendar")
        self.events_file = os.path.join(self.config_folder, "events.json")
        self.events: List[Event] = []
        self._notification_timeout_id = None
        self._callbacks = []
        
        # Ensure config directory exists
        os.makedirs(self.config_folder, exist_ok=True)
        
        # Load existing events
        self.load_events()
        
        # Start notification checker
        self._start_notification_checker()
    
    def load_events(self):
        """Load events from the JSON file."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    self.events = [Event.from_dict(e) for e in data.get("events", [])]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading events: {e}")
                self.events = []
        else:
            self.events = []
    
    def save_events(self):
        """Save events to the JSON file."""
        try:
            with open(self.events_file, 'w') as f:
                data = {"events": [e.to_dict() for e in self.events]}
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving events: {e}")
    
    def add_event(self, event: Event) -> bool:
        """Add a new event."""
        self.events.append(event)
        self.save_events()
        self._notify_callbacks()
        return True
    
    def update_event(self, event: Event) -> bool:
        """Update an existing event."""
        for i, e in enumerate(self.events):
            if e.id == event.id:
                self.events[i] = event
                self.save_events()
                self._notify_callbacks()
                return True
        return False
    
    def remove_event(self, event_id: str) -> bool:
        """Remove an event by ID."""
        for i, e in enumerate(self.events):
            if e.id == event_id:
                del self.events[i]
                self.save_events()
                self._notify_callbacks()
                return True
        return False
    
    def get_events_for_date(self, date_str: str) -> List[Event]:
        """Get all events for a specific date (YYYY-MM-DD format)."""
        return [e for e in self.events if e.date == date_str]
    
    def get_dates_with_events(self) -> set:
        """Get a set of all dates that have events."""
        return {e.date for e in self.events}
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get a specific event by ID."""
        for e in self.events:
            if e.id == event_id:
                return e
        return None
    
    def register_callback(self, callback):
        """Register a callback to be called when events change."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def _start_notification_checker(self):
        """Start the periodic notification checker."""
        # Check every 30 seconds
        self._notification_timeout_id = GLib.timeout_add_seconds(30, self._check_notifications)
        # Also check immediately
        GLib.idle_add(self._check_notifications)
    
    def _check_notifications(self) -> bool:
        """Check for events that need notifications."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        for event in self.events:
            if not event.notify or event.notified:
                continue
            
            event_dt = event.get_datetime()
            if event_dt is None:
                continue
            
            # Calculate when to notify
            notify_time = event_dt - timedelta(minutes=event.notify_minutes_before)
            
            # Check if it's time to notify
            if now >= notify_time and now <= event_dt + timedelta(hours=1):
                self._send_notification(event)
                event.notified = True
                self.save_events()
        
        # Reset notified flag for past events (next day)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        for event in self.events:
            if event.date < today and event.notified:
                event.notified = False
        
        return True  # Continue the timeout
    
    def _send_notification(self, event: Event):
        """Send a desktop notification for an event."""
        try:
            notification = Gio.Notification.new(event.title)
            
            message = ""
            if event.time:
                message = f"📅 {event.get_display_time()}"
            else:
                message = "📅 Today"
            
            if event.description:
                message += f"\n{event.description}"
            
            notification.set_body(message)
            notification.set_priority(Gio.NotificationPriority.HIGH)
            
            # Get the application and send notification
            app = Gio.Application.get_default()
            if app:
                app.send_notification(f"event-{event.id}", notification)
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self._notification_timeout_id:
            GLib.source_remove(self._notification_timeout_id)
            self._notification_timeout_id = None
