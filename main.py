import time
from core.fetch import fetch_sub
from core.parse import parse_vless, parse_vmess
from core.cache import load_cache, save_cache
from core.builder import build_clash, build_v2rayng

subs = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no2.txt",
]

def update_cache(cache, proxies):
    new_cache = cache.copy()

    for p in proxies:
        key = f"{p['type']}:{p['server']}:{p['port']}:{p['uuid']}"

        new_cache[key] = {
            "config": p,
            "updated": int(time.time())
        }

    return new_cache


def main():
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

    if clash:
        import yaml
        with open("clash.yaml", "w") as f:
            yaml.dump(clash, f, allow_unicode=True)

    if v2rayng:
        with open("v2rayng.txt", "w") as f:
            f.write(v2rayng)

    print("DONE:", len(cache))


if __name__ == "__main__":
    main()
