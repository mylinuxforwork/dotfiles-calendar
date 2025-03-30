# main.py
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

import sys
import gi
import subprocess
import os
import pathlib
import shutil
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import DotfilesCalendarWindow
from .settings import DotfilesCalendarSettings
from datetime import datetime

# The main application singleton class
class DotfilesCalendarApplication(Adw.Application):

    # Folders
    home_folder = os.path.expanduser('~')
    config_folder = home_folder + "/.config/com.ml4w.calendar"

    # Paths
    path_name = os.path.dirname(sys.argv[0])

    config = {}

    def __init__(self):
        super().__init__(application_id='com.ml4w.calendar',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('settings', self.on_settings_action)
        self.create_action('open_events', self.on_open_events)
        self.create_action('calendar_today', self.on_calendar_today)

    def do_activate(self):
        self.run_setup()

        win = self.props.active_window
        if not win:
            win = DotfilesCalendarWindow(application=self)
        win.present()

        self.calendar = win.calendar
        self.events_banner = win.events_banner

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
            application_name="ML4W Calendar App",
            developer_name="Stephan Raabe",
            version="1.0",
            website="https://github.com/mylinuxforwork/dotfiles-calendar",
            issue_url="https://github.com/mylinuxforwork/dotfiles-calendar/issues",
            support_url="https://github.com/mylinuxforwork/dotfiles-calendar/issues",
            copyright="© 2025 Stephan Raabe",
        )
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        # about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_settings_action(self, *args):
        self.events_banner.set_revealed(revealed=False)
        settings = DotfilesCalendarSettings(application=self)
        settings.eventsbuttoncommand.set_show_apply_button(True)
        settings.eventsbuttoncommand.set_text(self.config["eventsbuttoncommand"])
        settings.eventsbuttoncommand.connect("apply", self.on_eventsbuttoncommand)
        settings.present()

    def on_eventsbuttoncommand(self, widget):
        self.config["eventsbuttoncommand"] = widget.get_text()
        self.write_config()

    def on_open_events(self, widget, _):
        if self.config["eventsbuttoncommand"] != "":
            subprocess.Popen(["flatpak-spawn", "--host", self.config["eventsbuttoncommand"]])
            self.quit()
        else:
            self.on_show_banner()

    def on_show_banner(self, *args):
        self.events_banner.set_revealed(revealed=True)

    def on_calendar_today(self, widget, _):
        self.calendar.set_month(datetime.now().month-1)
        self.calendar.set_day(datetime.now().day)

    # Write config to json
    def write_config(self, *args):
        with open(self.config_folder + '/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    # Create or load the application configuration
    def run_setup(self):
        # Create com.ml4w.calendar in .config folder
        pathlib.Path(self.config_folder).mkdir(parents=True, exist_ok=True)

        # Create empty config.json if not exists
        if not os.path.exists(self.config_folder + '/config.json'):
            self.config["eventsbuttoncommand"] = ""
            with open(self.config_folder + '/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        else:
            config_file = open(self.config_folder + "/config.json")
            self.config = json.load(config_file)

    # Add an application action
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = DotfilesCalendarApplication()
    return app.run(sys.argv)
