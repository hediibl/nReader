# nReader v1.1
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, shutil, requests
from lib.nand import extractNandData
from lib.uid import readUidSys
from lib.checker import checkForTitle, checkForTicket
from lib.export import makeHtmlContent

def displayColor(status: str) -> str:
    """Return a colored string for terminal output."""
    if status == "No":
        return "\033[31mNo\033[0m"
    elif status == "N/A":
        return "\033[90mN/A\033[0m"
    else:
        return f"\033[32m{status}\033[0m"

def promptYesNo(message: str) -> bool:
    """Prompt the user for Y/N input and return True/False."""
    choice = input(message + " (Y/N): ").strip().upper()
    while choice not in ("Y", "N"):
        choice = input("Please enter Y or N: ").strip().upper()
    return choice == "Y"

def main():
    print("nReader v1.1\n(C) 2025 hediibl\nThis software is licensed under the GNU GPL v3.\n")
    print("This program generates a detailed report of a Wii's history, comparing the content of /sys/uid.sys with the installed titles and tickets.\n")

    nandPath = input("Please specify the path to your NAND binary: ").strip()
    keysPath = input("Please specify the path to the associated keys binary: ").strip()
    extractNandData(nandPath, keysPath)

    uidEntries = readUidSys(os.path.join("temp", "sys", "uid.sys"))

    for entry in uidEntries:
        uidEntries[entry]["title"] = checkForTitle(entry)
        uidEntries[entry]["ticket"] = checkForTicket(entry)

    print(f"\n{'ID':<20}{'Game ID':<10}{'Type':<25}{'Name':<75}{'Title ?':<16}{'Ticket ?':<20}")
    
    for entry, data in uidEntries.items():
        print(
            f"{str(entry):<20}{data['gid']:<10}{data['type']:<25}{data['name']:<75}"
            f"{displayColor(data['title']):<25}{displayColor(data['ticket']):<20}"
        )

    if promptYesNo("\nWould you like to save your report?"):
        print("\nYou can store your report as an HTML document, either online or locally.")
        print("Online reports are publicly available and used in a collaborative database.")
        doShare = promptYesNo("\nWould you like to store your report online?")
        userName = input("Please enter your username: ").strip()

        serialNumber, htmlContent = makeHtmlContent(
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

    shutil.rmtree("temp", ignore_errors=True)
    input("\nPress Enter to exit.")

if __name__ == "__main__":
    main()