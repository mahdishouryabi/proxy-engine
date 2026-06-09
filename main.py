import requests
import yaml
import base64
import json
import time
import os
from urllib.parse import urlparse, parse_qs

CACHE_FILE = "cache.json"

TEST_URL = "http://www.gstatic.com/generate_204"
FAIL_THRESHOLD = 3


# -------------------------
# CACHE
# -------------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# -------------------------
# FETCH SUB
# -------------------------
def fetch_sub(url):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []
        return [x.strip() for x in r.text.splitlines() if x.strip()]
    except:
        return []


# -------------------------
# TEST (SAFE)
# -------------------------
def test_server(host, port):
    try:
        requests.get(TEST_URL, timeout=5)
        return True
    except:
        return False


# -------------------------
# PARSE VLESS
# -------------------------
def parse_vless(link, name):
    try:
        p = urlparse(link)
        uuid, hp = p.netloc.split("@")
        host, port = hp.split(":")
        qs = parse_qs(p.query)

        return {
            "type": "vless",
            "name": name,
            "server": host,
            "port": int(port),
            "uuid": uuid,
            "tls": qs.get("security", ["none"])[0] == "tls"
        }
    except:
        return None


# -------------------------
# PARSE VMESS
# -------------------------
def parse_vmess(link, name):
    try:
        data = link.replace("vmess://", "")
        decoded = base64.b64decode(data + "==").decode()
        j = json.loads(decoded)

        return {
            "type": "vmess",
            "name": name,
            "server": j["add"],
            "port": int(j["port"]),
            "uuid": j["id"],
            "tls": j.get("tls") == "tls"
        }
    except:
        return None


# -------------------------
# CACHE UPDATE (STABLE)
# -------------------------
def update_cache(cache, proxies):
    new_cache = cache.copy()

    for p in proxies:
        key = f"{p['type']}:{p['server']}:{p['port']}:{p['uuid']}"

        if key not in new_cache:
            new_cache[key] = {
                "config": p,
                "fail": 0,
                "last_seen": int(time.time())
            }

        entry = new_cache[key]

        ok = test_server(p["server"], p["port"])

        if ok:
            entry["fail"] = 0
            entry["config"] = p
            entry["last_seen"] = int(time.time())
        else:
            entry["fail"] += 1

        if entry["fail"] >= FAIL_THRESHOLD:
            del new_cache[key]

    return new_cache


# -------------------------
# BUILD CLASH
# -------------------------
def build_clash(cache):
    proxies = [v["config"] for v in cache.values()]
    names = [p["name"] for p in proxies]

    return {
        "mixed-port": 7890,
        "mode": "rule",
        "allow-lan": True,

        "proxies": proxies,

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "url-test",
                "proxies": names,
                "url": TEST_URL,
                "interval": 300
            },
            {
                "name": "SELECT",
                "type": "select",
                "proxies": names + ["AUTO", "DIRECT"]
            }
        ],

        "rules": ["MATCH,SELECT"]
    }


# -------------------------
# BUILD V2RAYNG (RAW SUB)
# -------------------------
def build_v2rayng(cache):
    lines = []

    for v in cache.values():
        p = v["config"]

        if p["type"] == "vless":
            lines.append(
                f"vless://{p['uuid']}@{p['server']}:{p['port']}"
                f"?security={'tls' if p.get('tls') else 'none'}&type=tcp#{p['name']}"
            )

        elif p["type"] == "vmess":
            vm = {
                "v": "2",
                "ps": p["name"],
                "add": p["server"],
                "port": str(p["port"]),
                "id": p["uuid"],
                "net": "tcp",
                "tls": "tls" if p.get("tls") else ""
            }

            encoded = base64.b64encode(json.dumps(vm).encode()).decode()
            lines.append("vmess://" + encoded)

    return "\n".join(lines)  # ❗ مهم: خام، نه base64 شده


# -------------------------
# MAIN
# -------------------------
def main():
    subs = [
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no1.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no2.txt",
    ]

    cache = load_cache()

    all_links = []
    for s in subs:
        all_links += fetch_sub(s)

    proxies = []
    for i, c in enumerate(set(all_links)):
        p = None

        if c.startswith("vless://"):
            p = parse_vless(c, f"p{i}")
        elif c.startswith("vmess://"):
            p = parse_vmess(c, f"p{i}")

        if p:
            proxies.append(p)

    cache = update_cache(cache, proxies)
    save_cache(cache)

    clash = build_clash(cache)
    v2rayng = build_v2rayng(cache)

    # ❗ همیشه فایل ساخته میشه
    with open("clash.yaml", "w") as f:
        yaml.dump(clash if clash else {}, f, allow_unicode=True)

    with open("sub.txt", "w") as f:
        f.write(v2rayng if v2rayng else "")

    print("DONE")
    print("proxies:", len(cache))


if __name__ == "__main__":
    main()
