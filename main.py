import requests
import base64
import socket

TIMEOUT = 4
FAIL_LIMIT = 3
OUTPUT_FILE = "v2rayng_sub.txt"

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
# FETCH RAW
# -------------------------
def fetch(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        return [x.strip() for x in r.text.splitlines() if x.strip()]
    except:
        return []


# -------------------------
# REAL LIGHT TEST (NO MODIFY LINK)
# -------------------------
def test_link(line):
    try:
        if "@" not in line or ":" not in line:
            return False

        # فقط extract host/port برای تست TCP
        try:
            after = line.split("@")[1]
            host = after.split(":")[0]
            port = int(after.split(":")[1].split("?")[0])
        except:
            return False

        # TCP handshake test
        s = socket.create_connection((host, port), timeout=TIMEOUT)
        s.close()

        return True

    except:
        return False


# -------------------------
# MAIN
# -------------------------
def main():
    all_links = []

    # merge raw
    for s in subs:
        all_links.extend(fetch(s))

    # dedup بدون تغییر محتوا
    seen = set()
    unique = []

    for l in all_links:
        if l not in seen:
            seen.add(l)
            unique.append(l)

    # test + filter
    valid = []
    fail_counter = {}

    for l in unique:
        ok = test_link(l)

        if ok:
            valid.append(l)
        else:
            fail_counter[l] = fail_counter.get(l, 0) + 1

            # فقط بعد 3 fail حذف
            if fail_counter[l] < FAIL_LIMIT:
                valid.append(l)

    # output raw (IMPORTANT)
    raw = "\n".join(valid)

    encoded = base64.b64encode(raw.encode()).decode()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(encoded)

    print("DONE")
    print("input:", len(unique))
    print("output:", len(valid))


if __name__ == "__main__":
    main()
