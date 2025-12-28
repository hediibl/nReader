# nReader 2.4

Author: hediibl

---

## Description

**nReader** is a tool for analyzing the history of a Nintendo Wii NAND.
It generates a detailed report by comparing the entries of `/sys/uid.sys` with the current `/title` and `/ticket` directories, allowing users to understand what has been installed, removed, or left behind over time.

The report can be:

* **Displayed** in the shell as a human-readable table;
* **Saved** locally as an HTML document;
* **Uploaded** online to a public database.

The analysis includes:

* ID;
* Game ID;
* Type of title;
* Title name;
* Installed status and version;
* Ticket presence.

This makes it easy to audit a Wii NAND, detect inconsistencies, and preserve historical data.

---

## Distribution formats

nReader is available in two independent versions:

### 1. Desktop version

* **Language:** Python 3
* **Files:** `nReader.py`, optional `.exe` for Windows
* **License:** GNU General Public License v3.0 (GPL-3.0)

The executable version does **not** require Python or any dependencies to be installed.

### 2. Console version

* **Language:** C
* **Purpose:** Run directly on a Wii via exploits
* **License:** MIT License
* **Functionality:** Generates the same NAND history report, including all titles ever installed—even those no longer present—and can save it locally or share it online.

---

## Requirements

### Desktop version

If you're using the Python version, the following packages are required:

* `pycryptodome`
* `wcwidth`
* `requests`

Install them with:

```
pip install pycryptodome wcwidth requests
```

### Wii version

* A Nintendo Wii;
* Some exploit/the Homebrew Channel to run the `.elf/.dol` executable;
* devkitPPC and libogc (for compiling);
* An SD card for saving local reports;
* An Internet connection to your Wii for uploading reports.

---

## Usage

### Python version

```
python nReader.py nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

### Windows version

```
nReader.exe nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

### Wii version

Launch the `.elf/.dol` executable through any exploit/the Homebrew Channel and follow the on-screen instructions.

---

## License

* **Desktop version:** GNU General Public License v3.0 (GPL-3.0)
  See: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)
  Some code is derived from *Wii NAND Extractor* by Ben Wilson (2009) and remains covered under GPL‑3.0.

* **Console version:** MIT License
  See: [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)
  Some code is derived from *tikdumper* by Aep (2025) and remains covered under MIT License.

---

## Credits

* Original code for Wii NAND handling by Ben Wilson (Wii NAND Extractor, 2009), many thanks!
* Code for filesystem permissions borrowed from Aep's tikdumper, thanks a lot!
* Thanks to Hallowizer for hallowtools, which inspired this project, and to RedBees for the idea of making it a public project.

