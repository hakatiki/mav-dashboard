import requests, json, pandas as pd

url = "https://jegy-a.mav.hu/IK_API_PROD/api/OfferRequestAPI/GetStationList"
stations = requests.post(url, json={}, timeout=60).json()
with open("stations.json", "w", encoding="utf-8") as f:
    json.dump(stations, f, ensure_ascii=False, indent=4)
