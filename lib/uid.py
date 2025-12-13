# nReader v1.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import json, os

# =========================
# Title type definitions
# =========================
TYPES = {
    "00000000": "Development title",
    "00000001": "System title",
    "00010000": "Save data",
    "00010001": "Installed title",
    "00010002": "Preinstalled channel",
    "00010004": "Game channel",
    "00010005": "DLC",
    "00010008": "Hidden title",
}

# =========================
# Static name databases
# =========================
DEV_NAMES = {
    "87654321": "sdboot2",
}

SYS_SPECIAL_NAMES = {
    "00000000": "IOS Superuser",
    "00000001": "boot1 glitch",
    "00000002": "System Menu",
    "00000100": "BC",
    "00000101": "MIOS",
}

SPECIAL_IDS = {
    "00010001-af1bf516": "Homebrew Channel",
    "00010000-0000dead": "0000dead factory disc"
}

# =========================
# Helpers
# =========================
def loadGidDatabase(jsonPath: str) -> dict:
    """Load a GID-based name database from JSON; return empty dict if missing or invalid."""
    if not os.path.isfile(jsonPath):
        return {}
    try:
        with open(jsonPath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def resolveSystemTitle(minor: str) -> str:
    """Return a friendly name for system titles (IOS, BC, MIOS, etc.)."""
    if minor in SYS_SPECIAL_NAMES:
        return SYS_SPECIAL_NAMES[minor]
    try:
        iosNumber = int(minor, 16)
    except ValueError:
        return ""
    if 1 <= iosNumber <= 255:
        return f"IOS{iosNumber}"
    return ""

def resolveTitleName(titleType: str, minor: str, gid: str, gidDb: dict, fullId: str) -> str:
    """
    Resolve a title's display name based on its type and ID.
    Fallbacks:
        1. DEV_NAMES for development titles
        2. resolveSystemTitle for system titles
        3. SPECIAL_IDS for hard-coded full ID exceptions
        4. gidDb lookup
    """
    if titleType == "Development title":
        return DEV_NAMES.get(minor, "")
    if titleType == "System title":
        return resolveSystemTitle(minor)
    if fullId in SPECIAL_IDS:
        return SPECIAL_IDS[fullId]
    # Lookup by GID, try fallback if starting with 'U'
    name = gidDb.get(gid)
    if not name and gid.startswith("U"):
        altGid = "R" + gid[1:]
        name = gidDb.get(altGid, "")
    return name or ""

# =========================
# UID.sys parsing
# =========================
def readUidSys(uidSysPath: str, gidDbPath: str) -> dict:
    """
    Parse the Wii's uid.sys file and return a dictionary of entries with resolved names.
    
    Returns:
        { titleId: { "gid": str, "type": str, "name": str } }
    """
    gidDb = loadGidDatabase(gidDbPath)
    uidEntries = {}

    if not os.path.isfile(uidSysPath):
        return uidEntries

    with open(uidSysPath, "rb") as uidFile:
        while True:
            block = uidFile.read(12)
            if not block:
                break
            # skip all-zero blocks
            if block == b'\x00' * 12:
                continue

            major = "".join(f"{b:02x}" for b in block[0:4])
            minor = "".join(f"{b:02x}" for b in block[4:8])
            titleId = f"{major}-{minor}"

            # GID is stored in bytes 4-7, non-printable replaced by '.'
            gid = "".join(chr(b) if 32 <= b <= 126 else "." for b in block[4:8])

            titleType = TYPES.get(major, "Unknown")
            titleName = resolveTitleName(titleType, minor, gid, gidDb, titleId)

            uidEntries[titleId] = {
                "gid": gid,
                "type": titleType,
                "name": titleName,
            }


    return uidEntries
