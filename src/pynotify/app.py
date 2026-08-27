"""Textual user interface for posting messages to Teams webhooks."""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, SelectionList, TextArea


@dataclass(frozen=True)
class Channel:
    """A channel name and the environment variable containing its webhook."""

    name: str
    webhook_env_var: str


class ChannelConfigurationError(ValueError):
    """Raised when the channel configuration cannot be used."""


def default_channels_path() -> Path:
    """Return the user-level default rather than a file inside the project."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "pynotify" / "channels.csv"


def load_channels(path: Path) -> list[Channel]:
    """Load a credential-free channel list from a CSV file."""
    try:
        with path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None or not {"channel_name", "webhook_env_var"} <= set(reader.fieldnames):
                raise ChannelConfigurationError(
                    f"{path} must have channel_name and webhook_env_var columns; "
                    "never put webhook URLs in this file."
                )
            channels = [
                Channel(row["channel_name"].strip(), row["webhook_env_var"].strip())
                for row in reader
                if row["channel_name"].strip() and row["webhook_env_var"].strip()
            ]
    except OSError as error:
        raise ChannelConfigurationError(f"Could not read channel configuration {path}: {error}") from error

    if not channels:
        raise ChannelConfigurationError(f"No channels were found in {path}.")
    if len({channel.name.casefold() for channel in channels}) != len(channels):
        raise ChannelConfigurationError(f"Channel names in {path} must be unique.")
    return channels


def build_adaptive_card(heading: str, message: str) -> dict[str, object]:
    """Build the Adaptive Card payload accepted by Teams workflows."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "size": "Small",
                "weight": "Bolder",
                "color": "Accent",
                "text": heading,
                "wrap": True,
            },
            {"type": "TextBlock", "text": message, "wrap": True},
        ],
    }


def post_message(webhook_url: str, heading: str, message: str) -> None:
    """Post one card, raising a descriptive error on delivery failure."""
    payload = json.dumps(build_adaptive_card(heading, message)).encode()
    request = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 202):
                raise RuntimeError(f"Webhook returned HTTP {response.status}.")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Webhook returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach webhook: {error.reason}") from error


class NotifyApp(App[None]):
    """Select channels, compose a Teams card, and send it."""

    CSS = """
    #content { height: 1fr; }
    #channel-panel { width: 32; padding: 1; }
    #composer { width: 1fr; padding: 1; }
    #message { height: 1fr; }
    #send { width: 100%; margin-top: 1; }
    """

    def __init__(self, channels: list[Channel]) -> None:
        super().__init__()
        self.channels = {channel.name: channel for channel in channels}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="content"):
            with Vertical(id="channel-panel"):
                yield Label("Channels")
                yield SelectionList(
                    *[(channel.name, channel.name) for channel in self.channels.values()],
                    id="channels",
                )
            with Vertical(id="composer"):
                yield Label("Header")
                yield Input(placeholder="Notification header", id="heading")
                yield Label("Message")
                yield TextArea("", id="message")
                yield Button("Send to selected channels", id="send", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "send":
            return
        selected = list(self.query_one("#channels", SelectionList).selected)
        heading = self.query_one("#heading", Input).value.strip()
        message = self.query_one("#message", TextArea).text.strip()
        if not selected:
            self.notify("Select at least one channel.", severity="warning")
        elif not heading or not message:
            self.notify("A header and message are required.", severity="warning")
        else:
            event.button.disabled = True
            self.send_messages(selected, heading, message)

    @work(thread=True, exclusive=True)
    def send_messages(self, selected: list[str], heading: str, message: str) -> None:
        failures: list[str] = []
        for name in selected:
            webhook_url = os.environ.get(self.channels[name].webhook_env_var)
            if not webhook_url:
                failures.append(f"{name}: {self.channels[name].webhook_env_var} is not set")
                continue
            try:
                post_message(webhook_url, heading, message)
            except RuntimeError as error:
                failures.append(f"{name}: {error}")
        self.call_from_thread(self._show_send_result, len(selected), failures)

    def _show_send_result(self, total: int, failures: list[str]) -> None:
        self.query_one("#send", Button).disabled = False
        if failures:
            self.notify(
                f"Sent {total - len(failures)}/{total}. " + " | ".join(failures),
                severity="error",
                timeout=12,
            )
        else:
            self.notify(f"Sent to {total} channel(s).", severity="information")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send Teams status messages from a terminal UI.")
    parser.add_argument(
        "--channels",
        type=Path,
        default=(
            Path(os.environ["PYNOTIFY_CHANNELS_FILE"])
            if "PYNOTIFY_CHANNELS_FILE" in os.environ
            else default_channels_path()
        ),
        help="Credential-free channel CSV path (default: %(default)s or $PYNOTIFY_CHANNELS_FILE).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the application or print a clear configuration error."""
    args = parse_args()
    try:
        channels = load_channels(args.channels)
    except ChannelConfigurationError as error:
        raise SystemExit(error) from error
    NotifyApp(channels).run()
