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
            return {"exists": False, "error": f"HTTP {response.status_code}", "entries": []}
        data = response.json()
        if "entries" not in data:
            data["entries"] = []
        return data
    except requests.RequestException as e:
        return {"exists": False, "error": str(e), "entries": []}

def prepareJson(uidEntries, serial, serialNand, username, existing_entries=None):
    """
    Format UID entries and metadata for JSON export.
    Avoid adding entries that already exist on the server.

    :param uidEntries: dict of local UID entries
    :param serial: console serial
    :param serialNand: NAND serial
    :param username: user
    :param existing_entries: list of dicts from server (with 'id' or 'gid')
    """
    jsonData = {
        "serial": serial,
        "serialNand": serialNand,
        "username": username,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }
    existing_ids = set(e.get("id") for e in existing_entries) if existing_entries else set()
    start_pos = 1
    if existing_entries:
        existing_positions = [e.get("position", 0) for e in existing_entries]
        if existing_positions:
            start_pos = max(existing_positions) + 1
    for entry_uid, entry_data in uidEntries.items():
        if entry_uid in existing_ids:
            continue
        jsonData["entries"].append({
            "position": start_pos + len(jsonData["entries"]),
            "id": entry_uid,
            "gid": entry_data.get("gid", ""),
            "type": entry_data.get("type", ""),
            "name": entry_data.get("name", ""),
            "title": entry_data.get("title", ""),
            "ticket": entry_data.get("ticket", "")
        })
    return jsonData

def exportJson(uidEntries, serial, serialNand, username, phpUrl, existing_entries=None):
    """
    Export UID entries to PHP backend. Only sends new entries.
    """
    headers = {"Content-Type": "application/json"}
    jsonData = prepareJson(uidEntries, serial, serialNand, username, existing_entries)
    if not jsonData["entries"]:
        return {"success": True, "message": "No new entries to upload"}
    try:
        response = requests.post(phpUrl, json=jsonData, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}