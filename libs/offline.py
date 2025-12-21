# nReader 2.3
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, html, re
from datetime import datetime, timezone
from wcwidth import wcswidth

ansiEscape = re.compile(r'\x1b\[[0-9;]*m')

def isAnsiCompatible():
    try:
        return os.name != "nt" or "ANSICON" in os.environ or "WT_SESSION" in os.environ
    except Exception:
        return False

def displayColor(status, useColor=None):
    """
    Return colored string for terminal output depending on status.

    :param status: str, status string ("No", "N/A", or other)
    :param useColor: bool or None, whether to apply ANSI colors (auto-detected if None)
    :return: str, colored string if supported, plain string otherwise
    """
    if useColor is None:
        useColor = isAnsiCompatible()
    if not useColor:
        return status
    if status == "No":
        return "\033[31mNo\033[0m"
    elif status == "N/A":
        return "\033[90mN/A\033[0m"
    return f"\033[32m{status}\033[0m"

def padColumn(value, width):
    """
    Pad a string to a specified width ignoring ANSI codes.

    :param value: str, text to pad
    :param width: int, width of the column
    :return: str, padded string
    """
    value = str(value)
    visible = ansiEscape.sub('', value)
    pad = max(0, width - wcswidth(visible))
    return value + " " * (pad + 4)

def formatShellOutput(uidEntries, useColor=None):
    """
    Return a formatted table of UID entries for terminal display.

    :param uidEntries: dict, UID entries with resolved info
    :param useColor: bool or None, whether to apply ANSI colors (auto-detected if None)
    :return: str, formatted table string
    """
    if not uidEntries:
        return "No entries to display."
    headers = ["ID", "Game ID", "Type", "Name", "Title ?", "Ticket ?"]
    columns = [[] for _ in headers]
    for uid, entry in uidEntries.items():
        columns[0].append(str(uid))
        columns[1].append(str(entry.get("gid","")))
        columns[2].append(str(entry.get("type","")))
        columns[3].append(str(entry.get("name","")))
        columns[4].append(displayColor(entry.get("title","N/A"), useColor))
        columns[5].append(displayColor(entry.get("ticket","N/A"), useColor))
    widths = [max([wcswidth(ansiEscape.sub('', h))] + [wcswidth(ansiEscape.sub('', c)) for c in col]) for h, col in zip(headers, columns)]
    lines = ["".join(padColumn(h, w) for h, w in zip(headers, widths))]
    for i in range(len(uidEntries)):
        line = "".join(padColumn(columns[j][i], widths[j]) for j in range(len(headers)))
        lines.append(line)
    return "\n".join(lines)

def insertColor(status):
    """
    Return HTML span with color class depending on status.

    :param status: str, status string ("No", "N/A", or other)
    :return: str, HTML span string with color class
    """
    statusMap = {"No":"red", "N/A":"gray"}
    color = statusMap.get(status,"green")
    return f"<span class='{color}'>{html.escape(status)}</span>"

def formatDocumentOutput(templatePath, uidEntries, serialNumber, username, description=None, forcedSerial=None, currentDate=None):
    """
    Generate HTML content from template and UID entries.
    Handles warnings and uploader description.

    :param templatePath: str, path to HTML template
    :param uidEntries: dict, UID entries with resolved info
    :param serialNumber: str, serial detected in NAND
    :param username: str, user who generated the document
    :param description: str or None, optional uploader description
    :param forcedSerial: str or None, user-specified serial (for warning)
    :param currentDate: datetime, optional date to use instead of now
    :return: str, generated HTML content
    """
    if not os.path.isfile(templatePath):
        raise FileNotFoundError(f"HTML template not found: {templatePath}")
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
    displaySerial = forcedSerial or serialNumber
    htmlContent = htmlTemplate.replace("TBD_SERIAL", html.escape(displaySerial))
    htmlContent = htmlContent.replace("TBD_USER", html.escape(username))
    utcNow = currentDate or datetime.now(timezone.utc)
    htmlContent = htmlContent.replace("TBD_DATE", utcNow.strftime("%B %d, %Y %H:%M:%S"))
    htmlContent = htmlContent.replace("TBD_ROWS", "\n".join(rows))
    if forcedSerial and forcedSerial != serialNumber:
        warningHtml = f"<p class='orange'>Warning: User-specified serial ({html.escape(forcedSerial)}) does not match the NAND serial ({html.escape(serialNumber)}).</p>"
    else:
        warningHtml = ""
    htmlContent = htmlContent.replace("TBD_WARNING_SERIAL", warningHtml)
    if description:
        descriptionHtml = f"<p class='yellow description'><b>Notes from the uploader:</b> {html.escape(description)}</p>"
    else:
        descriptionHtml = ""
    htmlContent = htmlContent.replace("TBD_DESCRIPTION", descriptionHtml)
    return htmlContent