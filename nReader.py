# nReader 2.2
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, shutil, argparse
from libs.nand import extractNandData
from libs.uid import readUidSys
from libs.offline import formatShellOutput, formatDocumentOutput
from libs.user import getSerialNumber, chooseUsername, writeUserConfig
from libs.online import checkSerialOnServer, exportJson

def promptYesNo(question):
    """
    Prompt user for yes/no answer.
    :param question: str
    :return: bool
    """
    choices = {"Y": True, "N": False}
    answer = input(f"{question} (Y/N) ").upper()
    while answer not in choices:
        answer = input(f"{question} (Y/N) ").upper()
    return choices[answer]

def processNand(nandPath, keysPath, forcedSerial, saveFlag, shareFlag, username):
    tempDir = "temp"
    extractNandData(nandPath, keysPath, tempDir)
    dbPath = os.path.join("resources", "names.json")
    uidEntries = readUidSys(tempDir, dbPath)
    print(f"\n{formatShellOutput(uidEntries)}")
    settingsPath = os.path.join(tempDir, "title", "00000001", "00000002", "data", "setting.txt")
    serialNumber = getSerialNumber(settingsPath)
    if not forcedSerial:
        forcedSerial = serialNumber
    writeUserConfig(username)
    if saveFlag:
        print("\nSaving report as local HTML...")
        templatePath = os.path.join("resources", "template.html")
        htmlContent = formatDocumentOutput(templatePath, uidEntries, serialNumber, username, currentDate=None)
        outputFile = f"{serialNumber}.html"
        with open(outputFile, "w", encoding="utf-8") as htmlFile:
            htmlFile.write(htmlContent)
        print(f"Report saved as {outputFile}.")
    if shareFlag:
        print("\nChecking serial on server...")
        php_url = "https://nreader.eu/pages/upload.php"
        check_data = checkSerialOnServer(forcedSerial, php_url)
        if check_data.get("exists", False):
            existing_user = check_data.get("username", "")
            existing_date = check_data.get("date", "")
            print(
                f"Serial {forcedSerial} has already been registered by {existing_user} on {existing_date}."
            )
            proceed = promptYesNo(
                "Uploading will update current data and add newest entries. Continue?"
            )
            if not proceed:
                print("Upload cancelled by user.")
                return
        existing_positions = [e.get("position",0) for e in check_data.get("entries", [])]
        response = exportJson(uidEntries, serialNumber, forcedSerial, username, php_url, existing_positions)
        print(f"Report successfully uploaded!" if response.get("success") else f"Upload failed: {response.get('error')}")
    shutil.rmtree(tempDir, ignore_errors=True)

def main():
    print("nReader 2.2\nCopyright (C) 2025 hediibl\nLicensed under the GNU GPL v3")
    parser = argparse.ArgumentParser(description="nReader 2.2", usage="python nReader.py nand.bin [--keysPath keys.bin] [--forceSerial serialNumber] [--localSave] [--shareOnline] [--editUsername]")
    parser.add_argument("nandPath", nargs="?", help="Path to NAND binary")
    parser.add_argument("--keysPath", default=None, help="Path to keys binary (optional)")
    parser.add_argument("--forceSerial", default=None, help="Force serial number (optional)")
    parser.add_argument("--localSave", action="store_true", help="Save report as HTML")
    parser.add_argument("--shareOnline", action="store_true", help="Share report online")
    parser.add_argument("--editUsername", action="store_true", help="Force prompt to change username")
    args = parser.parse_args()
    if not args.nandPath:
        parser.print_usage()
        return
    nandPath = args.nandPath
    keysPath = args.keysPath or None
    forcedSerial = args.forceSerial
    username = chooseUsername(forcePrompt=args.editUsername)
    processNand(nandPath, keysPath, forcedSerial, args.localSave, args.shareOnline, username)

if __name__ == "__main__":
    main()