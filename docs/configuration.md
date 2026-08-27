# Configuration

The recommended channel CSV contains display names and the names of environment
variables, not webhook URLs:

```csv
channel_name,webhook_env_var
PreProd Status,PYNOTIFY_PREPROD_WEBHOOK_URL
QA Status,PYNOTIFY_QA_WEBHOOK_URL
```

By default, `pynotify` reads
`${XDG_CONFIG_HOME:-$HOME/.config}/pynotify/channels.csv`. Copy
`src_script_example/teams_channels.csv.example` there, then supply each webhook
through your shell or secret manager:

```sh
export PYNOTIFY_PREPROD_WEBHOOK_URL='https://...'
pynotify
```

Use `--channels /path/to/channels.csv` or `PYNOTIFY_CHANNELS_FILE` to select a
different file.

## Local webhook file

For compatibility with existing configurations, `pynotify` also accepts a local
CSV with `channel_name,webhook_url` columns. Keep this file outside the project,
do not commit it, and restrict it to your account:

```sh
chmod 600 "${XDG_CONFIG_HOME:-$HOME/.config}/pynotify/channels.csv"
```

Each CSV must use exactly one credential source: `webhook_env_var` or
`webhook_url`, never both.
