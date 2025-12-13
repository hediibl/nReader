# nReader v1.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os

def checkForTitle(uid: str) -> str:
    """
    Check if a title exists for a given UID.
    Args:
        uid (str): UID in the format 'major-minor'
    Returns:
        - "Yes" for save data if the TMD file exists
        - "vX" for installed/preinstalled/hidden/game titles (version from title.tmd)
        - "No" if the TMD file is missing or unreadable
    """
    try:
        major, minor = uid.split('-')
        # Save data are always "Yes" if content exists
        if major == "00010000":
            tmdPath = os.path.join("temp", "title", major, minor, "content", "title.tmd")
            return "Yes" if os.path.isfile(tmdPath) else "No"

        # Other titles: read version from title.tmd
        tmdPath = os.path.join("temp", "title", major, minor, "content", "title.tmd")
        if not os.path.isfile(tmdPath):
            return "No"

        with open(tmdPath, "rb") as tmdFile:
            tmdFile.seek(0x01DC)
            versionBytes = tmdFile.read(2)
            if len(versionBytes) < 2:
                return "No"
            version = (versionBytes[0] << 8) | versionBytes[1]
            return f"v{version}"

    except Exception:
        # Catch-all fallback
        return "No"


def checkForTicket(uid: str) -> str:
    """
    Check if a ticket exists for a given UID.
    Args:
        uid (str): UID in the format 'major-minor'
    Returns:
        - "N/A" for save data
        - "Yes" if the ticket file exists
        - "No" if missing or unreadable
    """
    try:
        major, minor = uid.split('-')
        if major == "00010000":
            return "N/A"

        tikPath = os.path.join("temp", "ticket", major, f"{minor}.tik")
        return "Yes" if os.path.isfile(tikPath) else "No"

    except Exception:
        # Fallback in case of unexpected error
        return "No"