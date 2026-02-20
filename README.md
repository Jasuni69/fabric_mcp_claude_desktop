# fabric-mcp-standalone

Fabric & Power BI MCP servers for **Claude Desktop** — no VS Code needed.

## What's included

| Server | Tools | Description |
|--------|-------|-------------|
| `fabric-core` | 138+ | Workspaces, lakehouses, SQL, DAX, notebooks, pipelines, OneLake, Git, CI/CD |

> **Not included:** `powerbi-modeling` and `powerbi-translation-audit` — both require the VS Code extension.

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.12+ | https://python.org |
| uv | https://docs.astral.sh/uv/getting-started/installation/ |
| Azure CLI | https://aka.ms/installazurecliwindows |

## Setup

```bash
# 1. Run setup (one time)
python setup.py

# 2. Log in to Azure (required for Fabric API access)
az login

# 3. Restart Claude Desktop
```

That's it. The setup script:
- Installs Python deps via `uv sync`
- Creates a venv for translation-audit
- Writes server entries into `claude_desktop_config.json`

## Usage

In Claude Desktop, the `fabric-core` tools are available immediately after restart.

Start with context:
```
set_workspace → set_lakehouse → list_tables → sql_query
```

See `CLAUDE.md` for full rules and `CLAUDE.md` + `.claude/agents/` for domain-specific guidance.

## Updating

Pull new code, then re-run `python setup.py`. Config paths are stable so it merges safely.
