# nReader v1.0

Author: hediibl
License: GNU General Public License v3.0 (GPL-3.0)

---

## Description

nReader is a Python tool for analyzing a Wii NAND's history. It generates a detailed report by comparing the /sys/uid.sys file with the currently installed titles and tickets on the console.

The program provides information such as:

* Title ID and Game ID
* Title type (System title, Save data, Installed title, etc.)
* Human-readable title name
* Installed status and version
* Ticket availability

This allows users to quickly audit the Wii's installed software and verify ticket presence for each title.

---

## Usage

1. Clone this repository:

git clone <repository-url>

2. Run the program:

python nreader.py

3. Enter the path to your NAND binary and the keys binary when prompted.

4. The program will extract the NAND in a temporary folder, read /sys/uid.sys, and print a formatted report in the terminal.

---

## License

This project is licensed under the GNU General Public License v3.0 ([https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)).

Some code is derived from Wii NAND Extractor by Ben Wilson (2009) and is also covered under the GPL v3.

---

## Credits

- Original code for Wii NAND handling by Ben Wilson (Wii NAND Extractor, 2009), many thanks!
- Thanks to Hallowizer for hallowtools, which inspired this project, and to RedBees for the idea of making it a public project.