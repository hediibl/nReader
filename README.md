# nReader 2.5

Author: hediibl

---

## Description

**nReader** is a tool for analyzing the history of a Nintendo Wii NAND.
It generates a detailed report by cross-checking `/sys/uid.sys` and the current `/title` and `/ticket` directories, allowing users to understand what has been installed, removed, or left behind over time.
The report is then uploaded to a public database to be processed later.

The report includes:

* ID;
* Game ID;
* Type;
* Name;
* Current version;
* Ticket presence.

---

## Distributions

nReader is available in two independent versions:

### 1. Console version

* **Language:** C/C++
* **Files:** `boot.elf` / `boot.dol`
* **License:** MIT License
* **Functionality:** Automatically uploads raw console data to the server.

### 2. Desktop version

* **Language:** Python 3
* **Files:** `nReader.py` (`nReader.exe` for Windows only)
* **License:** GNU General Public License v3.0 (GPL-3.0)
* **Functionality:** Offers to display the report, save it locally and/or upload it to the server. Allows forcing a serial number that is different from the NAND one, as well as providing a description. Intended for advanced users and for specific NANDs.

---

## Requirements

### Wii version

Running the Wii version requires:

* A Nintendo Wii, Wii Family Edition, Wii Mini;
* Some exploit/the Homebrew Channel to run the `.elf` / `.dol` executable;
* An Internet connection to your Wii.

### Python version

The following packages are required:

* `pycryptodome`
* `wcwidth`
* `requests`

Install them with:

```
pip install pycryptodome wcwidth requests
```

---

## Usage

### Wii version

Launch the `.elf` / `.dol` executable through any exploit/the Homebrew Channel.

### Python version

```
python nReader.py nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

### Windows version

```
nReader.exe nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

---

## Building

### Wii version

devkitPPC and libogc are required to compile the `.elf` / `.dol` executables.

To compile, open a shell in the root directory and run:

```
make
```

### Windows version

The following packages are required to compile the `.exe` executable :
* `pyinstaller`
* `pycryptodome`
* `wcwidth`
* `requests`

Install them with:

```
pip install pyinstaller pycryptodome wcwidth requests
```

To compile, open a shell in the root directory and run:

```
pyinstaller nReader.spec
```

---

## License

* **Desktop version:** GNU General Public License v3.0 (GPL-3.0). 
  See: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html). 
  Some code is derived from *Wii NAND Extractor* by Ben Wilson (2009) and remains covered under GPL‑3.0.

* **Console version:** MIT License. 
  See: [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT). 
  Some code is derived from *tikdumper* by Aep (2025) and remains covered under MIT License.

---

## Credits

* Original code for Wii NAND handling by Ben Wilson (Wii NAND Extractor, 2009), many thanks!
* Code for filesystem permissions borrowed from Aep's tikdumper, thanks a lot!
* Thanks to Hallowizer for hallowtools, which inspired this project, and to RedBees for the idea of making it a public project.