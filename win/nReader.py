# nReader 2.5
# Copyright (C) 2026 hediibl
# Licensed under the GNU GPL v3

import os, shutil, argparse, sys
from libs.nand import extractNandData
from libs.uid import readUidSys
from libs.offline import formatShellOutput, formatDocumentOutput
from libs.user import getSerialNumber, chooseUsername, writeUserConfig
from libs.online import checkSerialOnServer, exportJson

def resourcePath(relativePath):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        basePath = sys._MEIPASS
    except AttributeError:
        basePath = os.path.abspath(".")
    return os.path.join(basePath, relativePath)

def promptYesNo(question):
    """Prompt user for yes/no answer."""
    choices = {"Y": True, "N": False}
    answer = input(f"{question} (Y/N) ").upper()
    while answer not in choices:
        answer = input(f"{question} (Y/N) ").upper()
    return choices[answer]

def processNand(nandPath, useKeys, saveFlag=None, shareFlag=None, username="", forcedSerial=None, description=""):
    """
    Process NAND: extract, read UID, save report, upload if requested.
    """
    tempDir = "temp"
    extractNandData(nandPath, useKeys, tempDir)
    dbPath = resourcePath(os.path.join("resources", "names.json"))
    uidEntries = readUidSys(tempDir, dbPath)
    print(f"\n{formatShellOutput(uidEntries)}")

    if saveFlag is None:
        saveFlag = promptYesNo("Do you want to save a local report?")
    if shareFlag is None:
        shareFlag = promptYesNo("Do you want to share the report online?")

    settingsPath = os.path.join(tempDir, "title", "00000001", "00000002", "data", "setting.txt")
    serialNumber = getSerialNumber(settingsPath)
    writeUserConfig(username)

    if saveFlag:
        print("\nSaving report as local HTML...")
        templatePath = resourcePath(os.path.join("resources", "template.html"))
        htmlContent = formatDocumentOutput(
            templatePath, uidEntries, serialNumber, username,
            description=description, forcedSerial=forcedSerial
        )
        outputFile = f"{forcedSerial or serialNumber}.html"
        with open(outputFile, "w", encoding="utf-8") as htmlFile:
            htmlFile.write(htmlContent)
        print(f"Report saved as {outputFile}.")

    if shareFlag:
        print("\nChecking serial on server...")
        phpUrl = "https://nreader.eu/pages/upload.php"
        checkData = checkSerialOnServer(forcedSerial or serialNumber, phpUrl)

        if checkData.get("exists", False):
            existingUser = checkData.get("username", "")
            existingDate = checkData.get("date", "")
            print(f"Serial {forcedSerial or serialNumber} has already been registered by {existingUser} on {existingDate}.")
            proceed = promptYesNo("Uploading will update current data and add newest entries. Continue?")
            if not proceed:
                print("Upload cancelled by user.")
                shutil.rmtree(tempDir, ignore_errors=True)
                return

        response = exportJson(
            uidEntries, serial=forcedSerial or serialNumber, serialNand=serialNumber,
            username=username, phpUrl=phpUrl, description=description
        )

        if response.get("success"):
            print("Report successfully uploaded!")
        else:
            errorCode = response.get("errorCode", response.get("error", "Unknown error"))
            if errorCode == "HISTORY_MISMATCH":
                print("Upload refused: existing server history does not match this NAND.")
            elif errorCode == "BAD_SERIAL_NAND":
                print("Upload refused: NAND serial mismatch.")
            elif errorCode == "NETWORK_ERROR":
                print("Upload failed: network error while contacting server.")
            elif errorCode == "HTTP_ERROR":
                print("Upload failed: server returned an HTTP error.")
            else:
                print(f"Upload failed: {errorCode}")

    shutil.rmtree(tempDir, ignore_errors=True)

def main():
    print("nReader 2.5\nCopyright (C) 2026 hediibl\nLicensed under the GNU GPL v3")
    parser = argparse.ArgumentParser(
        usage="nReader.exe nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription 'descriptionText']"
    )
    parser.add_argument("nandPath", nargs="?", help="Path to NAND binary")
    parser.add_argument("--useKeys", default=None, help="Path to keys binary", metavar="keysPath")
    parser.add_argument("--localSave", action="store_true", help="Save report as HTML")
    parser.add_argument("--shareOnline", action="store_true", help="Share report online")
    parser.add_argument("--forceSerial", default=None, help="Force serial number", metavar="serialNumber")
    parser.add_argument("--addDescription", default="", help="Description to include with the report", metavar="'descriptionText'")
    args = parser.parse_args()

    username = chooseUsername()
    if not args.nandPath:
        print(f"\nWelcome {username}!")
        print("It looks like you've ran this program without any argument. Here's a quick reminder:")
        parser.print_help()
        return

    if len(sys.argv) == 2:
        saveFlag = None
        shareFlag = None
    else:
        saveFlag = args.localSave or False
        shareFlag = args.shareOnline or False

    processNand(
        nandPath=args.nandPath,
        useKeys=args.useKeys or None,
        saveFlag=saveFlag,
        shareFlag=shareFlag,
        username=username,
        forcedSerial=args.forceSerial,
        description=args.addDescription
    )

if __name__ == "__main__":
    main()