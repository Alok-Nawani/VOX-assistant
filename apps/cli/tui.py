import os
import sys
import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.theme import Theme
from datetime import datetime

# Custom theme for a premium feel
vox_theme = Theme({
    "vox": "bold cyan",
    "user": "bold magenta",
    "status": "italic yellow",
    "system": "dim blue",
    "critical": "bold red"
})

console = Console(theme=vox_theme)

class VoxTUI:
    def __init__(self):
        self.layout = Layout()
        self.history = []
        self.status = "Initializing..."
        self.system_info = {"cpu": "0%", "battery": "0%", "status": "Stable"}
        
        # Build layout
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="chat", ratio=3),
            Layout(name="sidebar", ratio=1)
        )

    def update_status(self, status: str):
        self.status = status

    def add_message(self, role: str, message: str):
        timestamp = datetime.now().strftime("%H:%M")
        self.history.append((role, message, timestamp))
        if len(self.history) > 10:
            self.history.pop(0)

    def update_system(self, cpu: str, battery: str, status: str = "Stable"):
        self.system_info = {"cpu": cpu, "battery": battery, "status": status}

    def _get_header(self):
        return Panel(
            Text(f"VOX AI COMPANION | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", justify="center", style="vox"),
            style="vox"
        )

    def _get_chat_panel(self):
        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim", width=8)
        table.add_column(width=10)
        table.add_column()

        for role, msg, ts in self.history:
            color = "vox" if role.lower() == "vox" else "user"
            table.add_row(ts, f"[{color}]{role.upper()}:[/{color}]", msg)
        
        return Panel(table, title="[bold]Conversation[/bold]", border_style="vox")

    def _get_sidebar(self):
        status_color = "green" if self.system_info["status"] == "Stable" else "yellow"
        
        stats = Text()
        stats.append("\nSYSTEM STATUS\n\n", style="bold")
        stats.append(f"CPU: {self.system_info['cpu']}\n", style="system")
        stats.append(f"BAT: {self.system_info['battery']}\n", style="system")
        stats.append(f"OS: {self.system_info['status']}\n", style=status_color)
        
        return Panel(stats, title="[bold]Metrics[/bold]", border_style="system")

    def _get_footer(self):
        return Panel(
            Text(f"STATUS: {self.status}", justify="left", style="status"),
            border_style="status"
        )

    def render(self):
        self.layout["header"].update(self._get_header())
        self.layout["chat"].update(self._get_chat_panel())
        self.layout["sidebar"].update(self._get_sidebar())
        self.layout["footer"].update(self._get_footer())
        return self.layout

# Global TUI instance
_tui = None

def get_console():
    return console

def get_tui():
    global _tui
    if _tui is None:
        _tui = VoxTUI()
    return _tui
