# nReader v1.1
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os

def checkForTitle(uid: str) -> str:
    """
    Check if a title exists for a given UID.
    Returns:
        - "Yes" for save data
        - "vX" for regular titles where X is the version
        - "No" if the TMD file is missing
    """
    try:
        major, minor = uid.split('-')
        tmdPath = os.path.join("temp", "title", major, minor, "content", "title.tmd")
        with open(tmdPath, "rb") as f:
            # System title
            if major == "00010000":
                return "Yes"
            # Read version from TMD file at offset 0x01DC
            f.seek(0x01DC)
            versionBytes = f.read(2)
            version = (versionBytes[0] << 8) + versionBytes[1]
            return f"v{version}"
    except FileNotFoundError:
        return "No"
    except Exception:
        return "No"

def checkForTicket(uid: str) -> str:
    """
    Check if a ticket exists for a given UID.
    Returns:
        - "N/A" for save data
        - "Yes" if the ticket exists
        - "No" if the ticket is missing
    """
    try:
        major, minor = uid.split('-')
        if major == "00010000":
            return "N/A"
        tikPath = os.path.join("temp", "ticket", major, f"{minor}.tik")
        return "Yes" if os.path.isfile(tikPath) else "No"
    except Exception:
        return "No"
