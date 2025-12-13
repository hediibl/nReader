# nReader v1.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, html
from datetime import datetime

def rotateLeft32(x: int) -> int:
    """Rotate a 32-bit integer left by 1 bit."""
    return ((x << 1) & 0xFFFFFFFF) | (x >> 31)

def xorEncrypt(buf: bytes, isEnc: bool) -> bytes:
    """
    Encrypt or decrypt buffer using a simple XOR-based scheme.
    Only first 256 bytes are affected when decrypting.
    """
    key = 0x73B5DBFA
    data = bytearray(buf)
    length = len(data) if isEnc else min(256, len(data))
    for i in range(length):
        data[i] ^= key & 0xFF
        key = rotateLeft32(key)
    return bytes(data)

def getSerialNumber(settingsPath: str) -> str:
    """Extract the serial number from a settings file."""
    if not os.path.isfile(settingsPath):
        raise FileNotFoundError(f"Settings file not found: {settingsPath}")

    with open(settingsPath, "rb") as f:
        encrypted = f.read()

    decrypted = xorEncrypt(encrypted, isEnc=True)
    parameters = decrypted.decode("ascii", errors="ignore").split("\r\n")

    if len(parameters) < 6:
        parameters = decrypted.decode("ascii", errors="ignore").split("\n")
        if len(parameters) < 6:
            raise ValueError("Settings file corrupted or invalid format")

    try:
        part1 = parameters[4].split("=")[1]
        part2 = parameters[5].split("=")[1]
    except IndexError:
        raise ValueError("Serial number fields missing in settings")

    return f"{part1}{part2}"

def insertColor(status: str) -> str:
    """Return HTML span with color depending on status."""
    statusMap = {"No": "red", "N/A": "gray"}
    color = statusMap.get(status, "green")
    return f"<span class='{color}'>{html.escape(status)}</span>"

def makeHtmlContent(templateHtmlPath: str, settingsPath: str,
                    uidEntries: dict, userName: str, doShare: bool):
    """
    Generate an HTML report from template and UID entries.

    Args:
        templateHtmlPath: path to HTML template
        settingsPath: path to settings file (for serial number)
        uidEntries: dictionary of UID entries
        userName: string to display as report creator
        doShare: if True, <style> block is removed

    Returns:
        tuple(serialNumber, htmlContent)
    """
    if not os.path.isfile(templateHtmlPath):
        raise FileNotFoundError(f"HTML template not found: {templateHtmlPath}")

    with open(templateHtmlPath, "r", encoding="utf-8") as f:
        htmlTemplate = f.read()

    serialNumber = getSerialNumber(settingsPath)

    # Build table rows
    rows = []
    for uid, entry in uidEntries.items():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(uid))}</td>"
            f"<td>{html.escape(str(entry.get('gid', '')))}</td>"
            f"<td>{html.escape(str(entry.get('type', '')))}</td>"
            f"<td>{html.escape(str(entry.get('name', '')))}</td>"
            f"<td>{insertColor(entry.get('title', 'N/A'))}</td>"
            f"<td>{insertColor(entry.get('ticket', 'N/A'))}</td>"
            "</tr>"
        )

    # Replace template placeholders
    htmlContent = htmlTemplate.replace("TBD_SERIAL", html.escape(serialNumber))
    htmlContent = htmlContent.replace("TBD_USER", html.escape(userName))
    htmlContent = htmlContent.replace("TBD_DATE", datetime.now().strftime("%B %d, %Y %H:%M:%S"))
    htmlContent = htmlContent.replace("TBD_ROWS", "\n".join(rows))

    # Remove <style> block if report is shared online
    if doShare:
        htmlContent = htmlContent.replace("<style></style>", "")

    return serialNumber, htmlContent