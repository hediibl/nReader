# nReader 2.0
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, shutil
from lib.nand import extractNandData
from lib.uid import readUidSys
from lib.export import getSerialNumber, formatShellOutput, formatDocumentOutput
from lib.online import exportJson

def promptYesNo(question: str) -> bool:
    """
    Ask for a Yes / No choice.
    """
    choices = {"Y": True, "N": False}
    answer = input(f"{question} (Y/N) ").upper()
    while answer not in choices:
        answer = input(f"{question} (Y/N) ").upper()
    return choices[answer]

def main() -> None:
    """
    Main entry point for nReader 2.0.
    """
    print("nReader 2.0\n(C) 2025 hediibl\nThis software is licensed under the GNU GPL v3.\n")
    print("This program generates a detailed report of a Wii's history, comparing the content of /sys/uid.sys with the installed titles and tickets.\n")
    
    nandPath = input("Please specify the path to your NAND binary: ").strip()
    keysPath = input("Please specify the path to the associated keys binary: ").strip()
    tempDir = "temp"
    extractNandData(nandPath, keysPath, tempDir)
    
    dbPath = os.path.join("resources", "db.json")
    uidEntries = readUidSys(tempDir, dbPath)
    
    print(f"\n{formatShellOutput(uidEntries)}")
    
    print("\nThis program allows you to save this report as a local HTML document in order to read it later.")
    if promptYesNo("Would you like to save your report?"):
        templatePath = os.path.join("resources", "template.html")
        settingsPath = os.path.join(tempDir, "title", "00000001", "00000002", "data", "setting.txt")
        serialNumber, htmlContent = formatDocumentOutput(templatePath, settingsPath, uidEntries)
        outputFile = f"{serialNumber}.html"
        with open(outputFile, "w", encoding="utf-8") as htmlFile:
            htmlFile.write(htmlContent)
    
    print("\nThis program allows you to share your report online. You can then access this report anytime at https://nreader.eu. It will also help us archive as much information as possible regarding Wii history.")
    if promptYesNo("Would you like to share your data online?"):
        userName = input("Please enter your username: ").strip()
        uploadUrl = "https://nreader.eu/pages/upload.php"
        settingsPath = os.path.join(tempDir, "title", "00000001", "00000002", "data", "setting.txt")
        serialNumber = getSerialNumber(settingsPath)
        success = exportJson(uidEntries, serialNumber, userName, uploadUrl)
        print("Report successfully uploaded!" if success else "Upload failed, check connection, server or data.")
    
    shutil.rmtree(tempDir, ignore_errors=True)
    input("\nPress Enter to exit.")

if __name__ == "__main__":
    main()