# nReader 2.0
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import requests
from datetime import datetime

def prepareJson(uidEntries: dict, serialNumber: str, username: str) -> dict:
    """
    Format UID entries and metadata for JSON export.
    """
    jsonData = {
        "serial": serialNumber,
        "user": username,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }
    for uid, entry in uidEntries.items():
        jsonData["entries"].append({
            "id": uid,
            "gid": entry.get("gid", ""),
            "type": entry.get("type", ""),
            "name": entry.get("name", ""),
            "title": entry.get("title", ""),
            "ticket": entry.get("ticket", "")
        })
    return jsonData
    
def exportJson(uidEntries: dict, serialNumber: str, username: str, phpUrl: str) -> bool:
    """
    Send the formatted UID data to the PHP upload script.
    """
    jsonData = prepareJson(uidEntries, serialNumber, username)
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(phpUrl, json=jsonData, headers=headers, timeout=15)
        return response.status_code == 200
    except Exception as e:
        return False
