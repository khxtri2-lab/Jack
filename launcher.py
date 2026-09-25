#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ LAUNCHER — Render Edition
- Loads proxies
- Downloads gooning.py from GitHub
- Runs gooning.py with proxy
"""

import os
import sys
import time
import random
import requests
import tempfile
import subprocess
from flask import Flask
from threading import Thread

# ============================================================
# 🔥 CONFIG — APNA REPO
# ============================================================
GOONING_URL = "https://raw.githubusercontent.com/khxtri2-lab/Jack/main/gooning.py"
PROXIES_FILE = "proxies.txt"

# ============================================================
# 🔥 PROXY MANAGER
# ============================================================
_proxy_list = []


def load_proxies():
    global _proxy_list
    proxies = []
    
    env_proxies = os.environ.get("PROXIES", "").strip()
    if env_proxies:
        for p in env_proxies.split(","):
            p = p.strip()
            if p:
                proxies.append(p)
    
    if not proxies and os.path.exists(PROXIES_FILE):
        with open(PROXIES_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
    
    _proxy_list = proxies
    print(f"✅ Loaded {len(proxies)} proxies")
    return proxies


def normalize_proxy(p):
    if not p:
        return None
    p = p.strip()
    if p.startswith(("http://", "https://", "socks4://", "socks5://")):
        return p
    if "@" in p:
        return f"http://{p}"
    if p.count(":") == 3:
        parts = p.split(":")
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    if p.count(":") == 1:
        return f"http://{p}"
    return f"http://{p}"


# ============================================================
# 🔥 FLASK KEEP-ALIVE
# ============================================================
app = Flask('')


@app.route('/')
def home():
    return "✅ Launcher is alive!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print(f"✅ Flask Keep-Alive on port {os.environ.get('PORT', 10000)}")


# ============================================================
# 🔥 MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  ⚡ LAUNCHER — Render Edition")
    print("=" * 60)
    
    load_proxies()
    
    print(f"\n📥 Downloading gooning.py...")
    try:
        r = requests.get(GOONING_URL, timeout=30)
        if r.status_code != 200:
            print(f"❌ Download failed: HTTP {r.status_code}")
            sys.exit(1)
        
        temp_path = os.path.join(tempfile.gettempdir(), "gooning.py")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"✅ Saved to {temp_path}")
    except Exception as e:
        print(f"❌ Download error: {e}")
        sys.exit(1)
    
    env = os.environ.copy()
    if _proxy_list:
        proxy = normalize_proxy(random.choice(_proxy_list))
        env["HTTP_PROXY"] = proxy
        env["HTTPS_PROXY"] = proxy
        env["http_proxy"] = proxy
        env["https_proxy"] = proxy
        print(f"🌐 Proxy set: {proxy[:50]}...")
    else:
        print("⚠️ No proxies — running without proxy")
    
    print(f"\n▶ Running gooning.py...")
    try:
        subprocess.run(
            [sys.executable, "-u", temp_path],
            env=env,
            check=False,
        )
    except KeyboardInterrupt:
        print("\n⏹ Stopped by user")
    except Exception as e:
        print(f"❌ Run error: {e}")


if __name__ == "__main__":
    keep_alive()
    main()
