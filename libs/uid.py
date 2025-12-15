# nReader 2.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, json

typesMap = {
    "00000000": "Development title",
    "00000001": "System title",
    "00010000": "Save data",
    "00010001": "Installed title",
    "00010002": "Preinstalled channel",
    "00010004": "Game channel",
    "00010005": "DLC",
    "00010008": "Hidden title",
}

specialIds = {
    "00000000-87654321": "sdboot2",
    "00000001-00000000": "IOS Superuser",
    "00000001-00000001": "boot1 glitch",
    "00000001-00000002": "System Menu",
    "00000001-00000100": "BC",
    "00000001-00000101": "MIOS",
}

def loadNamesDatabase(dbPath):
    """
    Load JSON database from a given path.

    :param dbPath: str, path to JSON file
    :return: dict, parsed JSON or empty dict if error
    """
    if not os.path.isfile(dbPath):
        raise RuntimeError("JSON database missing.")
    try:
        with open(dbPath, "r", encoding="utf-8") as dbFile:
            return json.load(dbFile)
    except (OSError, json.JSONDecodeError):
        return {}

def resolveIosName(minorId):
    """
    Calculate name for IOS.

    :param minorId: str, minor ID in hex
    :return: str, resolved IOS name or empty string
    """
    try:
        return f"IOS{int(minorId,16)}"
    except ValueError:
        return ""

def resolveTitleName(db, titleId, gid):
    """
    Resolve a title's name based on its ID and gid.

    :param db: dict, loaded names database
    :param titleId: str, title ID in format XXXX-XXXX
    :param gid: str, title's GID
    :return: str, resolved title name
    """
    major, minor = titleId[0:8], titleId[9:17]
    if titleId in specialIds:
        return specialIds[titleId]
    if major == "00000001":
        return resolveIosName(minor)
    if gid.startswith("U"):
        return db.get(gid) or db.get(f"R{gid[1:]}", "")
    return db.get(gid,"")

def checkForTitle(rootDir, titleId):
    """
    Check if a title exists in the NAND.

    :param rootDir: str, root path of NAND
    :param titleId: str, title ID in format XXXX-XXXX
    :return: str, "Yes"/"No" or version string like "v01"
    """
    try:
        major, minor = titleId.split("-")
        path = os.path.join(rootDir,"title",major,minor,"content","title.tmd")
        if major == "00010000":
            return "Yes" if os.path.isfile(path) else "No"
        if not os.path.isfile(path):
            return "No"
        with open(path,"rb") as tmdFile:
            tmdFile.seek(0x01DC)
            versionBytes = tmdFile.read(2)
            if len(versionBytes)<2:
                return "No"
            return f"v{(versionBytes[0]<<8)|versionBytes[1]}"
    except Exception:
        return "No"

def checkForTicket(rootDir, titleId):
    """
    Check if a ticket exists in the NAND.

    :param rootDir: str, root path of NAND
    :param titleId: str, title ID in format XXXX-XXXX
    :return: str, "Yes"/"No" or "N/A"
    """
    try:
        major, minor = titleId.split("-")
        if major == "00010000":
            return "N/A"
        ticketPath = os.path.join(rootDir,"ticket",major,f"{minor}.tik")
        return "Yes" if os.path.isfile(ticketPath) else "No"
    except Exception:
        return "No"

def readUidSys(rootDir, dbPath):
    """
    Parse the Wii's uid.sys file and return a dictionary of entries with resolved names.

    :param rootDir: str, root path of NAND
    :param dbPath: str, path to JSON names database
    :return: dict, UID entries with resolved names and status
    """
    uidEntries = {}
    uidPath = os.path.join(rootDir,"sys","uid.sys")
    if not os.path.isfile(uidPath):
        return uidEntries
    db = loadNamesDatabase(dbPath)
    with open(uidPath,"rb") as uidFile:
        while True:
            block = uidFile.read(12)
            if not block:
                break
            if block == b"\x00"*12:
                continue
            majorHex = "".join(f"{b:02x}" for b in block[0:4])
            minorHex = "".join(f"{b:02x}" for b in block[4:8])
            titleId = f"{majorHex}-{minorHex}"
            gid = "".join(chr(b) if 32<=b<=126 else "." for b in block[4:8])
            titleType = typesMap.get(majorHex,"Unknown")
            titleName = resolveTitleName(db,titleId,gid)
            titleStatus = checkForTitle(rootDir,titleId)
            ticketStatus = checkForTicket(rootDir,titleId)
            uidEntries[titleId] = {
                "gid": gid,
                "type": titleType,
                "name": titleName,
                "title": titleStatus,
                "ticket": ticketStatus
            }
    return uidEntries
