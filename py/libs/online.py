# nReader 2.5
# Copyright (C) 2026 hediibl
# Licensed under the GNU GPL v3

import requests
from datetime import datetime, timezone


def checkSerialOnServer(serial, phpUrl):
    """
    Check if a serial already exists on the server.
    """
    try:
        response = requests.get(f"{phpUrl}?checkSerial={serial}", timeout=10)
        if response.status_code != 200:
            return {"exists": False, "errorCode": "HTTP_ERROR"}
        return response.json()
    except requests.RequestException:
        return {"exists": False, "errorCode": "NETWORK_ERROR"}


def prepareJson(uidEntries, serial, serialNand, username, description=""):
    """
    Format UID entries and metadata for JSON export.

    :param uidEntries: dict of local UID entries
    :param serial: str, user-declared serial
    :param serialNand: str, serial detected from NAND
    :param username: str, uploader username
    :param description: str, optional description
    :return: dict, JSON-ready payload
    """
    jsonData = {
        "serial": serial,
        "serialNand": serialNand,
        "username": username,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "entries": []
    }
    position = 1
    for entryUid, entryData in uidEntries.items():
        jsonData["entries"].append({
            "position": position,
            "id": entryUid,
            "title": entryData.get("title", ""),
            "ticket": entryData.get("ticket", "")
        })
        position += 1
    return jsonData


def exportJson(uidEntries, serial, serialNand, username, phpUrl, description=""):
    """
    Export UID entries and optional description to PHP backend.
    """
    headers = {"Content-Type": "application/json"}
    jsonData = prepareJson(uidEntries, serial, serialNand, username, description)

    try:
        response = requests.post(
            phpUrl,
            json=jsonData,
            headers=headers,
            timeout=15
        )
        if response.status_code != 200:
            return {"success": False, "errorCode": "HTTP_ERROR"}
        return response.json()
    except requests.RequestException:
        return {"success": False, "errorCode": "NETWORK_ERROR"}