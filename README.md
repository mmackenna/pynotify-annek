# pynotify

`pynotify-annek` is a [Textual](https://textual.textualize.io/) terminal UI for sending
an Adaptive Card message to one or more Microsoft Teams channels.

## Setup

Install the project, then create a user-level channel list:

```sh
pip install pynotify-annek
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/pynotify"
cp src_script_example/teams_channels.csv.example \
  "${XDG_CONFIG_HOME:-$HOME/.config}/pynotify/channels.csv"
```

The CSV contains only display names and environment-variable names:

```csv
channel_name,webhook_env_var
PreProd Status,PYNOTIFY_PREPROD_WEBHOOK_URL
QA Status,PYNOTIFY_QA_WEBHOOK_URL
```

Set each webhook outside the repository, ideally through the operating system's
secret manager or the shell environment:

```sh
export PYNOTIFY_PREPROD_WEBHOOK_URL='https://…'
export PYNOTIFY_QA_WEBHOOK_URL='https://…'
poetry run pynotify
```

Use `--channels /path/to/channels.csv` or `PYNOTIFY_CHANNELS_FILE` to use a
different channel list. For compatibility, it also accepts a local
`channel_name,webhook_url` CSV. Keep that file outside the repository, do not
commit it, and set its permissions to `600`. The environment-variable format is
recommended because its channel list can be safely committed or distributed.

## Development

```sh
poetry install
pytest
ruff check .
mypy src/pynotify
mkdocs build --strict
```
