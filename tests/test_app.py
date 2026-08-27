from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError

import pytest

from pynotify.app import ChannelConfigurationError, build_adaptive_card, load_channels, post_message


def test_load_channels_reads_credential_free_configuration(tmp_path: Path) -> None:
    channels_file = tmp_path / "channels.csv"
    channels_file.write_text(
        "channel_name,webhook_env_var\nQA Status,PYNOTIFY_QA_WEBHOOK_URL\n",
        encoding="utf-8",
    )

    assert load_channels(channels_file)[0].name == "QA Status"


def test_load_channels_rejects_webhook_urls(tmp_path: Path) -> None:
    channels_file = tmp_path / "channels.csv"
    channels_file.write_text("channel_name,webhook_url\nQA Status,https://secret.example\n", encoding="utf-8")

    with pytest.raises(ChannelConfigurationError, match="webhook_env_var"):
        load_channels(channels_file)


def test_build_adaptive_card_contains_header_and_message() -> None:
    card = build_adaptive_card("Deployment", "Completed")

    assert card["body"] == [
        {
            "type": "TextBlock",
            "size": "Small",
            "weight": "Bolder",
            "color": "Accent",
            "text": "Deployment",
            "wrap": True,
        },
        {"type": "TextBlock", "text": "Completed", "wrap": True},
    ]


def test_post_message_raises_for_webhook_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_http_error(*args: object, **kwargs: object) -> None:
        raise HTTPError("https://example.test", 403, "Forbidden", {}, None)

    monkeypatch.setattr("pynotify.app.urlopen", raise_http_error)

    with pytest.raises(RuntimeError, match="HTTP 403"):
        post_message("https://example.test", "Deployment", "Completed")
