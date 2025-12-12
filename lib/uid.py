# nReader v1.0
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

TYPES = {
    "00000000": "Development title",
    "00000001": "System title",
    "00010000": "Save data",
    "00010001": "Installed title",
    "00010002": "Preinstalled channel",
    "00010004": "Game channel",
    "00010005": "DLC",
    "00010008": "Hidden title"
}

NAMES = {
    "RABA": "Generic ID",
    "0000": "Generic ID",
}

def readUidSys(uidSysPath):
    uidEntries = {}
    with open(uidSysPath, "rb") as uid:
        while True:
            block = uid.read(12)
            if not block:
                break
            id = f"{"".join(f"{byte:02x}" for byte in block[0:4])}-{"".join(f"{byte:02x}" for byte in block[4:8])}"
            gid = "".join((chr(byte) if 32 <= byte <= 126 else ".") for byte in block[4:8])
            type = TYPES[id[0:8]]
            try:
                name = NAMES[gid]
            except KeyError:
                name = ""
            uidEntries[id] = {"gid": gid, "type": type, "name": name}
    return uidEntries
