#!/usr/bin/env python3
"""
Setup script for fabric-mcp-standalone.
Installs dependencies and writes Claude Desktop config.
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


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def find_uv():
    uv = shutil.which("uv")
    if uv:
        return uv
    candidates = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path.home() / ".local" / "bin" / "uv.exe",
        Path.home() / ".cargo" / "bin" / "uv.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def get_claude_config_path():
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def step(n, msg):
    print(f"\n[{n}] {msg}")


# ── Step 1: check uv ──────────────────────────────────────────────────────────
step(1, "Checking for uv...")
uv = find_uv()
if not uv:
    print("  ERROR: uv not found. Install it from https://docs.astral.sh/uv/getting-started/installation/")
    sys.exit(1)
print(f"  Found: {uv}")

# ── Step 2: check az ──────────────────────────────────────────────────────────
step(2, "Checking Azure CLI authentication...")
az = shutil.which("az") or shutil.which("az.cmd")
if not az:
    print("  WARNING: Azure CLI not found. Install from https://aka.ms/installazurecliwindows")
    print("  fabric-core tools require 'az login' before use.")
else:
    result = run(
        [az, "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com/"],
        check=False,
    )
    if result.returncode != 0:
        print("  WARNING: Not logged in to Azure. Run 'az login' before using Claude.")
    else:
        print("  Azure auth OK.")

# ── Step 3: install fabric-core deps ─────────────────────────────────────────
step(3, "Installing fabric-core dependencies (this may take a minute)...")
run([uv, "sync"], cwd=FABRIC_CORE)
print("  Done.")

# ── Step 4: write Claude Desktop config ──────────────────────────────────────
step(4, "Writing Claude Desktop config...")
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
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print(f"  Written: {config_path}")

# ── Done ─────────────────────────────────────────────────────────────────────
print("""
Setup complete! Restart Claude Desktop.
Run 'az login' if not already authenticated.
""")
