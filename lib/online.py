# nReader 2.0
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import requests
from datetime import datetime

def prepareJson(uidEntries: dict, serialNumber: str, username: str) -> dict:
    """
    Format UID entries and metadata for JSON export,
    including the 'position' field to preserve order.
    """
    jsonData = {
        "serial": serialNumber,
        "user": username,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }
    for pos, (uid, entry) in enumerate(uidEntries.items(), start=1):
        jsonData["entries"].append({
            "id": uid,
            "gid": entry.get("gid", ""),
            "type": entry.get("type", ""),
            "name": entry.get("name", ""),
            "title": entry.get("title", ""),
            "ticket": entry.get("ticket", ""),
            "position": pos
        })
    return jsonData
    
def exportJson(uidEntries: dict, serialNumber: str, username: str, phpUrl: str, debug: bool = False) -> bool:
    """
    Send the formatted UID data to the PHP upload script.
    Returns True only if the server confirms success.
    """
    jsonData = prepareJson(uidEntries, serialNumber, username)
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(phpUrl, json=jsonData, headers=headers, timeout=15)
        if response.status_code != 200:
            if debug:
                print(f"HTTP error: {response.status_code}")
            return False

        data = response.json()
        if debug and "errors" in data and data["errors"]:
            print(f"Server returned {len(data['errors'])} entry errors:")
            for e in data["errors"]:
                entry = e.get("entry", {})
                error_msg = e.get("error", "")
                print(f"  Entry {entry} -> {error_msg}")

        return data.get("success", False)

    except Exception as e:
        if debug:
            print("Request exception:", e)
        return False