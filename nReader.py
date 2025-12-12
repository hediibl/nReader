import os, shutil
from lib.nand import extractNandData
from lib.uid import readUidSys
from lib.checker import checkForTitle, checkForTicket

print("nReader v1.0\nby hediibl")
print("This program generates a detailed report of a Wii's history, comparing the content of /sys/uid.sys with the installed titles and tickets.\n")

nandPath = input("Please specify the path to your nand binary: ")
keysPath = input("Please specify the path to the associated keys binary: ")
extractNandData(nandPath, keysPath)

uidEntries = readUidSys(os.path.join("temp", "sys", "uid.sys"))

for entry in uidEntries:
    uidEntries[entry]["title"] = checkForTitle(entry)
    uidEntries[entry]["ticket"] = checkForTicket(entry)

shutil.rmtree("temp")
print(f"\n{"ID":<20}{"Game ID":<10}{"Type":<25}{"Name":<75}{"Title ?":<16}{"Ticket ?":<20}")
for entry in uidEntries:
    print(f"{str(entry):<20}{uidEntries[entry]["gid"]:<10}{uidEntries[entry]["type"]:<25}{uidEntries[entry]["name"]:<75}{uidEntries[entry]["title"]:<25}{uidEntries[entry]["ticket"]:<20}")

input("Press Enter to exit.")