# nReader v1.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, shutil, requests, re
from wcwidth import wcswidth
from lib.nand import extractNandData
from lib.uid import readUidSys
from lib.checker import checkForTitle, checkForTicket
from lib.export import makeHtmlContent

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def displayColor(status: str) -> str:
    """Return a colored string for terminal output."""
    if status == "No":
        return "\033[31mNo\033[0m"
    elif status == "N/A":
        return "\033[90mN/A\033[0m"
    else:
        return f"\033[32m{status}\033[0m"

def padColumn(s: str, width: int) -> str:
    """
    Pad a string to a given display width, ignoring ANSI codes.
    Adds extra spacing for readability.
    """
    s = str(s)
    visible = ANSI_ESCAPE.sub('', s)
    pad = max(0, width - wcswidth(visible))
    return s + " " * (pad + 8)

def promptYesNo(message: str) -> bool:
    """Prompt the user for Y/N input and return True/False."""
    choice = input(message + " (Y/N): ").strip().upper()
    while choice not in ("Y", "N"):
        choice = input("Please enter Y or N: ").strip().upper()
    return choice == "Y"

def main():
    print("nReader v1.2\n(C) 2025 hediibl\nThis software is licensed under the GNU GPL v3.\n")
    print("This program generates a detailed report of a Wii's history, comparing the content of /sys/uid.sys with the installed titles and tickets.\n")

    # Input paths
    nandPath = input("Please specify the path to your NAND binary: ").strip()
    keysPath = input("Please specify the path to the associated keys binary: ").strip()

    # Extract NAND
    extractNandData(nandPath, keysPath)

    # Read uid.sys
    uidPath = os.path.join("temp", "sys", "uid.sys")
    dbPath = os.path.join("resources", "db.json")
    uidEntries = readUidSys(uidPath, dbPath)

    # Check titles and tickets
    for entry in uidEntries:
        uidEntries[entry]["title"] = checkForTitle(entry)
        uidEntries[entry]["ticket"] = checkForTicket(entry)

    # Prepare columns
    headers = ["ID", "Game ID", "Type", "Name", "Title ?", "Ticket ?"]
    columns = [[] for _ in headers]

    for entry, data in uidEntries.items():
        columns[0].append(str(entry))
        columns[1].append(str(data["gid"]))
        columns[2].append(str(data["type"]))
        columns[3].append(str(data["name"]))
        columns[4].append(displayColor(data["title"]))
        columns[5].append(displayColor(data["ticket"]))

    # Compute max widths
    widths = [max([wcswidth(ANSI_ESCAPE.sub('', h))] + [wcswidth(ANSI_ESCAPE.sub('', c)) for c in col]) for h, col in zip(headers, columns)]

    # Print header
    headerLine = "".join(padColumn(h, w) for h, w in zip(headers, widths))
    print(f"\n{headerLine}")

    # Print entries
    for i in range(len(uidEntries)):
        line = "".join(padColumn(columns[j][i], widths[j]) for j in range(len(headers)))
        print(line)

    # Save HTML report
    if promptYesNo("\nWould you like to save your report?"):
        print("\nYou can store your report as an HTML document, either online or locally.")
        print("Online reports are publicly available and used in a collaborative database.")
        doShare = promptYesNo("\nWould you like to store your report online?")
        userName = input("Please enter your username: ").strip()

        serialNumber, htmlContent = makeHtmlContent(
            os.path.join("resources", "template.html"),
            os.path.join("temp", "title", "00000001", "00000002", "data", "setting.txt"),
            uidEntries,
            userName,
            doShare
        )

        localPath = f"{serialNumber}.html"
        with open(localPath, "w", encoding="utf-8") as file:
            file.write(htmlContent)

        if doShare:
            with open(localPath, "rb") as file:
                response = requests.post("https://nreader.eu/uploads.php", files={"file": file})
            try:
                result = response.json()
                success = result.get("success", False)
            except ValueError:
                success = False

            if response.status_code == 200 and success:
                print(f"\nYour report has been uploaded successfully: https://nreader.eu/nands/{serialNumber}.html")
                os.remove(localPath)
            else:
                print("\nUpload failed. Your report has been saved locally.")

    # Cleanup
    shutil.rmtree("temp", ignore_errors=True)
    input("\nPress Enter to exit.")

if __name__ == "__main__":
    main()