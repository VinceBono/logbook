# logbook

A private record of which apps you used on your Windows PC and when, kept on the PC, that an AI agent can
search. It lets an agent answer "what was I working on Tuesday afternoon?" or "how long was I in Excel today?"

It records far less than screen-recording tools do, on purpose:

| It records | It never records |
|---|---|
| The name of the app in front, and for how long | Screenshots or screen text |
| The window title, **only for apps you list** | Keystrokes, clipboard, audio |
| | Anything from apps you exclude |

Nothing leaves the PC. There is no network code in the recorder.

Status: first version. See [Limits](#limits).

## Controls

| Control | What it does |
|---|---|
| Titles are opt-in | Window titles carry document, email and web page names. They are stored only for apps in `title_apps`. Other apps are stored by name with an empty title. |
| Exclusions | Apps in `exclude_apps` are not recorded at all. |
| Pause | While the pause file exists (default `~/.logbook/PAUSE`), nothing is recorded. |
| Retention | Records older than `retention_days` (default 30) are deleted. |
| Forget | `logbook forget` deletes everything; `logbook forget --app chrome.exe` deletes one app's records. |

## Setup

Needs Windows and [uv](https://docs.astral.sh/uv/).

```
git clone https://github.com/VinceBono/logbook
cd logbook
uv sync
copy logbook.example.toml logbook.toml
```

Edit `logbook.toml`, then start the recorder and leave it running:

```
uv run logbook record
```

Connect an agent, for example Claude Code:

```
claude mcp add logbook -- uv run --directory C:\path\to\logbook logbook serve
```

The agent gets two tools: `search` (when was an app or title in front) and `time_by_app` (totals per app).

## Limits

- **The database is not encrypted.** Anyone signed in as you, and any program you run, can read
  `~/.logbook/logbook.db`. Keep it on an encrypted drive if that matters.
- **An agent you connect can read everything in it**, and may send what it reads to its model provider.
  List only the titles you are willing to share that way.
- **Window titles can carry instructions.** A web page chooses its own tab title, so a title the agent reads
  may be written to steer it. logbook tells the agent to treat titles as data and cuts them to 120 characters;
  it cannot detect steering. Leave browsers out of `title_apps` unless you need them.
- **It samples every few seconds**, so short visits to a window can be missed and times are approximate.
- **It sees only the window in front.** Background apps, and what you did inside an app, are not recorded.
- **Tested with made-up records**, in CI on Windows. It has not yet been left running for days on a real PC.
- Only record a PC that is yours to record. Recording someone else's use of a computer can be illegal.

## Development

```
uv run python -m unittest discover -s tests -v
uv run python scripts/commitguard.py --all
```

## License

MIT. See [LICENSE](LICENSE).
