# Fabric & Power BI MCP for Claude Desktop

Three MCP servers for Microsoft Fabric and Power BI — no VS Code required.

## Servers

| Server | Tools | Description |
|--------|-------|-------------|
| `fabric-core` | 138+ | Workspaces, lakehouses, SQL, DAX, notebooks, pipelines, OneLake, Git, CI/CD |
| `powerbi-modeling` | 15+ | Live semantic model editing via TOM API (requires Power BI Desktop open) |
| `powerbi-translation-audit` | 3 | Scan .pbip reports for untranslated content |

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.12+ | https://python.org |
| uv | https://docs.astral.sh/uv/getting-started/installation/ |
| Azure CLI | https://aka.ms/installazurecliwindows |
| Power BI Desktop | https://powerbi.microsoft.com/desktop (for powerbi-modeling only) |

## Setup

```bash
git clone https://github.com/Jasuni69/fabric_mcp_claude_desktop.git
cd fabric_mcp_claude_desktop
python setup.py
```

Then restart Claude Desktop.

`setup.py`:
- Installs fabric-core deps via `uv sync`
- Creates a venv for translation-audit
- Downloads `powerbi-modeling-mcp.exe` from the VS Marketplace (or reuses existing VS Code install)
- Writes all servers into `claude_desktop_config.json` — merges safely with existing config

## Authentication

```bash
az login
```

Required for all fabric-core tools. Run once — token is cached.

## Usage

Start with:
```
set_workspace → set_lakehouse → list_tables → sql_query
```
