# NewAPI Client Configurator

Windows GUI for discovering a NewAPI gateway, probing models through the actual
Responses, Chat Completions and Anthropic Messages routes, and producing guarded
configuration for Codex, Claude Code, and OpenCode.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Build

```powershell
pyinstaller --onefile --windowed --name NewAPIClientConfigurator main.py
```

The app never logs tokens. Configuration is always previewed before it is
written. Model entries are eligible only after the protocol required by their
target client has passed text, streaming, and tool-call probes.

Quick testing includes an 8K context lower-bound request after a protocol has
passed. It never claims that result as the maximum context window; declared
limits come only from resolved metadata or a future manual override.
