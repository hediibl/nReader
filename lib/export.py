# nReader 2.0
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, html, re
from datetime import datetime
from wcwidth import wcswidth

ansiEscape = re.compile(r'\x1b\[[0-9;]*m')

def displayColor(status: str) -> str:
    """
    Return colored string for terminal output.
    """
    if status == "No":
        return "\033[31mNo\033[0m"
    elif status == "N/A":
        return "\033[90mN/A\033[0m"
    else:
        return f"\033[32m{status}\033[0m"

def padColumn(value: str, width: int) -> str:
    """
    Pad string to width ignoring ANSI codes, adding extra spacing.
    """
    value = str(value)
    visible = ansiEscape.sub('', value)
    pad = max(0, width - wcswidth(visible))
    return value + " " * (pad + 4)

def formatShellOutput(uidEntries: dict) -> str:
    """
    Return formatted table of UID entries as string for terminal display.
    """
    if not uidEntries:
        return "No entries to display."
    headers = ["ID", "Game ID", "Type", "Name", "Title ?", "Ticket ?"]
    columns = [[] for _ in headers]
    for uid, entry in uidEntries.items():
        columns[0].append(str(uid))
        columns[1].append(str(entry.get("gid", "")))
        columns[2].append(str(entry.get("type", "")))
        columns[3].append(str(entry.get("name", "")))
        columns[4].append(displayColor(entry.get("title", "N/A")))
        columns[5].append(displayColor(entry.get("ticket", "N/A")))
    widths = [max([wcswidth(ansiEscape.sub('', h))] + [wcswidth(ansiEscape.sub('', c)) for c in col]) for h, col in zip(headers, columns)]
    lines = ["".join(padColumn(h, w) for h, w in zip(headers, widths))]
    for i in range(len(uidEntries)):
        line = "".join(padColumn(columns[j][i], widths[j]) for j in range(len(headers)))
        lines.append(line)
    return "\n".join(lines)

def insertColor(status: str) -> str:
    """
    Return HTML span with color class depending on status.
    """
    statusMap = {"No": "red", "N/A": "gray"}
    color = statusMap.get(status, "green")
    return f"<span class='{color}'>{html.escape(status)}</span>"

def rotateLeft32(value: int) -> int:
    """
    Rotate a 32-bit integer left by 1 bit.
    """
    return ((value << 1) & 0xFFFFFFFF) | (value >> 31)

def xorEncrypt(buffer: bytes, isEnc: bool) -> bytes:
    """
    Encrypt or decrypt buffer using a simple XOR-based scheme.
    Only first 256 bytes are affected when decrypting.
    """
    key = 0x73B5DBFA
    dataBuffer = bytearray(buffer)
    length = len(dataBuffer) if isEnc else min(256, len(dataBuffer))
    for i in range(length):
        dataBuffer[i] ^= key & 0xFF
        key = rotateLeft32(key)
    return bytes(dataBuffer)

def getSerialNumber(settingsPath: str) -> str:
    """
    Extract the serial number from a Wii settings file.
    """
    if not os.path.isfile(settingsPath):
        raise FileNotFoundError(f"Settings file not found: {settingsPath}")
    with open(settingsPath, "rb") as file:
        encryptedData = file.read()
    decryptedData = xorEncrypt(encryptedData, isEnc=True)
    decodedData = decryptedData.decode("ascii", errors="ignore")
    parameters = re.split(r'[\r\n]+', decodedData)
    parameters = [p for p in parameters if p]
    if len(parameters) < 6:
        raise ValueError("Settings file corrupted or invalid format")
    try:
        part1 = parameters[4].split("=")[1]
        part2 = parameters[5].split("=")[1]
    except IndexError:
        raise ValueError("Serial number fields missing in settings")
    return f"{part1}{part2}"

def formatDocumentOutput(templatePath: str, settingsPath: str, uidEntries: dict):
    """
    Return HTML content string generated from template and UID entries.
    """
    if not os.path.isfile(templatePath):
        raise FileNotFoundError(f"HTML template not found: {templatePath}")
    if not os.path.isfile(settingsPath):
        raise FileNotFoundError(f"Settings file not found: {settingsPath}")
    serialNumber = getSerialNumber(settingsPath)
    rows = []
    for uid, entry in uidEntries.items():
        rows.append(
            "\t\t\t\t<tr>"
            f"<td>{html.escape(str(uid))}</td>"
            f"<td>{html.escape(str(entry.get('gid','')))}</td>"
            f"<td>{html.escape(str(entry.get('type','')))}</td>"
            f"<td>{html.escape(str(entry.get('name','')))}</td>"
            f"<td>{insertColor(entry.get('title','N/A'))}</td>"
            f"<td>{insertColor(entry.get('ticket','N/A'))}</td>"
            "</tr>"
        )
    with open(templatePath, "r", encoding="utf-8") as file:
        htmlTemplate = file.read()
    htmlContent = htmlTemplate.replace("TBD_SERIAL", html.escape(serialNumber))
    htmlContent = htmlContent.replace("TBD_DATE", datetime.now().strftime("%B %d, %Y %H:%M:%S"))
    htmlContent = htmlContent.replace("TBD_ROWS", "\n".join(rows))
    return serialNumber, htmlContent

