# nReader v1.0
# Copyright (C) 2009 Ben Wilson
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os

def checkForTitle(id):
    try:
        major, minor = id.split('-')
        tmdPath = os.path.join("temp", "title", major, minor, "content", "title.tmd")
        with open(tmdPath, "rb") as f:
            if major == "00010000":
                return "\033[32mYes\033[0m"
            f.seek(0x01DC)
            versionBytes = f.read(2)
            version = (versionBytes[0] << 8) + versionBytes[1]
            return f"\033[32mv{version}\033[0m"
    except FileNotFoundError:
        return "\033[31mNo\033[0m"
    
def checkForTicket(id):
    major, minor = id.split('-')
    if major == "00010000":
        return "\033[90mN/A\033[0m"
    tmdPath = os.path.join("temp", "ticket", major, f"{minor}.tik")
    if os.path.isfile(tmdPath):
        return "\033[32mYes\033[0m"
    return "\033[31mNo\033[0m"