# nReader 2.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import requests
from datetime import datetime, timezone

def checkSerialOnServer(serial, phpUrl):
    """
    Check if a serial already exists on the server.

    :param serial: str, console serial
    :param phpUrl: str, backend URL
    :return: dict with keys:
        - exists (bool)
        - username (str)
        - date (str)
        - entries (list)
        - error (str, optional)
    """
    try:
        response = requests.get(f"{phpUrl}?checkSerial={serial}", timeout=10)
        if response.status_code != 200:
            return {"exists": False, "error": f"HTTP {response.status_code}"}
        return response.json()
    except requests.RequestException as e:
        return {"exists": False, "error": str(e)}

def prepareJson(uidEntries, serial, serialNand, username, existing_positions=None):
    """
    Format UID entries and metadata for JSON export.
    Includes 'position' field to preserve entry order and append after existing entries.
    """
    jsonData = {
        "serial": serial,
        "serialNand": serialNand,
        "username": username,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }
    start_pos = 1
    if existing_positions:
        start_pos = max(existing_positions) + 1
    for offset, (uid, entry) in enumerate(uidEntries.items()):
        jsonData["entries"].append({
            "position": start_pos + offset,
            "id": uid,
            "gid": entry.get("gid", ""),
            "type": entry.get("type", ""),
            "name": entry.get("name", ""),
            "title": entry.get("title", ""),
            "ticket": entry.get("ticket", "")
        })
    return jsonData

def exportJson(uidEntries, serial, serialNand, username, phpUrl, existing_positions=None):
    """
    Export UID entries to PHP backend.
    """
    headers = {"Content-Type": "application/json"}
    jsonData = prepareJson(uidEntries, serial, serialNand, username, existing_positions)
    if not jsonData["entries"]:
        return {"success": True, "message": "No new entries to upload"}
    try:
        response = requests.post(phpUrl, json=jsonData, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}