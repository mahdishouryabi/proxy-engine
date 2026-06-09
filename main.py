import requests
import base64
import os
import json
import time
import socket

CACHE_FILE = "cache.json"
MERGE_FILE = "sub.txt"
V2RAY_FILE = "v2rayng_sub.txt"

FAIL_LIMIT = 3
TIMEOUT = 4
TEST_URL = "http://www.gstatic.com/generate_204"

subs = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no2.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no3.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no4.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no6.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no8.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no9.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no10.txt",
]


# -------------------------
# SAFE CACHE LOAD
# -------------------------
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        data = json.load(open(CACHE_FILE, "r"))

        # 🔥 FIX: اگر خراب یا list بود
        if not isinstance(data, dict):
            return {}

        return data

    except:
        return {}


def save_cache(cache):
    if not isinstance(cache, dict):
        cache = {}

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# -------------------------
# FETCH
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
# LATENCY TEST
# -------------------------
def latency_test():
    try:
        start = time.time()
        r = requests.get(TEST_URL, timeout=TIMEOUT)
        if r.status_code not in [200, 204]:
            return None
        return int((time.time() - start) * 1000)
    except:
        return None


# -------------------------
# TCP TEST
# -------------------------
def tcp_test(host, port):
    try:
        start = time.time()
        s = socket.create_connection((host, port), timeout=TIMEOUT)
        s.close()
        return int((time.time() - start) * 1000)
    except:
        return None


# -------------------------
# SCORE ENGINE
# -------------------------
def score_proxy(host, port):
    tcp = tcp_test(host, port)
    http = latency_test()

    if tcp is None:
        return None

    score = 0

    if tcp < 200:
        score += 50
    elif tcp < 500:
        score += 30
    else:
        score += 10

    if http:
        if http < 300:
            score += 50
        elif http < 800:
            score += 30
        else:
            score += 10

    return score


# -------------------------
# PARSE
# -------------------------
def parse(line, idx):
    if line.startswith("vless://"):
        return {
            "name": f"proxy-{idx}",
            "type": "vless",
            "raw": line
        }

    if line.startswith("vmess://"):
        return {
            "name": f"proxy-{idx}",
            "type": "vmess",
            "raw": line
        }

    return None


# -------------------------
# UPDATE CACHE (FIXED)
# -------------------------
def update_cache(cache, proxies):
    if not isinstance(cache, dict):
        cache = {}

    new_cache = dict(cache)

    for p in proxies:
        key = p["raw"]

        if key not in new_cache:
            new_cache[key] = {
                "fail": 0,
                "score": 0,
                "last_ok": 0,
                "config": p
            }

        entry = new_cache[key]

        # فقط vless تست دقیق (vmess فعلاً skip)
        if p["type"] != "vless":
            continue

        try:
            host_port = p["raw"].split("@")[1].split("?")[0]
            host, port = host_port.split(":")
        except:
            continue

        s = score_proxy(host, port)

        if s is None:
            entry["fail"] += 1
        else:
            entry["score"] = s
            entry["fail"] = 0
            entry["last_ok"] = int(time.time())
            entry["config"] = p

        if entry["fail"] >= FAIL_LIMIT:
            continue

        new_cache[key] = entry

    # حذف fail شده‌ها
    return {
        k: v for k, v in new_cache.items()
        if isinstance(v, dict) and v.get("fail", 0) < FAIL_LIMIT
    }


# -------------------------
# BUILD OUTPUT (TOP 10)
# -------------------------
def build_output(cache):
    items = list(cache.values())

    # فقط valid ها
    items = [i for i in items if isinstance(i, dict)]

    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    items = items[:10]

    return [i["config"]["raw"] for i in items if "config" in i]


# -------------------------
# MAIN
# -------------------------
def main():
    cache = load_cache()

    all_lines = []
    for s in subs:
        all_lines.extend(fetch_sub(s))

    all_lines = list(dict.fromkeys(all_lines))

    proxies = []
    for i, line in enumerate(all_lines):
        p = parse(line, i)
        if p:
            proxies.append(p)

    cache = update_cache(cache, proxies)
    save_cache(cache)

    best = build_output(cache)

    with open(MERGE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(best))

    encoded = base64.b64encode("\n".join(best).encode()).decode()
    with open(V2RAY_FILE, "w", encoding="utf-8") as f:
        f.write(encoded)

    print("DONE")
    print("best proxies:", len(best))


if __name__ == "__main__":
    main()
