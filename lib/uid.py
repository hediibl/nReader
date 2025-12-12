# nReader v1.1
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

def readUidSys(uidSysPath: str) -> dict:
    uidEntries = {}
    with open(uidSysPath, "rb") as uidFile:
        while True:
            block = uidFile.read(12)
            if not block:
                break
            uidHex = f'{"".join(f"{b:02x}" for b in block[0:4])}-{"".join(f"{b:02x}" for b in block[4:8])}'
            gid = "".join((chr(b) if 32 <= b <= 126 else ".") for b in block[4:8])
            typeName = TYPES.get(uidHex[:8], "Unknown")
            name = NAMES.get(gid, "")
            uidEntries[uidHex] = {"gid": gid, "type": typeName, "name": name}
    return uidEntries