# nReader v1.1
# Copyright (C) 2009 Ben Wilson
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os
import struct
from Crypto.Cipher import AES

def beU16(b: bytes) -> int:
    return struct.unpack(">H", b)[0]

def beU32(b: bytes) -> int:
    return struct.unpack(">I", b)[0]

class FstEntry:
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
    NOECC = 0
    ECC = 1
    OLDBOOTMII = 2

    def __init__(self, nandPath: str, keysPath: str):
        self.nandPath = nandPath
        self.keysPath = keysPath
        self.size = os.path.getsize(nandPath)
        self.type = self._guessType()
        self.key = None
        self._loadKey()
        self.iv = bytes([0] * 16)
        self.nandFile = open(nandPath, "rb")

        self.locSuper = self._findSuperblock()
        nFatLen = [0x010000, 0x010800, 0x010800]
        self.locFat = self.locSuper
        self.locFst = self.locFat + 0x0C + nFatLen[self.type]

    def close(self):
        try:
            self.nandFile.close()
        except Exception:
            pass

    def _guessType(self):
        if self.size == 536870912:
            return self.NOECC
        if self.size == 553648128:
            return self.ECC
        if self.size == 553649152:
            return self.OLDBOOTMII
        raise RuntimeError(f"NAND size unknown: {self.size}")

    def _loadKey(self):
        if self.type in (self.NOECC, self.ECC):
            with open(self.keysPath, "rb") as f:
                f.seek(0x158)
                self.key = f.read(16)
                if len(self.key) != 16:
                    raise RuntimeError("keys.bin too short or bad")
        elif self.type == self.OLDBOOTMII:
            with open(self.nandPath, "rb") as f:
                f.seek(0x21000158)
                self.key = f.read(16)
                if len(self.key) != 16:
                    raise RuntimeError("Failed reading key from NAND (OldBootMii)")
        else:
            raise RuntimeError("Unknown NAND type for key")

    def _findSuperblock(self):
        if self.type == self.NOECC:
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

    def _getCluster(self, clusterEntry: int) -> bytes:
        clusterLen, pageLen = (0x4000, 0x800) if self.type == self.NOECC else (0x4200, 0x840)
        self.nandFile.seek(clusterEntry * clusterLen)
        cluster = bytearray(0x4000)
        for i in range(8):
            page = self.nandFile.read(pageLen)
            if len(page) < pageLen:
                raise RuntimeError("Unexpected EOF while reading cluster page")
            cluster[i * 0x800:(i + 1) * 0x800] = page[:0x800]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        return cipher.decrypt(bytes(cluster))

    def _getFat(self, fatEntry: int) -> int:
        fatEntry += 6
        nFat = 0 if self.type == self.NOECC else 0x20
        loc = self.locFat + (fatEntry // 0x400 * nFat + fatEntry) * 2
        self.nandFile.seek(loc)
        raw = self.nandFile.read(2)
        if len(raw) < 2:
            raise RuntimeError("Unexpected EOF reading FAT")
        return beU16(raw)

    def _getFst(self, entry: int) -> FstEntry:
        fst = FstEntry()
        nFst = 0 if self.type == self.NOECC else 2
        locEntry = (entry // 0x40 * nFst + entry) * 0x20
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

    def extractFst(self, entry: int, parent: str, outDir: str, single: bool):
        fst = self._getFst(entry)

        if fst.sib != 0xFFFF and not single:
            self.extractFst(fst.sib, parent, outDir, False)

        if fst.mode == 0:
            self._extractDir(fst, parent, outDir)
        elif fst.mode == 1:
            self._extractFile(fst, parent, outDir)
        else:
            raise RuntimeError(f"Unsupported FST mode {fst.mode}")

    def _extractDir(self, fst: FstEntry, parent: str, outDir: str):
        filename = fst.filename
        if parent not in ("", "/"):
            filename = os.path.join(parent, filename)
        targetDir = os.path.join(outDir, filename) if filename != "/" else outDir

        firstComponent = filename.strip("/").split(os.sep)[0] if filename != "/" else ""
        if firstComponent not in ("title", "ticket", "sys") and filename != "/":
            return

        if filename != "/":
            os.makedirs(targetDir, exist_ok=True)

        if fst.sub != 0xFFFF:
            self.extractFst(fst.sub, filename if filename != "/" else "", outDir, False)

    def _extractFile(self, fst: FstEntry, parent: str, outDir: str):
        relPath = fst.filename.replace(":", "-")
        if parent not in ("", "/"):
            relPath = os.path.join(parent, relPath)

        if not (relPath.startswith("title") or relPath.startswith("ticket") or relPath == os.path.join("sys", "uid.sys")):
            return

        filePath = os.path.join(outDir, relPath)
        os.makedirs(os.path.dirname(filePath), exist_ok=True)

        fat = fst.sub
        if fst.size == 0:
            open(filePath, "wb").close()
            return

        clusterSpan = (fst.size // 0x4000) + 1
        data = bytearray(clusterSpan * 0x4000)

        i = 0
        while fat < 0xFFF0:
            clusterData = self._getCluster(fat)
            start = i * 0x4000
            end = start + 0x4000
            data[start:end] = clusterData[:0x4000]
            fat = self._getFat(fat)
            i += 1

        with open(filePath, "wb") as fw:
            fw.write(data[:fst.size])

def extractNandData(nandPath: str, keysPath: str, outDir="temp"):
    nand = WiiNand(nandPath, keysPath)
    try:
        nand.extractFst(0, "", outDir, True)
    finally:
        nand.close()