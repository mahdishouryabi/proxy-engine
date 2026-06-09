import base64
import yaml

def build_clash(cache):
    proxies = [v["config"] for v in cache.values()]

    names = [p["name"] for p in proxies]

    return {
        "mixed-port": 7890,
        "mode": "rule",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "select",
                "proxies": names + ["DIRECT"]
            }
        ],
        "rules": ["MATCH,AUTO"]
    }


def build_v2rayng(cache):
    out = set()

    for v in cache.values():
        p = v["config"]

        if p["type"] == "vless":
            out.add(
                f"vless://{p['uuid']}@{p['server']}:{p['port']}?"
                f"security={'tls' if p.get('tls') else 'none'}"
                f"&type=tcp#{p['name']}"
            )

        elif p["type"] == "vmess":
            import json

            vm = {
                "v": "2",
                "ps": p["name"],
                "add": p["server"],
                "port": str(p["port"]),
                "id": p["uuid"],
                "net": "tcp",
                "tls": "tls" if p.get("tls") else ""
            }

            out.add("vmess://" + base64.b64encode(json.dumps(vm).encode()).decode())

    return "\n".join(out)
