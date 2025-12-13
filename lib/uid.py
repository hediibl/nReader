# nReader v1.1
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

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
# Editable name databases
# =========================

DEV_NAMES = {
    "87654321": "sdboot2",
}

SYS_SPECIAL_NAMES = {
    "00000000": "ES_Identify Superuser",
    "00000001": "boot1 glitch",
    "00000002": "System Menu",
    "00000100": "BC",
    "00000101": "MIOS",
}

SAVE_NAMES = {
    "RABA": "Generic ID",
    "0000": "Generic ID",
}

INSTALLED_TITLES_NAMES = {

}

PREINSTALLED_CHANNELS_NAMES = {

}

GAME_CHANNELS_NAMES = {

}

DLC_NAMES = {

}

HIDDEN_CHANNELS_NAMES = {

}

# =========================
# Name resolution logic
# =========================

def resolveSystemTitle(minor: str) -> str:
    """
    Resolve IOS names.
    """
    if minor in SYS_SPECIAL_NAMES:
        return SYS_SPECIAL_NAMES[minor]

    try:
        iosNumber = int(minor, 16)
    except ValueError:
        return ""

    if 1 <= iosNumber <= 255:
        return f"IOS{iosNumber}"

    return ""


NAME_RESOLVERS = {
    "Development title": lambda minor: DEV_NAMES.get(minor, ""),
    "System title": lambda minor: resolveSystemTitle(minor),
    "Save data": lambda minor: SAVE_NAMES.get(minor, ""),
    "Installed title": lambda minor: INSTALLED_TITLES_NAMES.get(minor, ""),
    "Preinstalled channel": lambda minor: PREINSTALLED_CHANNELS_NAMES.get(minor, ""),
    "Game channel": lambda minor: GAME_CHANNELS_NAMES.get(minor, ""),
    "DLC": lambda minor: DLC_NAMES.get(minor, ""),
    "Hidden title": lambda minor: HIDDEN_CHANNELS_NAMES.get(minor, ""),
}


def resolveTitleName(titleType: str, minor: str) -> str:
    """
    Resolve a title name from its type and minor ID.
    """
    resolver = NAME_RESOLVERS.get(titleType)
    return resolver(minor) if resolver else ""


# =========================
# UID.sys parsing
# =========================

def readUidSys(uidSysPath: str) -> dict:
    uidEntries = {}

    with open(uidSysPath, "rb") as uidFile:
        while True:
            block = uidFile.read(12)
            if not block:
                break

            major = "".join(f"{b:02x}" for b in block[0:4])
            minor = "".join(f"{b:02x}" for b in block[4:8])
            titleId = f"{major}-{minor}"

            gid = "".join(chr(b) if 32 <= b <= 126 else "." for b in block[4:8])

            titleType = TYPES.get(major, "Unknown")
            titleName = resolveTitleName(titleType, minor)

            uidEntries[titleId] = {
                "gid": gid,
                "type": titleType,
                "name": titleName,
            }

    return uidEntries