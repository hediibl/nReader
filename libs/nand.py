# nReader 2.4
# Copyright (C) 2009 Ben Wilson
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, struct
from Crypto.Cipher import AES

def beU16(data):
    """
    Convert big-endian 2-byte data to integer.

    :param data: bytes, 2 bytes to convert
    :return: int, converted integer
    """
    return struct.unpack(">H", data)[0]

def beU32(data):
    """
    Convert big-endian 4-byte data to integer.

    :param data: bytes, 4 bytes to convert
    :return: int, converted integer
    """
    return struct.unpack(">I", data)[0]

class FstEntry:
    def __init__(self):
        self.fileName = ""
        self.mode = 0
        self.attr = 0
        self.sub = 0xFFFF
        self.sib = 0xFFFF
        self.size = 0
        self.uid = 0
        self.gid = 0
        self.x3 = 0

class WiiNand:
    noEcc = 0
    ecc = 1
    oldBootMii = 2

    def __init__(self, nandPath, keysPath):
        """
        Initialize WiiNand object.

        :param nandPath: str, path to NAND file
        :param keysPath: str|None, path to AES key file
        """
        self.nandPath = nandPath
        self.keysPath = keysPath
        fileSize = os.path.getsize(nandPath)
        if keysPath is None:
            self.nandSize = fileSize
            self.keysOffset = self.nandSize - 1024
        else:
            self.nandSize = fileSize
            self.keysOffset = None
        self.nandType = self._guessType()
        self.aesIv = bytes(16)
        self._loadKey()
        self.nandFile = open(self.nandPath, "rb")
        self.locSuperblock = self._getSuperblockOffset()
        fatLengths = [0x010000, 0x010800, 0x010800]
        self.locFat = self.locSuperblock
        self.locFst = self.locFat + 0x0C + fatLengths[self.nandType]

    def close(self):
        """
        Close the NAND file safely.

        :return: None
        """
        try:
            self.nandFile.close()
        except Exception:
            pass

    def _guessType(self):
        """
        Guess NAND type based on NAND size.

        :return: int, NAND type constant
        """
        if self.nandSize == 536_870_912:
            return self.noEcc
        if self.nandSize == 553_648_128:
            return self.ecc
        if self.nandSize == 553_649_152:
            return self.oldBootMii
        raise RuntimeError(f"Unknown NAND size: {self.nandSize}")

    def _loadKey(self):
        """
        Load AES key from file or NAND.

        :return: None
        """
        if self.keysPath:
            with open(self.keysPath, "rb") as keyFile:
                keyFile.seek(0x158)
                self.aesKey = keyFile.read(16)
        else:
            with open(self.nandPath, "rb") as nandFile:
                nandFile.seek(self.keysOffset + 0x158)
                self.aesKey = nandFile.read(16)
        if len(self.aesKey) != 16:
            raise RuntimeError("AES key not found")

    def _getSuperblockOffset(self):
        """
        Return the NAND superblock offset based on type.

        :return: int, superblock offset
        """
        return 0x1FC00000 if self.nandType == self.noEcc else 0x20BE0000

    def _getCluster(self, index):
        """
        Read and decrypt a NAND cluster.

        :param index: int, cluster index
        :return: bytes, decrypted cluster
        """
        clusterLen, pageLen = (0x4000, 0x800) if self.nandType == self.noEcc else (0x4200, 0x840)
        offset = index * clusterLen
        if offset + clusterLen > self.nandSize:
            raise RuntimeError("Cluster out of NAND bounds")
        self.nandFile.seek(offset)
        buf = bytearray(0x4000)
        for i in range(8):
            page = self.nandFile.read(pageLen)
            buf[i * 0x800:(i + 1) * 0x800] = page[:0x800]
        return AES.new(self.aesKey, AES.MODE_CBC, iv=self.aesIv).decrypt(bytes(buf))

    def _getFat(self, index):
        """
        Return the FAT entry for a cluster.

        :param index: int, FAT index
        :return: int, next cluster index
        """
        index += 6
        eccOffset = 0 if self.nandType == self.noEcc else 0x20
        loc = self.locFat + (index // 0x400 * eccOffset + index) * 2
        self.nandFile.seek(loc)
        return beU16(self.nandFile.read(2))

    def _getFst(self, index):
        """
        Return the FST entry for a file/directory.

        :param index: int, FST index
        :return: FstEntry, entry object
        """
        fst = FstEntry()
        eccOffset = 0 if self.nandType == self.noEcc else 2
        loc = (index // 0x40 * eccOffset + index) * 0x20
        self.nandFile.seek(self.locFst + loc)
        data = self.nandFile.read(0x20)
        fst.fileName = data[0:12].rstrip(b"\0").decode("ascii", "ignore")
        fst.mode = data[12] & 1
        fst.sub = beU16(data[14:16])
        fst.sib = beU16(data[16:18])
        fst.size = beU32(data[18:22])
        return fst

    def extractFst(self, index, parent, outDir, single):
        """
        Recursively extract files and directories from FST.

        :param index: int, FST index
        :param parent: str, parent path
        :param outDir: str, output directory
        :param single: bool, whether to extract a single entry
        :return: None
        """
        entry = self._getFst(index)
        if entry.sib != 0xFFFF and not single:
            self.extractFst(entry.sib, parent, outDir, False)
        if entry.mode == 0:
            self._extractDir(entry, parent, outDir)
        else:
            self._extractFile(entry, parent, outDir)

    def _extractDir(self, entry, parent, outDir):
        """
        Extract a directory and its subentries.

        :param entry: FstEntry, directory entry
        :param parent: str, parent path
        :param outDir: str, output directory
        :return: None
        """
        path = entry.fileName if parent in ("", "/") else os.path.join(parent, entry.fileName)
        root = path.strip("/").split(os.sep)[0]
        if root not in ("title", "ticket", "sys") and path != "/":
            return
        full = outDir if path == "/" else os.path.join(outDir, path)
        os.makedirs(full, exist_ok=True)
        if entry.sub != 0xFFFF:
            self.extractFst(entry.sub, path, outDir, False)

    def _extractFile(self, entry, parent, outDir):
        """
        Extract a single file from NAND.

        :param entry: FstEntry, file entry
        :param parent: str, parent path
        :param outDir: str, output directory
        :return: None
        """
        name = entry.fileName.replace(":", "-")
        path = name if parent in ("", "/") else os.path.join(parent, name)
        if not (path.startswith("title") or path.startswith("ticket") or path == os.path.join("sys", "uid.sys")):
            return
        full = os.path.join(outDir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        buf = bytearray()
        fat = entry.sub
        while fat < 0xFFF0:
            buf.extend(self._getCluster(fat))
            fat = self._getFat(fat)
        with open(full, "wb") as f:
            f.write(buf[:entry.size])

def extractNandData(nandPath, keysPath, outDir):
    """
    Extract NAND contents to output directory.

    :param nandPath: str, path to NAND file
    :param keysPath: str|None, path to AES key file
    :param outDir: str, output directory
    :return: None
    """
    nand = WiiNand(nandPath, keysPath)
    try:
        nand.extractFst(0, "", outDir, True)
    finally:
        nand.close()