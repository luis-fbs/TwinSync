import requests

import config as cfg


r = requests.put(f"{cfg.DITTO_URL}/api/2/policies/{cfg.THING_ID}", json=cfg.POLICY, auth=cfg.DITTO_AUTH)
r.raise_for_status()

r = requests.put(f"{cfg.DITTO_URL}/api/2/things/{cfg.THING_ID}", json=cfg.THING, auth=cfg.DITTO_AUTH)
r.raise_for_status()

conn_url = f"{cfg.DITTO_URL}/api/2/connections"
for c in requests.get(conn_url, auth=cfg.DITTO_DEVOPS_AUTH).json():
    if c["name"] == cfg.CONNECTION["name"]:
        requests.delete(f"{conn_url}/{c['id']}", auth=cfg.DITTO_DEVOPS_AUTH)

r = requests.post(conn_url, json=cfg.CONNECTION, auth=cfg.DITTO_DEVOPS_AUTH)
r.raise_for_status()
