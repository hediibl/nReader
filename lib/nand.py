# nReader 2.0
# Copyright (C) 2009 Ben Wilson
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, struct
from Crypto.Cipher import AES

def beU16(b: bytes) -> int:
    """
    Convert 2-byte big-endian bytes to integer.
    """
    return struct.unpack(">H", b)[0]

def beU32(b: bytes) -> int:
    """
    Convert 4-byte big-endian bytes to integer.
    """
    return struct.unpack(">I", b)[0]

class FstEntry:
    """
    Represents a single entry in the FST.
    """
    def __init__(self):
        self.filename = ""
        self.mode = 0
        self.attr = 0
        self.sub = 0xFFFF
        self.sib = 0xFFFF
        self.size = 0
        self.uid = 0
        self.gid = 0
        self.x3 = 0

class WiiNand:
    """
    Handles reading and extracting Wii NAND content.
    """
    NOECC = 0
    ECC = 1
    OLDBOOTMII = 2

    def __init__(self, nandPath: str, keysPath: str):
        """
        Initialize WiiNand object and prepare for extraction.
        """
        self.nandPath = nandPath
        self.keysPath = keysPath
        self.nandSize = os.path.getsize(nandPath)
        self.nandType = self._guessType()
        self.aesKey = None
        self._loadKey()
        self.aesIv = bytes([0]*16)
        self.nandFile = open(nandPath, "rb")
        self.locSuperblock = self._findSuperblock()
        nFatLen = [0x010000, 0x010800, 0x010800]
        self.locFat = self.locSuperblock
        self.locFst = self.locFat + 0x0C + nFatLen[self.nandType]

    def close(self):
        """
        Close the NAND file safely.
        """
        try:
            self.nandFile.close()
        except Exception:
            pass

    def _guessType(self) -> int:
        """
        Determine NAND type by exact size.
        """
        if self.nandSize == 536870912:
            return self.NOECC
        if self.nandSize == 553648128:
            return self.ECC
        if self.nandSize == 553649152:
            return self.OLDBOOTMII
        raise RuntimeError(f"Unknown NAND size: {self.nandSize}")

    def _loadKey(self):
        """
        Load AES key from keys.bin or NAND (OldBootMii).
        """
        if self.nandType in (self.NOECC, self.ECC):
            with open(self.keysPath, "rb") as f:
                f.seek(0x158)
                self.aesKey = f.read(16)
                if len(self.aesKey) != 16:
                    raise RuntimeError("keys.bin too short or corrupted")
        elif self.nandType == self.OLDBOOTMII:
            with open(self.nandPath, "rb") as f:
                f.seek(0x21000158)
                self.aesKey = f.read(16)
                if len(self.aesKey) != 16:
                    raise RuntimeError("Failed reading key from NAND (OldBootMii)")
        else:
            raise RuntimeError("Unknown NAND type for key")

    def _findSuperblock(self) -> int:
        """
        Locate the superblock in the NAND by scanning.
        """
        if self.nandType == self.NOECC:
            start, end, step = 0x1FC00000, 0x20000000, 0x40000
        else:
            start, end, step = 0x20BE0000, 0x21000000, 0x42000
        self.nandFile.seek(start + 4)
        last, loc = 0, start
        while loc < end:
            self.nandFile.seek(loc)
            raw = self.nandFile.read(4)
            if len(raw) < 4:
                raise RuntimeError("Unexpected EOF while searching superblock")
            current = beU32(raw)
            if current > last:
                last = current
            else:
                return loc - step
            loc += step
        raise RuntimeError("No superblock found")

    def _getCluster(self, clusterIndex: int) -> bytes:
        """
        Read a cluster from NAND and decrypt it with AES.
        """
        clusterLen, pageLen = (0x4000, 0x800) if self.nandType == self.NOECC else (0x4200, 0x840)
        self.nandFile.seek(clusterIndex * clusterLen)
        clusterData = bytearray(0x4000)
        for i in range(8):
            pageData = self.nandFile.read(pageLen)
            if len(pageData) < pageLen:
                raise RuntimeError("Unexpected EOF while reading cluster page")
            clusterData[i * 0x800:(i+1) * 0x800] = pageData[:0x800]
        cipher = AES.new(self.aesKey, AES.MODE_CBC, iv=self.aesIv)
        return cipher.decrypt(bytes(clusterData))

    def _getFat(self, fatIndex: int) -> int:
        """
        Return the next FAT cluster for a given FAT entry.
        """
        fatIndex += 6
        nFatOffset = 0 if self.nandType == self.NOECC else 0x20
        loc = self.locFat + (fatIndex // 0x400 * nFatOffset + fatIndex) * 2
        self.nandFile.seek(loc)
        raw = self.nandFile.read(2)
        if len(raw) < 2:
            raise RuntimeError("Unexpected EOF reading FAT")
        return beU16(raw)

    def _getFst(self, entryIndex: int) -> FstEntry:
        """
        Read a single FST entry.
        """
        fst = FstEntry()
        nFstOffset = 0 if self.nandType == self.NOECC else 2
        locEntry = (entryIndex // 0x40 * nFstOffset + entryIndex) * 0x20
        self.nandFile.seek(self.locFst + locEntry)
        data = self.nandFile.read(0x20)
        if len(data) < 0x20:
            raise RuntimeError("Unexpected EOF reading FST entry")
        fst.filename = data[0:12].rstrip(b'\x00').decode('ascii', errors='ignore')
        fst.mode = data[12] & 1
        fst.attr = data[13]
        fst.sub = beU16(data[14:16])
        fst.sib = beU16(data[16:18])
        fst.size = beU32(data[18:22])
        fst.uid = beU32(data[22:26])
        fst.gid = beU16(data[26:28])
        fst.x3 = beU32(data[28:32])
        return fst

    def extractFst(self, entryIndex: int, parentDir: str, outDir: str, single: bool):
        """
        Extract a file or directory recursively from the FST.
        """
        fstEntry = self._getFst(entryIndex)
        if fstEntry.sib != 0xFFFF and not single:
            self.extractFst(fstEntry.sib, parentDir, outDir, False)
        if fstEntry.mode == 0:
            self._extractDir(fstEntry, parentDir, outDir)
        elif fstEntry.mode == 1:
            self._extractFile(fstEntry, parentDir, outDir)
        else:
            raise RuntimeError(f"Unsupported FST mode {fstEntry.mode}")

    def _extractDir(self, fstEntry: FstEntry, parentDir: str, outDir: str):
        """
        Extract a directory and its sub-entries.
        """
        dirPath = fstEntry.filename
        if parentDir not in ("", "/"):
            dirPath = os.path.join(parentDir, dirPath)
        targetDir = os.path.join(outDir, dirPath) if dirPath != "/" else outDir
        firstComponent = dirPath.strip("/").split(os.sep)[0] if dirPath != "/" else ""
        if firstComponent not in ("title", "ticket", "sys") and dirPath != "/":
            return
        if dirPath != "/":
            os.makedirs(targetDir, exist_ok=True)
        if fstEntry.sub != 0xFFFF:
            self.extractFst(fstEntry.sub, dirPath if dirPath != "/" else "", outDir, False)

    def _extractFile(self, fstEntry: FstEntry, parentDir: str, outDir: str):
        """
        Extract /title, /ticket and /sys/uid.sys from NAND.
        """
        relPath = fstEntry.filename.replace(":", "-")
        if parentDir not in ("", "/"):
            relPath = os.path.join(parentDir, relPath)
        if not (relPath.startswith("title") or relPath.startswith("ticket") or relPath == os.path.join("sys", "uid.sys")):
            return
        filePath = os.path.join(outDir, relPath)
        os.makedirs(os.path.dirname(filePath), exist_ok=True)
        fatIndex = fstEntry.sub
        if fstEntry.size == 0:
            open(filePath, "wb").close()
            return
        clusterSpan = (fstEntry.size // 0x4000) + 1
        dataBuffer = bytearray(clusterSpan * 0x4000)
        i = 0
        while fatIndex < 0xFFF0:
            clusterData = self._getCluster(fatIndex)
            start = i * 0x4000
            end = start + 0x4000
            dataBuffer[start:end] = clusterData[:0x4000]
            fatIndex = self._getFat(fatIndex)
            i += 1
        with open(filePath, "wb") as outFile:
            outFile.write(dataBuffer[:fstEntry.size])

def extractNandData(nandPath: str, keysPath: str, outDir: str):
    """
    Extract the NAND to the given output directory.
    """
    nand = WiiNand(nandPath, keysPath)
    try:
        nand.extractFst(0, "", outDir, True)
    finally:
        nand.close()