# Configuration

The channel CSV contains display names and the names of environment variables,
not webhook URLs:

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
different file. The application rejects CSV files that use a `webhook_url`
column, preventing accidental use of URL-bearing channel lists.
