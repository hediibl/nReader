/*
MIT License

Copyright (c) 2025 Aep
Copyright (c) 2026 hediibl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// includes
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <malloc.h>
#include <gccore.h>
#include <gctypes.h>
#include <ogc/ipc.h>
#include <ogc/machine/processor.h>
#include <ogc/es.h>
#include "nand.h"

// definitions
#define MEM_PROT 0xd8b420a
#define AHBPROT_DISABLED (*(vu32*)0xcd800064 == 0xFFFFFFFF)

// variables
static const u32 stage0[] = { 0x4903468D, 0x49034788, 0x49036209, 0x47080000, 0x10100000, 0x00000000, 0xFFFF0014 };
static const u32 stage1[] = { 0xE3A01536, 0xE5910064, 0xE380013A, 0xE3800EDF, 0xE5810064, 0xE12FFF1E };
static const u8 isfsPermissionsOld[]   = { 0x9B,0x05,0x40,0x03,0x99,0x05,0x42,0x8B };
static const u8 isfsPermissionsPatch[] = { 0x9B,0x05,0x40,0x03,0x1C,0x0B,0x42,0x8B };
static const int fileMaxSize = 8192;
static int ret;

// helpers
static int getConsoleNickname(char *nickname) {
    if (!nickname)
        return -2;
    memset(nickname, 0, 11);
    CONF_GetNickName((u8 *)nickname);
    return 0;
}

static int getNandSerial(char *serial) {
    if (!serial)
        return -2;
    const char *path = "/title/00000001/00000002/data/setting.txt";
    s32 fd = IOS_Open(path, 1);
    if (fd < 0)
        return -111;
    u8 *buf = (u8*)memalign(32, fileMaxSize);
    if (!buf) {
        IOS_Close(fd);
        return -1;
    }
    s32 bytesRead = IOS_Read(fd, buf, fileMaxSize);
    IOS_Close(fd);
    if (bytesRead <= 0) {
        free(buf);
        return -112;
    }
    {
        u32 key = 0x73B5DBFA;
        for (s32 i = 0; i < bytesRead; i++) {
            buf[i] ^= (u8)(key & 0xFF);
            key = (key << 1) | (key >> 31);
        }
    }
    char code[16]  = {0};
    char serno[16] = {0};
    const char *keys[]  = { "CODE", "SERNO" };
    char *outs[]        = { code, serno };
    u32 outSizes[]      = { sizeof(code), sizeof(serno) };
    for (int k = 0; k < 2; k++) {
        const char *key = keys[k];
        u32 keyLen = strlen(key);
        int found = 0;
        for (u32 i = 0; i + keyLen + 1 < (u32)bytesRead; i++) {
            if (memcmp(buf + i, key, keyLen) == 0 && buf[i + keyLen] == '=') {
                i += keyLen + 1;
                u32 j = 0;
                while (i < (u32)bytesRead && j < outSizes[k] - 1) {
                    char c = buf[i++];
                    if (c < 32 || c > 126) break;
                    outs[k][j++] = c;
                }
                outs[k][j] = '\0';
                found = 1;
                break;
            }
        }
        if (!found) {
            free(buf);
            return -113;
        }
    }
    free(buf);
    snprintf(serial, 13, "%s%s", code, serno);
    return 0;
}

static int checkForTitle(u64 titleId, char outTitle[16]) {
    if (!outTitle)
        return -2;
    u32 tmdSize = 0;
    if (ES_GetStoredTMDSize(titleId, &tmdSize) < 0 || tmdSize == 0) {
        strcpy(outTitle, "No");
        return 0;
    }
    u8 *tmd = (u8*)malloc(tmdSize);
    if (!tmd) {
        strcpy(outTitle, "No");
        return -1;
    }
    if (ES_GetStoredTMD(titleId, (signed_blob*)tmd, tmdSize) < 0) {
        free(tmd);
        strcpy(outTitle, "No");
        return -121;
    }
    u16 version = (tmd[0x1DC] << 8) | tmd[0x1DD];
    free(tmd);
    snprintf(outTitle, 16, "v%u", version);
    return 0;
}

static int checkForTicket(u64 titleId, char outTicket[4]) {
    if (!outTicket)
        return -2;
    u32 ticketCount = 0;
    if (ES_GetNumTicketViews(titleId, &ticketCount) < 0 || ticketCount == 0) {
        strcpy(outTicket, "No");
    } else {
        strcpy(outTicket, "Yes");
    }
    return 0;
}

// public
int nandInit(void) {
    IOS_ReloadIOS(IOS_GetVersion());
    if (!AHBPROT_DISABLED) {
        u32 *const mem1 = (u32 *)0x80000000;
        __attribute__((__aligned__(32)))
        ioctlv vectors[3] = {
            [1] = { .data = (void *)0xFFFE0028, .len = 0 },
            [2] = { .data = mem1, .len = 0x20 }
        };
        memcpy(mem1, stage0, sizeof(stage0));
        mem1[5] = (((u32)stage1) & ~0xC0000000);
        int ret = IOS_Ioctlv(0x10001, 0, 1, 2, vectors);
        if (ret < 0)
            return -101;
        int tries = 1000;
        while (!AHBPROT_DISABLED) {
            usleep(1000);
            if (!tries--)
                return -101;
        }
    }
    write32(MEM_PROT, read32(MEM_PROT) & 0x0000FFFF);
    u8 *ptrStart = (u8*)*((u32*)0x80003134);
    u8 *ptrEnd   = (u8*)0x94000000;
    u32 found = 0;
    while (ptrStart < (ptrEnd - sizeof(isfsPermissionsPatch))) {
        if (!memcmp(ptrStart, isfsPermissionsOld, sizeof(isfsPermissionsOld))) {
            found++;
            u8 *location = ptrStart;
            for (u32 i = 0; i < sizeof(isfsPermissionsPatch); i++)
                location[i] = isfsPermissionsPatch[i];
            u8 *start = location;
            DCFlushRange((u8*)(((u32)start)>>5<<5), (sizeof(isfsPermissionsPatch)>>5<<5)+64);
            ICInvalidateRange((u8*)(((u32)start)>>5<<5), (sizeof(isfsPermissionsPatch)>>5<<5)+64);
        }
        ptrStart++;
    }
    if (found == 0)
        return -102;
    return 0;
}

int nandRead(nandReport *dump) {
    if (!dump)
        return -2;
    dump->entries=NULL;
    dump->count=0;
    ret = getConsoleNickname(dump->username);
    if (ret < 0)
        return ret;
    ret = getNandSerial(dump->serial);
    if (ret < 0)
        return ret;
    s32 fd = IOS_Open("/sys/uid.sys", 1);
    if (fd < 0)
        return -131;
    s32 size = IOS_Seek(fd, 0, SEEK_END);
    if (size <= 0) {
        IOS_Close(fd);
        return -132;
    }
    u8 *buf = malloc(size);
    if (!buf) {
        IOS_Close(fd);
        return -1;
    }
    IOS_Seek(fd, 0, SEEK_SET);
    s32 readBytes = IOS_Read(fd,buf,size);
    IOS_Close(fd);
    if (readBytes!=size) {
        free(buf);
        return -132;
    }
    u32 entryCount = size/12;
    nandEntry *entries = calloc(entryCount,sizeof(nandEntry));
    if (!entries) {
        free(buf);
        return -1;
    }
    u32 validCount = 0;
    for (u32 i = 0; i < entryCount; i++) {
        u64 tid = 0;
        for (int j = 0; j < 8; j++) {
            tid = (tid << 8) | buf[i * 12 + j];
        }
        u32 major = (u32)(tid >> 32);
        u32 minor = (u32)(tid & 0xFFFFFFFF);
        snprintf(entries[validCount].id, sizeof(entries[validCount].id), "%08X-%08X", major, minor);
        ret = checkForTitle(tid, entries[validCount].title);
        if (ret < 0) {
            free(buf);
            free(entries);
            return ret;
        }
        ret = checkForTicket(tid, entries[validCount].ticket);
        if (ret < 0) {
            free(buf);
            free(entries);
            return ret;
        }
        validCount++;
    }
    free(buf);
    if (validCount == 0) {
        dump->entries = calloc(1, sizeof(nandEntry));
        dump->count = 0;
    } else {
        dump->entries = entries;
        dump->count = validCount;
    }
    return 0;
}