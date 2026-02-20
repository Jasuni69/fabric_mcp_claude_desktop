#!/usr/bin/env python3
"""
Setup script for Fabric & Power BI MCP for Claude Desktop.
Installs all three MCP servers and writes claude_desktop_config.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
FABRIC_CORE = HERE / "fabric-core"
POWERBI_MODELING = HERE / "powerbi-modeling"
TRANSLATION_AUDIT = HERE / "translation-audit"


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def find_uv():
    uv = shutil.which("uv")
    if uv:
        return uv
    for p in [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path.home() / ".local" / "bin" / "uv.exe",
        Path.home() / ".cargo" / "bin" / "uv.exe",
    ]:
        if p.exists():
            return str(p)
    return None


def get_claude_config_path():
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def step(n, msg):
    print(f"\n[{n}] {msg}")


# ── Step 1: uv ────────────────────────────────────────────────────────────────
step(1, "Checking for uv...")
uv = find_uv()
if not uv:
    print("  ERROR: uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/")
    sys.exit(1)
print(f"  Found: {uv}")

# ── Step 2: Azure CLI ─────────────────────────────────────────────────────────
step(2, "Checking Azure CLI authentication...")
az = shutil.which("az") or shutil.which("az.cmd")
if not az:
    print("  WARNING: Azure CLI not found. Install: https://aka.ms/installazurecliwindows")
    print("  Run 'az login' before using fabric-core tools.")
else:
    result = run(
        [az, "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com/"],
        check=False,
    )
    print("  Azure auth OK." if result.returncode == 0 else "  WARNING: Not logged in. Run 'az login'.")

# ── Step 3: fabric-core deps ──────────────────────────────────────────────────
step(3, "Installing fabric-core dependencies (may take a minute)...")
run([uv, "sync"], cwd=FABRIC_CORE)
print("  Done.")

# ── Step 4: powerbi-modeling deps ─────────────────────────────────────────────
step(4, "Installing powerbi-modeling dependencies...")
run([uv, "sync"], cwd=POWERBI_MODELING)
print("  Done.")

# ── Step 5: translation-audit venv ───────────────────────────────────────────
step(5, "Setting up translation-audit virtual environment...")
venv_dir = TRANSLATION_AUDIT / ".venv"
python = shutil.which("python3") or shutil.which("python")
if not python:
    print("  ERROR: Python not found on PATH.")
    sys.exit(1)
run([python, "-m", "venv", str(venv_dir)])
if platform.system() == "Windows":
    venv_python = venv_dir / "Scripts" / "python.exe"
    venv_pip = venv_dir / "Scripts" / "pip.exe"
else:
    venv_python = venv_dir / "bin" / "python"
    venv_pip = venv_dir / "bin" / "pip"
run([str(venv_pip), "install", "--quiet", "mcp"])
print("  Done.")

# ── Step 6: write Claude Desktop config ──────────────────────────────────────
step(6, "Writing Claude Desktop config...")
config_path = get_claude_config_path()
config_path.parent.mkdir(parents=True, exist_ok=True)
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {}
config.setdefault("mcpServers", {})

config["mcpServers"]["fabric-core"] = {
    "command": uv,
    "args": ["--directory", str(FABRIC_CORE), "run", "fabric_mcp_stdio.py"],
}
config["mcpServers"]["powerbi-modeling"] = {
    "command": uv,
    "args": ["--directory", str(POWERBI_MODELING), "run", "powerbi-modeling-mcp"],
}
config["mcpServers"]["powerbi-translation-audit"] = {
    "command": str(venv_python),
    "args": [str(TRANSLATION_AUDIT / "server.py")],
}

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print(f"  Written: {config_path}")

# ── Done ─────────────────────────────────────────────────────────────────────
print("\nSetup complete! Configured: fabric-core, powerbi-modeling, powerbi-translation-audit")
print("Restart Claude Desktop to apply.")
print("Run 'az login' if not already authenticated.")
