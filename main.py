import requests
import base64
import os
import json

CACHE_FILE = "cache.json"
MERGE_FILE = "sub.txt"

subs = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no2.txt",
    # ... بقیه منابع
]

# -------------------------
# LOAD CACHE (برای تکراری)
# -------------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            return set(json.load(open(CACHE_FILE)))
        except:
            return set()
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f, indent=2)

# -------------------------
# FETCH RAW
# -------------------------
def fetch_sub(url):
    try:
        r = requests.get(url, timeout=15)
        return [x.strip() for x in r.text.splitlines() if x.strip()]
    except:
        return []

# -------------------------
# MAIN
# -------------------------
def main():
    cache = load_cache()
    all_lines = []

    for s in subs:
        lines = fetch_sub(s)
        all_lines.extend(lines)

    all_lines = list(dict.fromkeys(all_lines))  # حذف تکراری‌ها
    cache.update(all_lines)

    # ذخیره cache برای دفعه بعد
    save_cache(cache)

    # ذخیره فایل merge
    with open(MERGE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))

    # خروجی v2rayng هم می‌خوای، فقط base64
    raw = "\n".join(all_lines)
    v2rayng_encoded = base64.b64encode(raw.encode()).decode()
    with open("v2rayng_sub.txt", "w") as f:
        f.write(v2rayng_encoded)

    print("DONE")
    print("configs:", len(all_lines))


if __name__ == "__main__":
    main()
