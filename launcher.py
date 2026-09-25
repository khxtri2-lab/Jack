#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ LAUNCHER — Render Edition (AUTO PROXY FETCH)
- Auto-fetches proxies from multiple sources
- Tests and filters working proxies
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
import concurrent.futures
from flask import Flask
from threading import Thread

# ============================================================
# 🔥 CONFIG
# ============================================================
GOONING_URL = "https://raw.githubusercontent.com/khxtri2-lab/Jack/main/gooning.py"
PROXIES_FILE = "proxies.txt"

# 🔥 FREE PROXY SOURCES
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
]

# 🔥 TEST URL (fast)
TEST_URL = "https://api.ipify.org?format=json"
TEST_TIMEOUT = 8
MAX_WORKERS = 100  # threads for testing


# ============================================================
# 🔥 PROXY FETCHER
# ============================================================
def fetch_proxies():
    """Fetch proxies from all sources."""
    print("\n" + "=" * 60)
    print("  🌐 FETCHING PROXIES FROM SOURCES")
    print("=" * 60)
    
    all_proxies = set()
    
    for url in PROXY_SOURCES:
        try:
            src_name = url.split("/")[-1]
            print(f"⬇ {src_name}...", end=" ")
            r = requests.get(url, timeout=20)
            
            if r.status_code != 200:
                print(f"❌ HTTP {r.status_code}")
                continue
            
            count = 0
            for line in r.text.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                if line.startswith("#"):
                    continue
                
                # Determine protocol from URL
                if "socks5" in url.lower():
                    proxy = f"socks5://{line}"
                elif "socks4" in url.lower():
                    proxy = f"socks4://{line}"
                else:
                    proxy = f"http://{line}"
                
                all_proxies.add(proxy)
                count += 1
            
            print(f"✅ {count}")
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
    
    print(f"\n📊 Total unique proxies: {len(all_proxies)}")
    return list(all_proxies)


# ============================================================
# 🔥 PROXY TESTER
# ============================================================
def test_proxy(proxy):
    """Test if proxy works for HTTPS."""
    try:
        r = requests.get(
            TEST_URL,
            proxies={"http": proxy, "https": proxy},
            timeout=TEST_TIMEOUT
        )
        if r.status_code == 200:
            return (proxy, True)
        return (proxy, False)
    except:
        return (proxy, False)


def filter_working_proxies(proxies):
    """Test all proxies and return working ones."""
    print("\n" + "=" * 60)
    print(f"  🧪 TESTING {len(proxies)} PROXIES")
    print("=" * 60)
    print(f"  ⏳ This takes 30-60 seconds...\n")
    
    working = []
    tested = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(test_proxy, p): p for p in proxies}
        
        for future in concurrent.futures.as_completed(futures):
            tested += 1
            proxy, ok = future.result()
            if ok:
                working.append(proxy)
                print(f"  ✅ {proxy}")
            
            # Progress
            if tested % 100 == 0:
                print(f"  📊 Progress: {tested}/{len(proxies)} | Working: {len(working)}")
    
    print(f"\n✅ Working proxies: {len(working)}/{len(proxies)}")
    return working


# ============================================================
# 🔥 PROXY MANAGER
# ============================================================
_proxy_list = []


def load_proxies():
    """Fetch, test, and save working proxies."""
    global _proxy_list
    
    # 1. Try to load existing proxies.txt first
    if os.path.exists(PROXIES_FILE):
        try:
            with open(PROXIES_FILE) as f:
                existing = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            if existing:
                print(f"📁 Found existing {PROXIES_FILE} with {len(existing)} proxies")
                # Quick test
                working = filter_working_proxies(existing[:50])  # Test first 50
                if len(working) >= 5:
                    _proxy_list = working
                    print(f"✅ Reusing {len(working)} working proxies")
                    return working
                else:
                    print(f"⚠️ Only {len(working)} working — fetching fresh")
        except Exception as e:
            print(f"⚠️ Could not read existing: {e}")
    
    # 2. Fetch fresh proxies
    print("\n🔄 Fetching fresh proxies...")
    raw_proxies = fetch_proxies()
    
    if not raw_proxies:
        print("❌ No proxies fetched!")
        return []
    
    # 3. Random sample for testing (testing all is too slow)
    sample_size = min(500, len(raw_proxies))
    sample = random.sample(raw_proxies, sample_size)
    print(f"\n🎲 Testing {sample_size} random proxies from {len(raw_proxies)}")
    
    # 4. Filter working
    working = filter_working_proxies(sample)
    
    # 5. Save to file
    if working:
        with open(PROXIES_FILE, "w") as f:
            for p in working:
                f.write(f"{p}\n")
        print(f"✅ Saved {len(working)} working proxies to {PROXIES_FILE}")
    
    _proxy_list = working
    return working


def normalize_proxy(p):
    if not p:
        return None
    p = p.strip()
    if p.startswith(("http://", "https://", "socks4://", "socks5://")):
        return p
    if "@" in p:
        return f"http://{p}"
    if p.count(":") == 1:
        return f"http://{p}"
    return f"http://{p}"


# ============================================================
# 🔥 FLASK KEEP-ALIVE
# ============================================================
app = Flask('')


@app.route('/')
def home():
    return f"✅ Launcher alive | {len(_proxy_list)} proxies"


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
    print("  ⚡ LAUNCHER — AUTO PROXY FETCH")
    print("=" * 60)
    
    # 🔥 1. Load proxies (auto-fetch if needed)
    load_proxies()
    
    if not _proxy_list:
        print("\n⚠️ No working proxies — running without proxy")
    else:
        print(f"\n✅ Ready with {len(_proxy_list)} proxies")
    
    # 🔥 2. Download gooning.py
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
    
    # 🔥 3. Set proxy env
    env = os.environ.copy()
    if _proxy_list:
        proxy = normalize_proxy(random.choice(_proxy_list))
        env["HTTP_PROXY"] = proxy
        env["HTTPS_PROXY"] = proxy
        env["http_proxy"] = proxy
        env["https_proxy"] = proxy
        print(f"🌐 Proxy set: {proxy[:60]}")
    
    # 🔥 4. Run gooning.py
    print(f"\n▶ Running gooning.py...")
    print("=" * 60 + "\n")
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


# ============================================================
# 🔥 START
# ============================================================
if __name__ == "__main__":
    keep_alive()
    main()
