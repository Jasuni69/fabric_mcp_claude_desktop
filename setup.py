#!/usr/bin/env python3
"""
Setup script for Fabric & Power BI MCP for Claude Desktop.
Installs all three MCP servers and writes claude_desktop_config.json.
"""

import io
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent.resolve()
FABRIC_CORE = HERE / "fabric-core"
TRANSLATION_AUDIT = HERE / "translation-audit"
BIN_DIR = HERE / "bin"


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


def find_pbimcp_in_vscode():
    """Check if powerbi-modeling-mcp.exe is already installed via VS Code extension."""
    vscode_ext_dir = Path.home() / ".vscode" / "extensions"
    if not vscode_ext_dir.exists():
        return None
    for d in sorted(vscode_ext_dir.iterdir(), reverse=True):
        if d.name.startswith("analysis-services.powerbi-modeling-mcp"):
            exe = d / "server" / "powerbi-modeling-mcp.exe"
            if exe.exists():
                return exe
    return None


def get_latest_pbimcp_version():
    url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    payload = json.dumps({
        "filters": [{"criteria": [{"filterType": 7, "value": "analysis-services.powerbi-modeling-mcp"}]}],
        "flags": 529,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1",
            "User-Agent": "fabric-powerbi-mcp-setup/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data["results"][0]["extensions"][0]["versions"][0]["version"]


def download_pbimcp_exe():
    """Download powerbi-modeling-mcp.exe from the VS Marketplace VSIX."""
    exe_path = BIN_DIR / "powerbi-modeling-mcp.exe"
    if exe_path.exists():
        print(f"  Already downloaded: {exe_path}")
        return exe_path

    print("  Fetching latest version from marketplace...")
    version = get_latest_pbimcp_version()
    print(f"  Version: {version}")

    vsix_url = (
        f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/"
        f"analysis-services/vsextensions/powerbi-modeling-mcp/{version}/"
        f"vspackage?targetPlatform=win32-x64"
    )
    print("  Downloading VSIX...")
    with urllib.request.urlopen(vsix_url, timeout=60) as resp:
        vsix_data = resp.read()

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(vsix_data)) as z:
        z.extract("extension/server/powerbi-modeling-mcp.exe", BIN_DIR)

    extracted = BIN_DIR / "extension" / "server" / "powerbi-modeling-mcp.exe"
    extracted.rename(exe_path)
    shutil.rmtree(BIN_DIR / "extension", ignore_errors=True)

    print(f"  Saved: {exe_path}")
    return exe_path


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

# ── Step 4: translation-audit venv ───────────────────────────────────────────
step(4, "Setting up translation-audit virtual environment...")
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

# ── Step 5: powerbi-modeling exe ─────────────────────────────────────────────
step(5, "Locating powerbi-modeling MCP server...")
pbimcp_exe = find_pbimcp_in_vscode()
if pbimcp_exe:
    print(f"  Found in VS Code extensions: {pbimcp_exe}")
else:
    if platform.system() != "Windows":
        print("  SKIP: powerbi-modeling-mcp.exe is Windows-only.")
        pbimcp_exe = None
    else:
        print("  Not found in VS Code. Downloading from marketplace...")
        try:
            pbimcp_exe = download_pbimcp_exe()
        except Exception as e:
            print(f"  WARNING: Download failed ({e}). Skipping powerbi-modeling.")
            pbimcp_exe = None

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
config["mcpServers"]["powerbi-translation-audit"] = {
    "command": str(venv_python),
    "args": [str(TRANSLATION_AUDIT / "server.py")],
}
if pbimcp_exe:
    config["mcpServers"]["powerbi-modeling"] = {
        "command": str(pbimcp_exe),
        "args": ["--start"],
    }

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print(f"  Written: {config_path}")

# ── Done ─────────────────────────────────────────────────────────────────────
servers = ["fabric-core", "powerbi-translation-audit"] + (["powerbi-modeling"] if pbimcp_exe else [])
print(f"\nSetup complete! Configured: {', '.join(servers)}")
print("Restart Claude Desktop to apply.")
if not pbimcp_exe:
    print("Note: powerbi-modeling skipped (install VS Code extension or retry on Windows).")
