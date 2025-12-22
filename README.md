# nReader 2.4

Author: hediibl

License: GNU General Public License v3.0 (GPL-3.0)

---

## Description

**nReader** is a tool for analyzing the history of a Nintendo Wii NAND dump.
It generates a detailed report by comparing the contents of `/sys/uid.sys` with the titles and tickets actually present on the NAND, allowing users to understand what has been installed, removed, or left behind over time.

The report can be:

* **Displayed in the terminal** (human‑readable table)
* **Saved locally** as an HTML file
* **Uploaded online** to a public database (optional)

The analysis includes:

* Title ID and Game ID
* Title type (System title, Save data, Installed title, etc.)
* Human‑readable title name
* Installed status and version
* Ticket presence

This makes it easy to audit a Wii NAND, detect inconsistencies, and preserve historical data.

---

## Distribution formats

nReader is available in two forms:

* **Python script** (`nReader.py`)
* **Standalone executable** (`nReader.exe`) (Windows only)

The executable version does **not** require Python to be installed.

---

## Requirements

If you use the Python script, the following packages are required:

* `pycryptodome`
* `wcwidth`
* `requests`

Install them with:

```
pip install pycryptodome wcwidth requests
```

The `.exe` version already bundles all dependencies.

---

## Usage

### Python version

```
python nReader.py nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

### Executable version (Windows)

```
nReader.exe nandPath [--useKeys keysPath] [--localSave] [--shareOnline] [--forceSerial serialNumber] [--addDescription "description"]
```

### Arguments

* `nandPath`
  Path to the Wii NAND binary (`nand.bin`).

* `--useKeys keysPath` (optional)
  Path to a keys file. Required if the NAND does not embed AES keys.

* `--localSave`
  Save the report as a local HTML file.

* `--shareOnline`
  Upload the report to the public nReader database.

* `--forceSerial serialNumber` (optional)
  Override the detected serial number.

* `--addDescription "description"` (optional)
  Add a textual description to the saved or uploaded report.

---

## License

This project is licensed under the GNU General Public License v3.0.

See: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)

Some code is derived from *Wii NAND Extractor* by Ben Wilson (2009) and remains covered under GPL‑3.0.

---

## Credits

* Original code for Wii NAND handling by Ben Wilson (Wii NAND Extractor, 2009), many thanks!
* Thanks to Hallowizer for hallowtools, which inspired this project, and to RedBees for the idea of making it a public project.